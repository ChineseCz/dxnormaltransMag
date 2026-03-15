# 对于输入的参数随时间变化的情况做可视化
import numpy as np
import matplotlib.pyplot as plt
import pylab as pl
from scipy.interpolate import make_interp_spline

from matplotlib import rcParams

config = {
    "font.family": 'serif',  # sans-serif/serif/cursive/fantasy/monospace
    "font.size": 24,  # medium/large/small
    'font.style': 'normal',  # normal/italic/oblique
    'font.weight': 'bold',  # bold
    "mathtext.fontset": 'cm',  # 'cm' (Computer Modern)
    "font.serif": ['Times New Roman'],  # 'Simsun'宋体
    "axes.unicode_minus": False,  # 用来正常显示负号
         }
rcParams.update(config)

def moving_average(interval, windowsize):
    window = np.ones(int(windowsize)) / float(windowsize)
    re = np.convolve(interval, window, 'same')
    return re


def plotCurVari(data, ctype):
    time_data = np.linspace(0.04, 0.1, 121)   # (81,)

    # totalA_av = moving_average(totalA, 10)
    # totalB_av = moving_average(totalB, 10)
    # totalC_av = moving_average(totalC, 10)
    fig = plt.figure(figsize = (12,12))    #figsize是图片的大小`
    ax1 = fig.add_subplot(1, 1, 1) # ax1是子图的名字`
    pl.plot(time_data,data,'b-*')
    # p2 = pl.plot(time_data, totalB,'g-^', label=u'b相')
    # p3 = pl.plot(time_data, totalC, 'b-.', label=u'c相')
    # pl.legend()
    plt.legend(fontsize=20)
    # box = ax1.get_position()
    # ax1.set_position([box.x0, box.y0, box.width, box.width * 0.8])
    # ax1.legend(loc='center left', bbox_to_anchor=(0.2, 1.12), ncol=3)
    pl.xlabel(u't/s')
    pl.ylabel(ctype + '/A')
    # plt.title(ctype + ' variation')
    plt.savefig('../figure/InputVari/' + ctype + '_variation.jpg', bbox_inches='tight')
    # plt.show()

def plotVolVari(data, ctype):
    time_data = np.linspace(0.04, 0.1, 121)   # (81,)

    # totalA_av = moving_average(totalA, 10)
    # totalB_av = moving_average(totalB, 10)
    # totalC_av = moving_average(totalC, 10)
    fig = plt.figure(figsize = (12,12))    #figsize是图片的大小`
    ax1 = fig.add_subplot(1, 1, 1) # ax1是子图的名字`
    pl.plot(time_data,data,'b-*')
    # p2 = pl.plot(time_data, totalB,'g-^', label=u'b相')
    # p3 = pl.plot(time_data, totalC, 'b-.', label=u'c相')
    # pl.legend()
    # plt.legend(fontsize=20)
    # box = ax1.get_position()
    # ax1.set_position([box.x0, box.y0, box.width, box.width * 0.8])
    # ax1.legend(loc='center left', bbox_to_anchor=(0.2, 1.12), ncol=3)
    pl.xlabel(u't/s')
    pl.ylabel(ctype + '/V')
    # plt.title(ctype + ' variation')
    plt.savefig('../figure/InputVari/' + ctype + '_variation.jpg', bbox_inches='tight')
    # plt.show()


if __name__ == '__main__':
    # path改为cut后的path
    data = np.loadtxt('../data/cutInput.txt')
    data1 = data[:, 0]
    data2 = data[:, 1]
    data3 = data[:, 2]
    data4 = data[:, 3]

    plotVolVari(data1, 'Induced voltage in the primary winding')
    plotVolVari(data2, 'Induced voltage in the secondary winding')
    plotCurVari(data3, 'Current in the primary winding')
    plotCurVari(data4, 'Current in the secondary winding')

