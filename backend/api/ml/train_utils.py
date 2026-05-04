"""
模型训练工具模块
提供可复用的DNN/CNN/RF训练函数，供API调用
"""
import os
import time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from typing import Optional, Dict, Callable, List


class DNNModel(nn.Module):
    """标准DNN模型（动态隐藏层）"""
    def __init__(self, input_dim: int = 4, output_dim: int = 1241,
                 hidden_layers: Optional[List[int]] = None):
        super().__init__()
        if hidden_layers is None:
            hidden_layers = [16, 32, 64]
        dims = [input_dim] + hidden_layers + [output_dim]
        layers = []
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:
                layers.append(nn.ReLU())
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)



class CNN1DModel(nn.Module):
    """
    CNN-1D 模型：将输入视为 (batch, 1, input_dim) 的一维信号进行卷积特征提取。
    conv_layers: list of dict {filters, kernel_size, pooling}
    fc_units: 全连接头的隐藏维度
    """
    def __init__(self, input_dim: int = 4, output_dim: int = 1241,
                 conv_layers: Optional[List[Dict]] = None, fc_units: int = 256):
        super().__init__()
        if conv_layers is None:
            conv_layers = [
                {'filters': 32, 'kernel_size': 3, 'pooling': False},
                {'filters': 64, 'kernel_size': 3, 'pooling': False},
            ]

        conv_blocks = []
        in_ch = 1
        seq_len = input_dim
        for cfg in conv_layers:
            ks = min(cfg.get('kernel_size', 3), seq_len)  # kernel不超过序列长度
            ks = max(ks, 1)
            padding = ks // 2
            conv_blocks.append(nn.Conv1d(in_ch, cfg['filters'], ks, padding=padding))
            conv_blocks.append(nn.ReLU())
            if cfg.get('pooling', False) and seq_len > 1:
                conv_blocks.append(nn.MaxPool1d(2))
                seq_len = seq_len // 2
            in_ch = cfg['filters']

        self.conv = nn.Sequential(*conv_blocks)
        # 用 dummy forward 推导真实 flat_dim，避免偶数 kernel_size 导致维度偏差
        with torch.no_grad():
            dummy = torch.zeros(1, 1, input_dim)
            flat_dim = int(nn.Flatten()(self.conv(dummy)).shape[1])
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(flat_dim, fc_units),
            nn.ReLU(),
            nn.Linear(fc_units, output_dim),
        )

    def forward(self, x):
        # x: (batch, input_dim) → (batch, 1, input_dim)
        x = x.unsqueeze(1)
        x = self.conv(x)
        return self.head(x)


