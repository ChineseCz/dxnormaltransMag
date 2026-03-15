import numpy as np
import torch
import torch.nn as nn
import datetime


class NetShortCircuit(nn.Module):
    def __init__(self):
        super(NetShortCircuit, self).__init__()
        self.fc1 = nn.Linear(4, 64)
        self.fc2 = nn.Linear(64, 8)
        # self.drop1 = nn.Dropout()
        self.fc3 = nn.Linear(8, 128)
        # self.drop2 = nn.Dropout()
        self.fc4 = nn.Linear(128, 512)
        # self.drop3 = nn.Dropout()
        self.fc5 = nn.Linear(512, 512)
        # self.fc6 = nn.Linear(256, 64)
        self.fc7 = nn.Linear(512, 60)

    def forward(self, x):
        x = self.fc1(x)
        x = torch.relu(x)
        x = self.fc2(x)
        x = torch.relu(x)
        # x = self.drop1(x)
        x = self.fc3(x)
        x = torch.relu(x)
        # x = self.drop2(x)
        x = self.fc4(x)
        x = torch.relu(x)
        # x = self.drop3(x)
        x = self.fc5(x)
        x = torch.relu(x)
        # x = self.fc6(x)
        # x = torch.relu(x)
        x = self.fc7(x)
        return x

def rebuildPCA(lowdim_data, mean_pca, vector_pca):
    # pca_data = np.loadtxt('../result/mix/LR/predY_linearmodel.txt', encoding='utf-8', comments='#')
    # mean_pca = np.loadtxt('./data/pcaData/pcaDim01/pcaDim1-mean.txt', comments='%')
    # vector_pca = np.loadtxt('./data/pcaData/pcaDim01/pcaDim1-vector.txt', comments='%').reshape(1, -1)
    # print(lowdim_data.shape)
    # print(vector_pca.shape)
    huanyuan_data = np.matmul(lowdim_data, vector_pca) + mean_pca
    # np.savetxt('../result/mix/LR/predY_linearmodel_rebuild.txt', huanyuan_data)
    # print(huanyuan_data.shape)
    return huanyuan_data

def UseModelDNN(load_model_path, test_input, mean, vector):
    # start = datetime.datetime.now()
    device = torch.device("cpu")
    net = NetShortCircuit().to(device)
    net.load_state_dict(torch.load(load_model_path))   # loadmodel 费时1s
    load1 = datetime.datetime.now()
    # print(str(load1 - start))
    # logging.info('loading model finished!')
    # test_input = np.array(float(str_test_input))
    # print(test_input.shape)
    data = torch.from_numpy(test_input)
    # mid1 = datetime.datetime.now()
    # data = torch.unsqueeze(data, 1)
    # mid2 = datetime.datetime.now()
    data = data.to(device=device, dtype=torch.float32)
    predY = net(data)
    predY = predY.data.cpu().numpy()
    load2 = datetime.datetime.now()
    rebuild_predY = rebuildPCA(predY, mean, vector)
    end = datetime.datetime.now()
    cost_time = str(end - load1)
    # cost_time1 = str(end - load2)
    # mid_time = str(mid1 - start)
    print("testing time:" + cost_time)
    # print("rebuild time" + cost_time1)
    return rebuild_predY


if __name__ == '__main__':
    load_model_path = './model/DNN_2023-03-25-15-24-37.pth'
    mean_pca = np.loadtxt('./data/mean_pca.txt', comments='%')
    vector_pca = np.loadtxt('./data/vector_pca.txt', comments='%')
    test_input = np.array([-9.832595976954838779e-01, -9.885149800291961331e-01, 9.504103933898914169e-01,
                           9.885149800292000188e-01]).reshape(1, -1)
    UseModelDNN(load_model_path, test_input, mean_pca, vector_pca)
