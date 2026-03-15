import torch
from torch import nn

def corr2d(X, K):
    h, w = K.shape
    Y = torch.zeros((X.shape[0] - h + 1, X.shape[1] - w + 1))
    for i in range(Y.shape[0]):
        for j in range(Y.shape[1]):
            Y[i, j] = (X[i: i + h, j: j + w] * K).sum()
    return Y


x = torch.tensor([[3,2,2,1],
              [2,0,1,2],
              [3,1,1,3],
              [2,3,2,0]])
w = torch.tensor([[0,1,2],
              [1,2,1],
              [0,1,2]])

y = corr2d(x,w)
print(y)