# ───────────────────────────────────────────────────────────────
#  通用 DL 训练函数（DNN / PINN / CNN）
# ───────────────────────────────────────────────────────────────
def train_dnn_model(
    data_dir: str,
    model_save_dir: str,
    model_type: str = "DNN",
    epochs: int = 3000,
    batch_size: int = 16,
    lr: float = 1e-4,
    device: Optional[torch.device] = None,
    progress_callback: Optional[Callable[[int, float, float], None]] = None,
    # 额外架构配置（来自前端 model_config）
    hidden_layers: Optional[List[int]] = None,
    conv_layers: Optional[List[Dict]] = None,
    fc_units: int = 256,
) -> Dict:
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 加载数据：优先使用 zscore 归一化输入 + PCA 降维输出
    # 回退：若 zscore/PCA 文件不存在则使用原始 split 文件
    def _try(a, b):
        return a if os.path.exists(os.path.join(data_dir, a)) else b

    trainX_file = _try('zstrainInput.txt', 'trainInput.txt')
    testX_file  = _try('zstestInput.txt',  'testInput.txt')
    trainY_file = _try('trainPCA.txt',     'trainOutput.txt')
    testY_file  = _try('testPCA.txt',      'testOutput.txt')

    trainX_path = os.path.join(data_dir, trainX_file)
    trainY_path = os.path.join(data_dir, trainY_file)
    testX_path  = os.path.join(data_dir, testX_file)
    testY_path  = os.path.join(data_dir, testY_file)

    if not all(os.path.exists(p) for p in [trainX_path, trainY_path, testX_path, testY_path]):
        raise FileNotFoundError(
            f"训练数据文件不完整（尝试: {trainX_file}, {trainY_file}），请确保已完成完整预处理流水线"
        )

    trX  = torch.Tensor(np.loadtxt(trainX_path))
    trY  = torch.Tensor(np.loadtxt(trainY_path))
    testX = torch.Tensor(np.loadtxt(testX_path))
    testY = torch.Tensor(np.loadtxt(testY_path))

    if trX.ndim == 1: trX = trX.unsqueeze(1)
    if trY.ndim == 1: trY = trY.unsqueeze(1)
    if testX.ndim == 1: testX = testX.unsqueeze(1)
    if testY.ndim == 1: testY = testY.unsqueeze(1)

    input_dim  = trX.shape[1]
    output_dim = trY.shape[1]

    train_loader = DataLoader(TensorDataset(trX, trY), batch_size=batch_size, shuffle=True,  num_workers=0)
    test_loader  = DataLoader(TensorDataset(testX, testY), batch_size=batch_size, shuffle=False, num_workers=0)

    # 构建模型
    mtype = model_type.upper()
    if mtype == "CNN":
        net = CNN1DModel(input_dim, output_dim, conv_layers=conv_layers, fc_units=fc_units).to(device)
    else:  # DNN (default)
        net = DNNModel(input_dim, output_dim, hidden_layers=hidden_layers).to(device)

    loss_fn = nn.L1Loss()
    # 分阶段学习率优化器
    opts = [
        torch.optim.Adam(net.parameters(), lr=lr),
        torch.optim.Adam(net.parameters(), lr=0.1 * lr),
        torch.optim.Adam(net.parameters(), lr=0.01 * lr),
        torch.optim.Adam(net.parameters(), lr=0.001 * lr),
    ]

    train_losses = []
    test_losses  = []

    for epoch in range(epochs):
        net.train()
        ep_loss = 0.0
        stage = 0 if epoch < 0.2 * epochs else (1 if epoch < 0.5 * epochs else (2 if epoch < 0.7 * epochs else 3))
        opt = opts[stage]

        for bX, bY in train_loader:
            bX, bY = bX.to(device), bY.to(device)
            pred = net(bX)
            loss = loss_fn(pred, bY)
            opt.zero_grad(); loss.backward(); opt.step()
            ep_loss += loss.item()

        net.eval()
        t_loss = 0.0
        with torch.no_grad():
            for tX, tY in test_loader:
                t_loss += loss_fn(net(tX.to(device)), tY.to(device)).item()

        avg_tr = ep_loss / len(train_loader)
        avg_te = t_loss  / len(test_loader)
        train_losses.append(avg_tr)
        test_losses.append(avg_te)

        if progress_callback and (epoch + 1) % 10 == 0:
            progress_callback(epoch + 1, avg_tr, avg_te)

    # 保存模型
    os.makedirs(model_save_dir, exist_ok=True)
    ts = time.strftime("%Y-%m-%d-%H-%M-%S")
    fname = f"{mtype}_{ts}.pth"
    torch.save(net.state_dict(), os.path.join(model_save_dir, fname))

    net.eval()
    with torch.no_grad():
        pred_pca    = net(testX.to(device)).cpu().numpy()
        pred_tr_pca = net(trX.to(device)).cpu().numpy()
        true_pca    = testY.numpy()
        final_test_loss_pca  = float(np.mean(np.abs(pred_pca    - true_pca)))
        final_train_loss_pca = float(np.mean(np.abs(pred_tr_pca - trY.numpy())))

    # 反变换到原始空间，得到物理意义的 MAE
    final_test_loss  = final_test_loss_pca
    final_train_loss = final_train_loss_pca
    inverse_transform_ok = False
    if os.path.exists(os.path.join(data_dir, 'trainPCA.txt')):
        pca_dir   = os.path.join(os.path.dirname(data_dir), 'pca_result')
        mean_path = os.path.join(pca_dir, 'mean_pca.txt')
        vec_path  = os.path.join(pca_dir, 'vector_pca.txt')
        raw_te = os.path.join(data_dir, 'testOutput.txt')
        raw_tr = os.path.join(data_dir, 'trainOutput.txt')
        if not os.path.exists(mean_path):
            import warnings; warnings.warn(f"[train_utils] 反变换失败: mean_pca.txt 不存在于 {pca_dir}")
        elif not os.path.exists(vec_path):
            import warnings; warnings.warn(f"[train_utils] 反变换失败: vector_pca.txt 不存在于 {pca_dir}")
        elif not os.path.exists(raw_te):
            import warnings; warnings.warn(f"[train_utils] 反变换失败: testOutput.txt 不存在于 {data_dir}")
        elif not os.path.exists(raw_tr):
            import warnings; warnings.warn(f"[train_utils] 反变换失败: trainOutput.txt 不存在于 {data_dir}")
        else:
            try:
                pca_mean = np.loadtxt(mean_path)   # (raw_dim,)
                pca_vec  = np.loadtxt(vec_path)    # (n_comp, raw_dim)
                pred_orig    = pred_pca    @ pca_vec + pca_mean
                pred_tr_orig = pred_tr_pca @ pca_vec + pca_mean
                final_test_loss  = float(np.mean(np.abs(pred_orig    - np.loadtxt(raw_te))))
                final_train_loss = float(np.mean(np.abs(pred_tr_orig - np.loadtxt(raw_tr))))
                inverse_transform_ok = True
            except Exception as _e:
                import warnings; warnings.warn(f"[train_utils] 反变换异常: {_e}")

    return {
        "model_path": os.path.join(model_save_dir, fname),
        "model_filename": fname,
        "final_train_loss": final_train_loss,           # 原始空间 MAE（T）若反变换成功，否则PCA空间
        "final_test_loss":  final_test_loss,
        "final_train_loss_pca": final_train_loss_pca,   # PCA 空间 MAE（用于曲线趋势）
        "final_test_loss_pca":  final_test_loss_pca,
        "inverse_transform_ok": inverse_transform_ok,   # True=已反变换到原始空间
        "epochs": epochs,
        "input_dim": int(input_dim),
        "output_dim": int(output_dim),
        "batch_size": batch_size,
        "learning_rate": lr,
        "device": str(device),
    }


