# 因为电压和电流是周期性的，得保证输入和输出是一一对应的，不能出现相同的输入对应不同的输出
import numpy as np

def checkInput():
    inputdata = np.loadtxt('../data/cutInput.txt')   # (120,4)
    for i in range(inputdata.shape[1]):
        inputdatai = inputdata[:, i]
        print(inputdatai.shape)
        print(np.max(inputdatai))
        print(np.min(inputdatai))

    # for i in range(inputdata.shape[0] - 1):

    print(inputdata[-1, :])
    print(inputdata[-2, :])

def checkOut():
    outdata = np.loadtxt('../data/cutOutput.txt')

    print(outdata.shape)
    print(np.max(outdata))   # 1.0508028125865911
    print(np.min(outdata))  # 3.858155586125297e-06


if __name__ == '__main__':
    # checkOut()
    checkInput()

