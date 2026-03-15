# 支持向量回归
from sklearn.multioutput import MultiOutputRegressor
from sklearn.svm import SVR
import numpy as np
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import optuna
from optuna.trial import TrialState
import sklearn
from sklearn.ensemble import RandomForestRegressor

# 需要还原后计算mape
def mape_fn(yTrue, yPred):
    # for i in range(yTrue)
    return np.mean(np.abs((yPred - yTrue) / yTrue)) * 100

def rebuild_PCA(pca_data):
    # pca_data = np.loadtxt('../data/train_output.txt', encoding='utf-8', comments='%')
    mean_pca = np.loadtxt('../pca result/mean_pca.txt', encoding='utf-8', comments='%')
    vector_pca = np.loadtxt('../pca result/vector_pca.txt', encoding='utf-8', comments='%')

    # print(vector_pca.shape)  # (296277,)
    # print(pca_data.shape)  # (5, 1)
    huanyuan_data = np.matmul(pca_data, vector_pca) + mean_pca
    # huanyuan_data = np.matmul(pca_data.reshape(-1, 1), vector_pca.reshape(1, -1)) + mean_pca
    # print(raw_data.shape)
    # print(huanyuan_data.shape)
    # print('mape: ' + str(mape_fn(raw_data, huanyuan_data)) + '%')
    return huanyuan_data


rf = RandomForestRegressor( n_estimators = 286,
                                criterion = 'mse',
                                max_depth = 58,
                                min_samples_split = 2,
                                # min_samples_leaf = min_samples_leaf,
                                # min_weight_fraction_leaf = 0.0,
                                max_features = 'auto',
                                # max_leaf_nodes = None,
                                # min_impurity_split = 1e-07,
                                # bootstrap = True,
                                # oob_score = False,
                                # n_jobs = 1,
                                # random_state = None,
                                # verbose = 0,
                                # warm_start = False
)


train_input = np.loadtxt('../data/zstrainInput.txt')  # (40, 1)
    # print(train_input.shape)
test_input = np.loadtxt('../data/zstestInput.txt')
train_output = np.loadtxt('../data/trainPCA.txt')
    # print(train_output.shape)
test_output = np.loadtxt('../data/testPCA.txt')
test_outreal = np.loadtxt('../data/testOutput.txt')

rf.fit(train_input, train_output)

y_pred = rf.predict(test_input)
pred_rebuild = rebuild_PCA(y_pred)

print('MSE: ', mean_squared_error(test_outreal, pred_rebuild))
print('MAE: ', mean_absolute_error(test_outreal, pred_rebuild))
print('rmse: ', np.sqrt(mean_squared_error(test_outreal, pred_rebuild)))
# print('MAPE: ', mape_fn(test_outreal, pred_rebuild))
print('r2: ' + str(r2_score(test_outreal, pred_rebuild)))
print('MAPE: ', mape_fn(test_outreal, pred_rebuild))