# ───────────────────────────────────────────────────────────────
#  随机森林训练函数
# ───────────────────────────────────────────────────────────────
def train_rf_model(
    data_dir: str,
    model_save_dir: str,
    n_estimators: int = 100,
    max_depth: Optional[int] = 20,
    min_samples_split: int = 2,
    min_samples_leaf: int = 1,
    max_features: str = "sqrt",
    bootstrap: bool = True,
    oob_score: bool = False,
    progress_callback: Optional[Callable[[int, float, float], None]] = None,
) -> Dict:
    try:
        from sklearn.ensemble import RandomForestRegressor
        import joblib
    except ImportError:
        raise ImportError("scikit-learn / joblib 未安装，请 pip install scikit-learn joblib")

    def _try(a, b):
        return a if os.path.exists(os.path.join(data_dir, a)) else b

    trainX = np.loadtxt(os.path.join(data_dir, _try('zstrainInput.txt', 'trainInput.txt')))
    trainY = np.loadtxt(os.path.join(data_dir, _try('trainPCA.txt',     'trainOutput.txt')))
    testX  = np.loadtxt(os.path.join(data_dir, _try('zstestInput.txt',  'testInput.txt')))
    testY  = np.loadtxt(os.path.join(data_dir, _try('testPCA.txt',      'testOutput.txt')))

    if trainX.ndim == 1: trainX = trainX.reshape(-1, 1)
    if trainY.ndim == 1: trainY = trainY.reshape(-1, 1)
    if testX.ndim  == 1: testX  = testX.reshape(-1, 1)
    if testY.ndim  == 1: testY  = testY.reshape(-1, 1)

    input_dim  = trainX.shape[1]
    output_dim = trainY.shape[1]

    max_depth_val = None if max_depth == 0 else max_depth
    # 解析 max_features
    mf = max_features
    if mf == "1.0":
        mf = 1.0

    # 用 warm_start 逐步增加树，每步上报真实 MAE，形成收敛曲线
    step = max(1, n_estimators // 20)   # 最多上报 20 个点
    rf = RandomForestRegressor(
        n_estimators=step,
        max_depth=max_depth_val,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        max_features=mf,
        bootstrap=bootstrap,
        oob_score=False,
        n_jobs=-1,
        random_state=42,
        warm_start=True,
    )

    n_built = 0
    while n_built < n_estimators:
        n_built = min(n_built + step, n_estimators)
        rf.n_estimators = n_built
        rf.fit(trainX, trainY)
        if progress_callback:
            tr_mae = float(np.mean(np.abs(rf.predict(trainX) - trainY)))
            te_mae = float(np.mean(np.abs(rf.predict(testX)  - testY)))
            progress_callback(n_built, tr_mae, te_mae)

    # 评估（PCA 空间）
    pred_train = rf.predict(trainX)
    pred_test  = rf.predict(testX)
    train_mae_pca = float(np.mean(np.abs(pred_train - trainY)))
    test_mae_pca  = float(np.mean(np.abs(pred_test  - testY)))

    # 反变换到原始空间
    train_mae = train_mae_pca
    test_mae  = test_mae_pca
    if os.path.exists(os.path.join(data_dir, 'trainPCA.txt')):
        pca_dir   = os.path.join(os.path.dirname(data_dir), 'pca_result')
        mean_path = os.path.join(pca_dir, 'mean_pca.txt')
        vec_path  = os.path.join(pca_dir, 'vector_pca.txt')
        if os.path.exists(mean_path) and os.path.exists(vec_path):
            try:
                pca_mean = np.loadtxt(mean_path)
                pca_vec  = np.loadtxt(vec_path)
                pred_orig    = pred_test  @ pca_vec + pca_mean
                pred_tr_orig = pred_train @ pca_vec + pca_mean
                raw_te = os.path.join(data_dir, 'testOutput.txt')
                raw_tr = os.path.join(data_dir, 'trainOutput.txt')
                if os.path.exists(raw_te) and os.path.exists(raw_tr):
                    test_mae  = float(np.mean(np.abs(pred_orig    - np.loadtxt(raw_te))))
                    train_mae = float(np.mean(np.abs(pred_tr_orig - np.loadtxt(raw_tr))))
            except Exception:
                pass

    # 保存
    os.makedirs(model_save_dir, exist_ok=True)
    ts = time.strftime("%Y-%m-%d-%H-%M-%S")
    fname = f"RF_{ts}.pkl"
    import joblib
    joblib.dump(rf, os.path.join(model_save_dir, fname))

    return {
        "model_path": os.path.join(model_save_dir, fname),
        "model_filename": fname,
        "final_train_loss": train_mae,
        "final_test_loss":  test_mae,
        "final_train_loss_pca": train_mae_pca,
        "final_test_loss_pca":  test_mae_pca,
        "epochs": n_estimators,
        "input_dim": int(input_dim),
        "output_dim": int(output_dim),
        "device": "CPU",
    }


def get_model_info(model_path: str, model_type: str = "DNN") -> Dict:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}")
    file_size = os.path.getsize(model_path)
    file_time = os.path.getmtime(model_path)
    return {
        "path": model_path,
        "filename": os.path.basename(model_path),
        "type": model_type,
        "size_mb": round(file_size / (1024 * 1024), 2),
        "modified_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(file_time)),
    }

