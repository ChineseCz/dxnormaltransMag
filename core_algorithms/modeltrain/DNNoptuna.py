# 使用optuna调参
import os

import optuna
from optuna.trial import TrialState
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader   # 将data读取存储在loader中
import random
import numpy as np
from torch.utils.tensorboard import SummaryWriter
import math
import datetime
import time
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

matplotlib.rc("font", family="Microsoft YaHei")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCHSIZE = 16
EPOCHES = 10000
INNUMS = 4   # 输入维度
OUTNUMS = 60  # 输出维度

alpha1 = 1 / 4   # 限定epoch
alpha2 = 1 / 2
alpha3 = 3 / 4


def define_model(trial):
    n_layers = trial.suggest_int("n_layers", 3, 6)
    layers = []
    in_features = 4
    for i in range(n_layers):
        # out_features = trial.suggest_int("n_units_l{}".format(i), 16, 1024)
        out_features = trial.suggest_categorical("n_units_l{}".format(i), [8, 32, 64, 128, 256, 512])
        layers.append(nn.Linear(in_features, out_features))
        layers.append(nn.ReLU())
        in_features = out_features

    layers.append(nn.Linear(in_features, OUTNUMS))
    # print(layers)
    return nn.Sequential(*layers)


def objective(trial):
    # model = define_model(trial).to(DEVICE)
    model = define_model(trial).to(DEVICE)
    optimizer_name = trial.suggest_categorical("optimizer", ["Adam"])
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    lr1 = trial.suggest_float("lr1", 1e-6, lr, log=True)
    lr2 = trial.suggest_float("lr2", 1e-7, lr1, log=True)
    lr3 = trial.suggest_float("lr3", 1e-8, lr2, log=True)
    # optimizer = getattr(optim, optimizer_name)(model.parameters(), lr=lr)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    optimizer1 = torch.optim.Adam(model.parameters(), lr=lr1)
    optimizer2 = torch.optim.Adam(model.parameters(), lr=lr2)
    optimizer3 = torch.optim.Adam(model.parameters(), lr=lr3)

    # loss_fn = torch.nn.MSELoss()
    loss_fn = torch.nn.L1Loss()   # 正常数据使用L1loss

    trX = np.loadtxt(trainXPath)
    trY = np.loadtxt(trainYPath)
    tr = zip(trX, trY)
    tr = list(tr)
    random.shuffle(tr)
    trX, trY = zip(*tr)
    trX = torch.Tensor(trX)
    trY = torch.Tensor(trY)
    trX = trX.to(DEVICE)
    trY = trY.to(DEVICE)
    torch_datasets = TensorDataset(trX, trY)
    loader = DataLoader(
        # 从数据库中每次抽出batch size个样本
        dataset=torch_datasets,
        batch_size=BATCHSIZE,
        shuffle=True,
        num_workers=0,
    )

    testX = np.loadtxt(testXPath)
    testY = np.loadtxt(testYPath)
    testX = torch.Tensor(testX)
    testY = torch.Tensor(testY)
    testX = testX.to(DEVICE)
    testY = testY.to(DEVICE)
    # writer = SummaryWriter(logs)

    for epoch in range(EPOCHES):
        for step, (batchX, batchY) in enumerate(loader):
            if torch.cuda.is_available():
                batchX = batchX.cuda()
                batchY = batchY.cuda()
            # print(batchX.shape)    # torch.Size([8, 1])
            y_pred = model(batchX)
            loss = loss_fn(y_pred, batchY)
        if (epoch + 1) % 10 == 0:
            print("Epoch", epoch + 1, loss.item())
            if epoch < alpha1 * EPOCHES:
                optimizer.zero_grad()
                loss.backward()  # backpass
                optimizer.step()  # gradient descent
            elif epoch < alpha2 * EPOCHES:
                optimizer1.zero_grad()
                loss.backward()  # backpass
                optimizer1.step()  # gradient descent
            elif epoch < alpha3 * EPOCHES:
                optimizer2.zero_grad()
                loss.backward()  # backpass
                optimizer2.step()  # gradient descent
            else:
                optimizer3.zero_grad()
                loss.backward()  # backpass
                optimizer3.step()  # gradient descent

        if torch.cuda.is_available():
            testX = testX.cuda()
        with torch.no_grad():
            predY = model(testX)
        loss = loss_fn(predY, testY)

        # 对无望的trail进行剪枝
        trial.report(loss, epoch)
        if trial.should_prune():
            raise optuna.exceptions.TrialPruned()
    # writer.close()

    if torch.cuda.is_available():
        testX = testX.cuda()
    with torch.no_grad():
        predY = model(testX)

    # 保存模型权重文件
    # torch.save(model, os.path.join(projectPath, "ModelPart{}".format(i), "F01_Model",
    #                              "Part{0}_DNN{1}.ptl".format(i, timeStr)))

    loss = loss_fn(predY, testY)
    # mape = mape_fn_tensor(testY, predY)
    predY = predY.data.cpu().numpy()

    header = "loss\t" + str(float(loss)) + "\n"
    for key, value in trial.params.items():
        header = header + "{}\t{}".format(key, value) + "\n"

    np.savetxt(projectPath + '/optuna_result/trail{}.txt'.format(trial.number), predY, header=header)

    return loss


