import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
from torch.utils.data import DataLoader, TensorDataset
import time
import matplotlib.pyplot as plt
import pylab as pl
from scipy.spatial import Delaunay
from torch.autograd import grad

# 文件路径
trainY_path = '../data/trainOutput.txt'
testX_path = '../data/testInput.txt'
testY_path = '../data/testOutput.txt'
trainX_path = '../data/trainInput.txt'
coord_path = '../data/zuobiao.txt'  # 坐标文件路径
logs = "../log"
predY_save_path = '../result/DNN'

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 加载坐标数据
coords = np.loadtxt(coord_path)
print(f"Loaded coordinates: {coords.shape}")


# 创建邻接矩阵（用于平滑约束）
def create_adjacency_matrix(points):
    tri = Delaunay(points)
    num_points = points.shape[0]
    adjacency = np.zeros((num_points, num_points), dtype=np.float32)

    for simplex in tri.simplices:
        for i in range(3):
            for j in range(i + 1, 3):
                idx1, idx2 = simplex[i], simplex[j]
                adjacency[idx1, idx2] = 1.0
                adjacency[idx2, idx1] = 1.0

    # 归一化
    row_sums = adjacency.sum(axis=1)
    adjacency = adjacency / np.maximum(row_sums[:, np.newaxis], 1e-6)  # 避免除以零

    return adjacency


# 创建拉普拉斯矩阵（用于平滑约束）
def create_laplacian_matrix(points):
    adjacency = create_adjacency_matrix(points)
    num_points = points.shape[0]

    # 度矩阵
    degree = np.diag(adjacency.sum(axis=1))

    # 拉普拉斯矩阵
    laplacian = degree - adjacency
    return laplacian


# 创建边界掩码（用于边界约束）
# 创建边界掩码（用于边界约束）
def create_boundary_mask(points, threshold=0.5):
    """
    创建对称边界掩码（z=35和z=-35平面）
    """
    z1 = 35.0
    z2 = -35.0
    mask1 = np.abs(points[:, 2] - z1) < threshold
    mask2 = np.abs(points[:, 2] - z2) < threshold
    return mask1 | mask2

# 预计算矩阵
adjacency_matrix = create_adjacency_matrix(coords)
laplacian_matrix = create_laplacian_matrix(coords)
#boundary_mask = create_boundary_mask(coords)
boundary_mask = create_boundary_mask(coords, threshold=0.5)  # 可以根据需要调整阈值
# 转换为PyTorch张量
adjacency_tensor = torch.tensor(adjacency_matrix, dtype=torch.float32).to(device)
laplacian_tensor = torch.tensor(laplacian_matrix, dtype=torch.float32).to(device)
boundary_tensor = torch.tensor(boundary_mask, dtype=torch.bool).to(device)
coords_tensor = torch.tensor(coords, dtype=torch.float32).to(device).requires_grad_(True)

# 物理约束权重
LAMBDA_DIV = 0.1  # 散度约束权重
LAMBDA_LAP = 0.05  # 平滑约束权重
LAMBDA_BC = 0.2  # 边界条件权重


def get_parameter_number(net):
    total_num = sum(p.numel() for p in net.parameters())
    trainable_num = sum(p.numel() for p in net.parameters() if p.requires_grad)
    return {'Total': total_num, 'Trainable': trainable_num}


class NetShortCircuit(nn.Module):
    def __init__(self):
        super(NetShortCircuit, self).__init__()
        self.fc1 = nn.Linear(4, 32)
        self.fc2 = nn.Linear(32, 64)
        self.fc3 = nn.Linear(64, 128)
        self.fc4 = nn.Linear(128, 256)
        self.fc5 = nn.Linear(256, 1241)

        # 添加批归一化层以改善稳定性
        self.bn1 = nn.BatchNorm1d(32)
        self.bn2 = nn.BatchNorm1d(64)
        self.bn3 = nn.BatchNorm1d(128)
        self.bn4 = nn.BatchNorm1d(256)

    def forward(self, x):
        x = torch.relu(self.bn1(self.fc1(x)))
        x = torch.relu(self.bn2(self.fc2(x)))
        x = torch.relu(self.bn3(self.fc3(x)))
        x = torch.relu(self.bn4(self.fc4(x)))
        return self.fc5(x)


# 训练参数
lr = 1e-4
BATCH_SIZE = 16
epochs = 3000
net = NetShortCircuit().to(device)
print(f"Model parameters: {get_parameter_number(net)}")

# 加载数据
trX = np.loadtxt(trainX_path)
trY = np.loadtxt(trainY_path)
print(f"Training data shapes: X={trX.shape}, Y={trY.shape}")

trX = torch.Tensor(trX)
trY = torch.Tensor(trY)
train_datasets = TensorDataset(trX, trY)
train_loader = DataLoader(
    dataset=train_datasets,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
)

testX = np.loadtxt(testX_path)
testY = np.loadtxt(testY_path)
testX = torch.Tensor(testX)
testY = torch.Tensor(testY)
test_datasets = TensorDataset(testX, testY)
test_loader = DataLoader(
    dataset=test_datasets,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0,
)

# 损失函数和优化器
loss_fn = torch.nn.L1Loss()
optimizer = torch.optim.Adam(net.parameters(), lr=lr)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=50, verbose=True
)

# 训练记录
epoches = []
losses = []
testlosses = []
phys_losses = []
writer = SummaryWriter(logs)
current_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


