# 对所有数据做PCA降维，记录在磁场小的点的值
import numpy as np
from sklearn.decomposition import PCA


def allPCA(trainPath):
    '''
    训练PCA
    :param trainPath:
    :return:
    '''
    value_c = np.loadtxt(trainPath)  # 3200 * 1241
    # print(value_c.shape)
    pca = PCA(n_components=60)
    new_data = pca.fit_transform(value_c)
    print(new_data.shape)
    # 路径需要修改
    np.savetxt('../data/trainPCA.txt', new_data)
    # PCA均值数据
    np.savetxt('../pca result/mean_pca.txt', pca.mean_)
    # PCA特征向量
    np.savetxt('../pca result/vector_pca.txt', pca.components_)
    # PCA成分占比
    np.savetxt('../pca result/variance_pca.txt', pca.explained_variance_ratio_)
    print(pca.explained_variance_ratio_.sum(axis=0))
    print('training data PCA finished!')

if __name__ == '__main__':
    dataPath = '../data/cutOutput.txt'
    allPCA(trainPath)