def reNormalization(preData, i):
    """
    对预测的数据进行归一化反变换
    :param preData:
    :return:
    """
    normalDataMaxMin = np.loadtxt(
        projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F01_Train\F02_Output{}\F06_dataNormalizationMinMax.txt".format(
            i))
    minData, maxData = normalDataMaxMin[0], normalDataMaxMin[1]
    t = time.time()
    return preData * (maxData - minData) + minData, t


def reconstructPCA(data, i):
    """
    PCA反变换，将预测值利用训练时保存的components和mean反变换
    :param data: 预测数据
    :return: 反变换后的数据
    """
    components = np.loadtxt(
        projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F01_Train\F02_Output{}\F03_components.txt".format(i))
    mean = np.loadtxt(
        projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F01_Train\F02_Output{}\F02_mean.txt".format(i))
    t = time.time()
    return np.matmul(data, components) + mean, t


def mape_fn(yTrue, yPred):
    """
    计算MPAPE
    :param yTrue: 真实值
    :param yPred: 预测值
    :return:
    """
    # return np.mean(np.abs((yPred - yTrue) / (yTrue + 1e-5))) * 100
    return np.mean(np.abs((yPred - yTrue) / (yTrue + 1e-5))) * 100


def mae_fn(yTrue, yPred):
    """
    计算MAE
    :param yTrue:
    :param yPred:
    :return:
    """
    return np.mean(np.abs(yPred - yTrue))


def nmae_fn(yTrue, yPred):
    return (mae_fn(yTrue, yPred) / np.max(yTrue)) * 100


def ae_fn(yTrue, yPred):
    return np.abs(np.max(yTrue) - np.max(yPred))


def nae_fn(yTrue, yPred):
    return (ae_fn(yTrue, yPred) / np.max(yTrue)) * 100


def rmse_fn(yTrue, yPred):
    return np.sqrt(np.mean(np.square(yTrue - yPred)))


def nrmse_fn(yTrue, yPred):
    return (rmse_fn(yTrue, yPred) / np.max(yTrue)) * 100


def showDataRow(x, y, title):
    plt.scatter(x, y, s=2)
    plt.title(title)
    # plt.show()


def drawPic3DxyzT(x, y, z, T, title):
    fig = plt.figure(figsize=(12, 8))
    ax = Axes3D(fig)
    sc = ax.scatter(x, y, z, c=T, s=1, cmap=plt.cm.get_cmap('jet'))
    ax.set_xlabel("x/mm")
    ax.set_ylabel("y/mm")
    ax.set_zlabel("z/mm")
    ax.set_title(title, loc="center", y=1.0)
    axins = inset_axes(ax,
                       width="5%",
                       height="80%",
                       loc="center left",
                       bbox_to_anchor=(1.05, 0., 1, 1),
                       bbox_transform=ax.transAxes,
                       borderpad=0,
                       )
    colorband = np.max(T) - np.min(T)
    cbar = plt.colorbar(sc,
                        cax=axins,
                        ticks=[np.min(T), np.min(T) + 0.25 * colorband, np.min(T) + 0.5 * colorband,
                               np.min(T) + 0.75 * colorband, np.max(T)],
                        label="B/T")
    # plt.title(title, loc="left")
    # plt.show()


# 展示预测数据
def showPredY(predYData, i, picSavePath):
    reNormalData = reNormalization(predYData, i)[0]
    rePCAData = reconstructPCA(reNormalData, i)[0]
    realYData = np.loadtxt(
        projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F02_Test\F02_Output{}\F01_outputRow.txt".format(i))
    # print(projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F02_Test\F02_Output{}\F01_outputRow.txt".format(i))
    # print(realYData.shape)
    # print(realYData.shape, reNormalData.shape)
    # print(realYData.shape, rePCAData.shape)
    realYLabels = np.loadtxt(
        projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F02_Test\F01_Input{}\F01_inputRow.txt".format(i))
    coordinates = np.loadtxt(projectPath + r"\F02_RowData\漏磁导出数据\R=5400\5400_0.001.txt", comments="%", encoding="utf-8")
    x, y, z = coordinates[:, 0], coordinates[:, 1], coordinates[:, 2]
    # print(realYData.shape, rePCAData.shape)
    MAPE = mape_fn(realYData, rePCAData)
    print("total mean MAPE:\t" + str(MAPE))
    MAE = mae_fn(realYData, rePCAData)
    NMAE = nmae_fn(realYData, rePCAData)
    AE = ae_fn(realYData, rePCAData)
    NAE = nae_fn(realYData, rePCAData)
    RMSE = rmse_fn(realYData, rePCAData)
    NRMSE = nrmse_fn(realYData, rePCAData)
    result = "测试集总的MAPE(%):\n" + str(MAPE) + \
             "\n测试集MAE:\n" + str(MAE) + \
             "\n测试集NMAE(%):\n" + str(NMAE) + \
             "\n测试集AE:\n" + str(AE) + \
             "\n测试集NAE(%):\n" + str(NAE) + \
             "\n测试集RMSE:\n" + str(RMSE) + \
             "\n测试集NRMSE(%):\n" + str(NRMSE) + \
             "\n\n测试集每条数据评价指标：\n" + \
             "时间t(s)\tMAPE(%)\tMAE\tNMAE(%)\tAE\tNAE(%)\tRMSE\tNRMSE(%)\n"
    nums = rePCAData.shape[0]
    labelList = np.zeros((1, 1))
    # picSavePath = r"..\E-ModelSave\B-Model_PredY_Results\ModelPart{0}\D_PredYShow\part{0}_predY_{1}".format(i, time)
    # 展示每条数据的预测情况
    totalMape = 0
    for j in range(nums):
        # break
        realData = realYData[j]
        predData = rePCAData[j]
        realYLabel = realYLabels[j]
        label = str(realYLabel)
        mape = mape_fn(realData, predData)
        mae = mae_fn(realData, predData)
        nmae = nmae_fn(realData, predData)
        ae = ae_fn(realData, predData)
        nae = nae_fn(realData, predData)
        rmse = rmse_fn(realData, predData)
        nrmse = nrmse_fn(realData, predData)
        result += label + "\t" + str(mape) + "\t" + str(mae) + "\t" + str(nmae) + "\t" + str(ae) + "\t" + \
                  str(nae) + "\t" + str(rmse) + "\t" + str(nrmse) + "\n"
        totalMape = totalMape + mape
        # """
        # 展示所有测试与真实数据以及其差值
        drawPic3DxyzT(x, y, z, realData, label + "s FEA")
        plt.savefig(os.path.join(picSavePath, label + "s_a_FEA.png"), dpi=300)
        plt.close('all')
        drawPic3DxyzT(x, y, z, predData, label + "s pred")
        plt.savefig(os.path.join(picSavePath, label + "s_b_pred.png"), dpi=300)
        plt.close('all')
        drawPic3DxyzT(x, y, z, predData - realData, label + "s difference(pred-FEA)")
        plt.savefig(os.path.join(picSavePath, label + "s_c_difference(pred-FEA).png"), dpi=300)
        plt.close('all')

        # 将真实与预测数据拉平，纵轴没有归一化
        fig = plt.figure(figsize=(18, 6))
        plt.subplot(131)
        plt.bar(range(len(realData)), realData)
        plt.title(label + "s FEA flatten")
        plt.ylabel("B/T")
        # plt.show()
        plt.subplot(132)
        plt.bar(range(len(predData)), predData)
        plt.title(label + "s pred flatten")
        plt.subplot(133)
        plt.bar(range(len(predData)), abs(realData - predData))
        plt.title(label + "s diff flatten")
        plt.savefig(os.path.join(picSavePath, label + "s_d_flatten_NoNormarl.png"), dpi=300)
        plt.close('all')

        # 将真实与预测数据拉平，纵轴归一化
        maxColor = max(np.max(realData), np.max(predData))
        maxColor += 0.1 * maxColor
        ticks = [0, 0.2 * maxColor, 0.4 * maxColor, 0.6 * maxColor, 0.8 * maxColor, maxColor]
        print("时间t: " + label + "\tmape: " + str(mape))
        fig = plt.figure(figsize=(18, 6))
        plt.subplot(131)
        plt.bar(range(len(realData)), realData)
        plt.yticks(ticks)
        plt.title(label + "s FEA flatten")
        plt.ylabel("B/T")
        # plt.show()
        plt.subplot(132)
        plt.bar(range(len(predData)), predData)
        plt.yticks(ticks)
        plt.title(label + "s pred flatten")
        plt.subplot(133)
        plt.bar(range(len(predData)), abs(realData - predData))
        plt.yticks(ticks)
        plt.title(label + "s diff flatten")
        plt.savefig(os.path.join(picSavePath, label + "s_e_flatten_Normal.png"), dpi=300)
        plt.close('all')
        # plt.show()
        # """
        # 训练数据与测试数据分布
        trainLabel = np.loadtxt(
            os.path.join(
                projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F01_Train\F01_Input{}\F01_inputRow.txt".format(i)))
        testLabel = np.loadtxt(
            os.path.join(
                projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F02_Test\F01_Input{}\F01_inputRow.txt".format(i)))
        trainData = np.loadtxt(
            os.path.join(
                projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F01_Train\F02_Output{}\F01_outputRow.txt".format(
                    i)))
        testData = np.loadtxt(
            os.path.join(
                projectPath + r"\F04_ExpLargePart\F02_TrainTestData\F02_Test\F02_Output{}\F01_outputRow.txt".format(i)))
        n = [0]
        title = "第" + str(n[0]) + "个点"
        # showDataRow(allLabel, allData, title)
        showDataRow(np.array(trainLabel), trainData[:, n[0]], title)
        showDataRow(np.array(testLabel), testData[:, n[0]], title)
        plt.savefig(os.path.join(picSavePath, title + ""), dpi=300)
        plt.close()

    avgMape = totalMape / nums
    result = result + "\n测试集每一条平均MAPE(%):\n" + str(avgMape)
    return result


if __name__ == "__main__":
    # 这也没有交叉验证啊...还要自己手动设置I的值，自己事先划分完成然后通过修改I完成每一折的实验...
    I = 9
    projectPath = r'F:\Pycharm Projects\dxnormaltransMag'
    trainXPath = projectPath + '/data/zstrainInput.txt'
    trainYPath = projectPath + '/data/trainPCA.txt'
    testXPath = projectPath + '/data/zstestInput.txt'
    testYPath = projectPath + '/data/testPCA.txt'

    """参数优化开始"""
    study = optuna.create_study(direction="minimize", study_name='net_trail{}'.format(I))
    studyName = study.study_name  # study_name未设置默认为None，这是干什么....

    study.optimize(objective, n_trials=30, timeout=60 * 60 * 200)  # 时间秒s
    """参数优化结束"""
    pruned_trials = study.get_trials(deepcopy=False, states=[TrialState.PRUNED])
    complete_trials = study.get_trials(deepcopy=False, states=[TrialState.COMPLETE])
    """打印细节"""
    print("Study statistics: ")
    print("  Number of finished trials: ", len(study.trials))
    print("  Number of pruned trials: ", len(pruned_trials))
    print("  Number of complete trials: ", len(complete_trials))

    print("Best trial:")
    trial = study.best_trial

    print("  Trial: ", trial.number)
    print("  Value: ", trial.value)

    print("  Params: ")
    detail = "loss\t" + str(float(trial.value)) + "\n" \
             + "Epochs\t"+ str(float(EPOCHES)) + "\n" \
             + "batchSize\t" + str(float(BATCHSIZE)) + "\n" \
             # + "lr\t" + str(float(lr)) + "\n" \
             # + "lr1\t" + str(float(lr1)) + "\n" \
             # + "lr2\t" + str(float(lr2)) + "\n"\
             # + "lr3\t" + str(float(lr3)) + "\n"
    # detail = detail + "n_layers\t{}\n".format(len(nlayers))
    # for layeri in(range(len(nlayers))):
    #     detail = detail + "n_units_l{}\t{}\n".format(layeri, nlayers[layeri])
    for key, value in trial.params.items():
        print("    {}: {}".format(key, value))
        detail = detail + "{}\t{}".format(key, value) + "\n"

    os.makedirs(projectPath + '/optuna_result/BestTrial{}'.format(trial.number))
    picSavePath = projectPath + '/optuna_result/BestTrial{}'.format(trial.number)
    # predYData = np.loadtxt(projectPath + '/optuna_result/BestTrial{}.txt'.format(trial.number))

    # results = showPredY(predYData, I, picSavePath)

    with open(os.path.join(picSavePath, "BestTrial{}.txt".format(trial.number)),
              "a") as file:
        file.write("\n" + "\n-------------\n\n" + "\n" + detail + "\n-------------")


    '''
    """
    手动查看各模型表现
    """
    # 要查看的trial
    studyName = "no-name-ee2652fe-519b-4a77-b866-058b4db663b9"
    trial_number = 65
    detail = "Epochs\t"+ str(float(EPOCHES)) + "\n" \
             + "batchSize\t" + str(float(BATCHSIZE)) + "\n" \
             # + "lr\t" + str(float(lr)) + "\n" \
             # + "lr1\t" + str(float(lr1)) + "\n" \
             # + "lr2\t" + str(float(lr2)) + "\n"\
             # + "lr3\t" + str(float(lr3)) + "\n"
    detail = detail + "n_layers\t{}\n".format(len(nlayers))
    for i in(range(len(nlayers))):
        detail = detail + "n_units_l{}\t{}\n".format(i, nlayers[i])
    if not os.path.exists(pathRow + r"\..\F02_Results\{}\Trial{}".format(studyName, trial_number)):
        os.makedirs(pathRow + r"\..\F02_Results\{}\Trial{}".format(studyName, trial_number))
    picSavePath = pathRow + r"\..\F02_Results\{}\Trial{}".format(studyName, trial_number)
    predYData = np.loadtxt(pathRow + r"\..\F02_Results\{}\trial{}.txt".format(studyName, trial_number))
    # print(predYData.shape)
    results = showPredY(predYData, I, picSavePath)

    with open(os.path.join(picSavePath, "Trial{}.txt".format(trial_number)),
              "a") as file:
        file.write("\n" + results + "\n-------------\n\n" + "\n" + detail + "\n-------------")
    '''