# 修正的物理约束计算函数
def compute_physics_loss(output):
    """
    计算物理约束损失，包括散度约束、平滑约束和边界条件约束
    修复了梯度计算中的问题
    """
    # 散度约束 (∇·B≈0)
    loss_div = 0.0

    # 创建可微坐标变量
    coords_var = coords_tensor.clone().requires_grad_(True)

    # 计算散度损失
    for i in range(output.shape[0]):  # 遍历batch中的每个样本
        # 获取当前样本的预测场
        field = output[i]

        # 计算一阶梯度
        gradients = grad(
            outputs=field,
            inputs=coords_var,
            grad_outputs=torch.ones_like(field),
            create_graph=True,
            retain_graph=True,
            allow_unused=True  # 关键修复：允许未使用的变量
        )[0]

        if gradients is None:
            continue

        # 计算散度 (∇·B = ∂Bx/∂x + ∂By/∂y + ∂Bz/∂z)
        div = 0.0
        for j in range(3):  # x,y,z三个方向
            grad_comp = gradients[:, j]

            # 计算二阶导数
            div_comp = grad(
                outputs=grad_comp,
                inputs=coords_var,
                grad_outputs=torch.ones_like(grad_comp),
                create_graph=True,
                retain_graph=True,
                allow_unused=True  # 关键修复
            )[0]

            if div_comp is None:
                continue

            div += div_comp[:, j]  # 只取对角线元素

        # 累加散度损失
        if div is not 0:
            loss_div += torch.mean(div ** 2)

    # 平均散度损失
    loss_div = loss_div / output.shape[0] if loss_div != 0 else torch.tensor(0.0, device=device)

    # 平滑约束 (拉普拉斯项)
    # 使用预计算的拉普拉斯矩阵: L * B
    smoothed = torch.mm(laplacian_tensor, output.t()).t()
    loss_lap = torch.mean(smoothed ** 2)

    # 边界条件约束
    # 假设边界上磁场应该接近0
    boundary_output = output[:, boundary_tensor]
    loss_bc = torch.mean(boundary_output ** 2)

    # 总物理损失
    physics_loss = (
            LAMBDA_DIV * loss_div +
            LAMBDA_LAP * loss_lap +
            LAMBDA_BC * loss_bc
    )

    return physics_loss, loss_div, loss_lap, loss_bc


# 训练循环
for epoch in range(epochs):
    net.train()
    total_loss = 0.0
    total_phys_loss = 0.0

    for step, (batchX, batchY) in enumerate(train_loader):
        batchX = batchX.to(device)
        batchY = batchY.to(device)

        # 前向传播
        y_pred = net(batchX)

        # 数据损失
        loss_data = loss_fn(y_pred, batchY)

        # 物理约束损失
        physics_loss, loss_div, loss_lap, loss_bc = compute_physics_loss(y_pred)

        # 总损失
        loss = loss_data + physics_loss

        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        total_phys_loss += physics_loss.item() if not torch.isnan(physics_loss) else 0.0

    # 计算平均损失
    avg_loss = total_loss / len(train_loader)
    avg_phys_loss = total_phys_loss / len(train_loader)

    # 测试集评估
    net.eval()
    with torch.no_grad():
        test_loss = 0.0
        for testdata in test_loader:
            testin, testout = testdata
            testin = testin.to(device)
            testout = testout.to(device)
            predY = net(testin)
            test_loss += loss_fn(predY, testout).item()

        test_loss /= len(test_loader)

    # 记录损失
    epoches.append(epoch + 1)
    losses.append(avg_loss)
    testlosses.append(test_loss)
    phys_losses.append(avg_phys_loss)

    # 学习率调整
    scheduler.step(test_loss)

    # 日志记录
    if (epoch + 1) % 30 == 0:
        print(f"Epoch {epoch + 1}/{epochs}")
        print(f"  Train Loss: {avg_loss:.6f} (Data: {avg_loss - avg_phys_loss:.6f}, Physics: {avg_phys_loss:.6f})")
        print(f"  Test Loss: {test_loss:.6f}")
        print(f"  Learning Rate: {optimizer.param_groups[0]['lr']:.2e}")

# 保存模型和预测结果
model_savePath = f'../model/DNN_PINN_{current_time}.pth'
torch.save(net.state_dict(), model_savePath)

with torch.no_grad():
    testX = testX.to(device)
    testY = testY.to(device)
    predY = net(testX)
    loss = loss_fn(predY, testY)

# 保存预测结果
detail = (f"time: {current_time}\nModel: {net}\n"
          f"lr: {lr}\noptimizer: {optimizer}\nBATCH_SIZE: {BATCH_SIZE}\n"
          f"epochs: {epochs}\ntest_Loss: {loss.item():.6f}\n"
          f"Physics weights: Div={LAMBDA_DIV}, Lap={LAMBDA_LAP}, BC={LAMBDA_BC}")

predY = predY.cpu().numpy()
np.savetxt(os.path.join(predY_save_path, f"predY_PINN_{current_time}.txt"),
           predY, delimiter=',', header=detail)

# 绘制损失曲线
plt.figure(figsize=(12, 8))
plt.plot(epoches, losses, 'g-', label='Total Train Loss')
plt.plot(epoches, testlosses, 'r-', label='Test Loss')
plt.plot(epoches, phys_losses, 'b--', label='Physics Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training and Physics Loss')
plt.yscale('log')
plt.legend()
plt.grid(True)

# 保存损失曲线
loss_plot_path = os.path.join(predY_save_path, f"loss_plot_PINN_{current_time}.png")
plt.savefig(loss_plot_path)
plt.close()

print(f"Training completed. Model saved to {model_savePath}")
print(f"Loss plot saved to {loss_plot_path}")