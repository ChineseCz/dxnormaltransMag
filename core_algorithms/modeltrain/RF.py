# 用交叉验证与optuna超参数调优嵌套的RF训练及测试代码

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def rebuildPCA(lowdim_data):
    # pca_data = np.loadtxt('../result/mix/LR/predY_linearmodel.txt', encoding='utf-8', comments='#')
    mean_pca = np.loadtxt('../pca_result/mean_pca.txt', encoding='utf-8', comments='%')
    vector_pca = np.loadtxt('../pca_result/vector_pca.txt', encoding='utf-8', comments='%')
    print(lowdim_data.shape)    # (4,)
    print(vector_pca.shape)    # (296277,)
    print(mean_pca.shape)   # (296277,)
    huanyuan_data = np.matmul(lowdim_data, vector_pca) + mean_pca
    # np.savetxt('../result/DNN/predY_DNNmodel_rebuild.txt', huanyuan_data)
    return huanyuan_data


# 需要还原后计算mape
def mape_fn(yTrue, yPred):
    # for i in range(yTrue)
    return np.mean(np.abs((yPred - yTrue) / yTrue)) * 100


train_input = np.loadtxt('../data/zstrainInput.txt')
# print(train_input.shape)
test_input = np.loadtxt('../data/zstestInput.txt')
train_output = np.loadtxt('../data/trainPCA.txt')
# print(train_output.shape)
test_output = np.loadtxt('../data/testPCA.txt')
train_outreal = np.loadtxt('../data/trainOutput.txt')


kf = KFold(n_splits=5, shuffle=True, random_state=0)   # 16条数据4折交叉验证
for train_index, test_index in kf.split(train_input):
    print("TRAIN:", train_index, "TEST:", test_index)
    traininputi = [train_input[indexi] for indexi in train_index]
    trainoutputi = np.array([train_output[indexi] for indexi in train_index])
    validinputi = np.array([train_input[indexi] for indexi in test_index])
    validoutputi = np.array([train_output[indexi] for indexi in test_index])
    # validoutreal = np.array([train_outreal[indexi] for indexi in test_index])

    rf = RandomForestRegressor( n_estimators = 400,
                                criterion = 'mae',
                                max_depth = 3,
                                # min_samples_split = 2,
                                min_samples_leaf = 5,
                                # min_weight_fraction_leaf = 0.0,
                                max_features = 'auto',
                                max_leaf_nodes = None,
                                # min_impurity_split = 1e-07,
                                # bootstrap = True,
                                # oob_score = False,
                                # n_jobs = 1,
                                # random_state = None,
                                # verbose = 0,
                                # warm_start = False
                                )

    rf.fit(traininputi, trainoutputi)
    pred = rf.predict(validinputi)

    # rebuildy_pre = rebuildPCA(pred)

    test_mae = mean_absolute_error(validoutputi, pred)
    test_mape = mape_fn(validoutputi, pred)
    test_mse = mean_squared_error(validoutputi, pred)
    test_r2 = r2_score(validoutputi, pred)

    print('测试集MSE:' + str(test_mse))
    print('测试集MAE:' + str(test_mae))
    print('测试集MAPE:' + str(test_mape))
    print('测试集R2:' + str(test_r2))