# 从获取的仿真数据中截取数据
# 初始时选择从0.02到0.06的3个周期内共120条数据作为初始数据集

import numpy as np

def cutOUtIn():
    '''
    截取输出的磁场数据和输入数据（0.04-0.1）
    :return:
    '''
    outdata = np.loadtxt('../data/raw data/mag-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')
    # print(outdata.shape)   # (1241, 404)

    cutdata = outdata[:, 83:204]  # 从0.04开始的3个周期

    inprimvol = np.loadtxt('../data/raw data/primvol-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')[:, 1]
    inprimcur = np.loadtxt('../data/raw data/primcur-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')[:, 1]
    insecvol = np.loadtxt('../data/raw data/secvol-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')[:, 1]
    inseccur = np.loadtxt('../data/raw data/seccur-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')[:, 1]

    # indata1 = np.c_[inprimvol, insecvol]
    # indata2 = np.c_[inprimcur, inseccur]
    # inputdata = np.c_[indata1, indata2]

    cutinprimvol = inprimvol[80:201]
    cutinprimcur = inprimcur[80:201]
    cutinsecvol = insecvol[80:201]
    cutinseccur = inseccur[80:201]

    indata = np.c_[cutinprimvol, np.c_[cutinsecvol, np.c_[cutinprimcur, cutinseccur]]]
    # print(indata.shape)   # (121, 4)
    # print(cutdata.shape)   # (1241, 121)
    np.savetxt('../data/cutInput.txt', indata)
    np.savetxt('../data/cutOutput.txt', cutdata)

if __name__ == '__main__':
    cutOUtIn()