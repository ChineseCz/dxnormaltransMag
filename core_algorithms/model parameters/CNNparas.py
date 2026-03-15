# -*- coding: utf-8 -*-
# 发热功率密度数据PCA降维后保留的主成分在第一个维度上就保持在1e+8或者1e+7的数量级，第二个维度开始降到1e-2和1e-1数量级
import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader   # 将data读取存储在loader中
from torch.utils.data import TensorDataset
import time
import datetime

# 训练集PCA结果
trainY_path = './data/trainPCA.txt'
# 测试集标签（位置+电流）
testX_path = './data/zstestInput.txt'
testY_path = './data/testPCA.txt'
# test_input = test_input.reshape(-1, 1)
# 训练数据的标签（位置+电流）
trainX_path = './data/zstrainInput.txt'
# logs = "../log/DNN-org-pca"
predY_save_path = './result/CNN'

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# def mape_fn(yTrue, yPred):
#     return torch.mean(torch.abs((yPred - yTrue) / yTrue)) * 100

#网络参数数量
def get_parameter_number(net):
    total_num = sum(p.numel() for p in net.parameters())
    trainable_num = sum(p.numel() for p in net.parameters() if p.requires_grad)
    return {'Total': total_num, 'Trainable': trainable_num}

class NetShortCircuit(nn.Module):
    def __init__(self):
        super(NetShortCircuit, self).__init__()
        self.fc1 = nn.Linear(4, 8)   # (4, 1, 64)
        self.cov1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=2, stride=1)
        self.max_pool1 = nn.MaxPool1d(kernel_size=2, stride=1)
        self.cov2 = nn.Conv1d(in_channels=32, out_channels= 16, kernel_size=2, stride=1)
        self.max_pool2 = nn.MaxPool1d(kernel_size=2, stride=1)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 60)

    def forward(self, x):
        # print(x)  # torch.Size([8, 1, 4])
        x = F.relu(self.fc1(x))
        # print(x.size())   # # torch.Size([8, 1, 8])
        # print(x)
        x = F.relu(self.cov1(x))
        # print(x.shape)   # ([8, 32, 7])
        x = self.max_pool1(x)
        # print(x.shape)   # ([8, 32, 6])
        x = F.relu(self.cov2(x))
        # print(x.shape)   # torch.Size([8, 32, 5])
        x = self.max_pool2(x)
        # print(x.shape)   # torch.Size([8, 32, 4])
        x = x.view(-1, 16 * 4)
        # print(x.shape)
        # x = F.relu(self.fc6(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        # print(x.shape)
        return x


lr = 1e-3
# lr1 = 1.908408957894138e-06
# lr2 = 3.513436771462793e-07
# lr3 = 2.3638194866742972e-08
BATCH_SIZE = 32
epochs = 20000
net = NetShortCircuit().to(device)
print(get_parameter_number(net))
