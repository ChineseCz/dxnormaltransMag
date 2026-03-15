# -*- coding: utf-8 -*-
# 发热功率密度数据PCA降维后保留的主成分在第一个维度上就保持在1e+8或者1e+7的数量级，第二个维度开始降到1e-2和1e-1数量级
import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader   # 将data读取存储在loader中
from torch.utils.data import TensorDataset
import time

#训练集PCA结果
trainY_path = './data/trainPCA.txt'
#测试集标签（位置+电流）
testX_path = './data/zstestInput.txt'
testY_path = './data/testPCA.txt'
# test_input = test_input.reshape(-1, 1)
# 训练数据的标签（位置+电流）
trainX_path = './data/zstrainInput.txt'
predY_save_path = './result/DNN'


def get_parameter_number(net):    # 网络参数数量
    total_num = sum(p.numel() for p in net.parameters())
    trainable_num = sum(p.numel() for p in net.parameters() if p.requires_grad)
    return {'Total': total_num, 'Trainable': trainable_num}


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

lr = 0.00011525825763535917
lr1 = 1.908408957894138e-06
lr2 = 3.513436771462793e-07
lr3 = 2.3638194866742972e-08
BATCH_SIZE = 16
epochs = 10000
net = NetShortCircuit()
print(get_parameter_number(net))
