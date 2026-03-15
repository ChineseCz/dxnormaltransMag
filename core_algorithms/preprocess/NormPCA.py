# 因为PCA降维后的结果本身仍然存在数量级的差异，所以对PCA降维后的结果做归一化
import numpy as np

def zscoreNormalize(data, mu, sigma):
    '''
    使用零均值（zero-score）归一化，把PCA降维后的所有维度数据映射到1个范围内，消除各维度特征之间数量级带来的训练权重偏向。
    但是这一步骤是否必须不确定，因为数量级较小的维度经过PCA还原后对原始数据的影响（因为对方差的贡献度问题）并不像PCA还原前那么明显（可能在后面的维度预测不准确，但是还原后的数据差异很小）
    :return:
    '''
    data = (data - mu) / sigma
    return data


def outdataNormalize():
    '''
    分别对训练和测试数据在1241个维度上进行降维，注意测试数据降维时使用的是训练数据的均值和标准差
    :return:
    '''
    trainPCAdata = np.loadtxt('../data/trainPCA.txt')   # (96, 60)
    testPCAdata = np.loadtxt('../data/testPCA.txt')  # (25, 60)
    # print(trainPCAdata.shape)

    # 对训练集输出做归一化
    new_trainPCAdata = np.zeros((96, 1))
    train_mu = np.zeros((1, 1))
    train_sigma = np.zeros((1, 1))
    for i in range(trainPCAdata.shape[1]):
        featurei = trainPCAdata[:, i]
        mui = np.mean(featurei).reshape(-1, 1)
        sigmai = np.std(featurei).reshape(-1, 1)
        zsi = zscoreNormalize(featurei, mui, sigmai).reshape(96, 1)
        new_trainPCAdata = np.c_[new_trainPCAdata, zsi]
        # print(new_trainPCAdata.shape)
        train_mu = np.c_[train_mu, mui]
        train_sigma = np.c_[train_sigma, sigmai]

    new_trainPCAdata = np.delete(new_trainPCAdata, 0, axis=1)
    train_mu = np.delete(train_mu, 0, axis=1)
    train_sigma = np.delete(train_sigma, 0, axis=1)
    print(new_trainPCAdata.shape)
    print(train_mu.shape)
    print(train_sigma.shape)

    np.savetxt('../data/zstrainPCA.txt', new_trainPCAdata)
    np.savetxt('../data/zstrainmu.txt', train_mu)
    np.savetxt('../data/zstrainsigma.txt', train_sigma)

    # 测试集的归一化有问题
    # 测试集数据归一化（利用训练集数据的mu和sigma
    new_testPCAdata = np.zeros((25, 1))
    for j in range(testPCAdata.shape[1]):
        featurej = testPCAdata[:, j]
        muj = train_mu[:, j]
        sigmaj = train_sigma[:, j]
        zsj = zscoreNormalize(featurej, muj, sigmaj).reshape(25, 1)
        print(zsj.shape)
        print(max(zsj))
        new_testPCAdata = np.c_[new_testPCAdata, zsj]
    new_testPCAdata = np.delete(new_testPCAdata, 0 ,axis=1)
    print(new_testPCAdata.shape)
    np.savetxt('../data/zstestPCA.txt', new_testPCAdata)

if __name__ == '__main__':

    outdataNormalize()
