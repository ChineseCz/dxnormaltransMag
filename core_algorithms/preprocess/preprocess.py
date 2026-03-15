import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import MaxNLocator
from scipy import interpolate
import numpy as np
from matplotlib import rcParams

config = {
    "font.family": 'serif',  # sans-serif/serif/cursive/fantasy/monospace
    "font.size": 16,  # medium/large/small
    'font.style': 'normal',  # normal/italic/oblique
    'font.weight': 'bold',  # bold
    "mathtext.fontset": 'cm',  # 'cm' (Computer Modern)
    "font.serif": ['Times New Roman'],  # 'Simsun'宋体
    "axes.unicode_minus": False,  # 用来正常显示负号
         }
rcParams.update(config)

def plot_point(plot_data, ctype):
    fig = plt.figure(figsize=(10, 6))
    ax = Axes3D(fig)
    x = plot_data[:, 0]
    y = plot_data[:, 1]
    z = plot_data[:, 2]
    color = plot_data[:, 3]
    max_color = np.max(color)
    colorband = max_color - np.min(color)

    jet = plt.cm.get_cmap('jet')
    sc = ax.scatter(x, y, z, vmin=np.min(color), vmax=max_color, s=1, c=color, cmap=jet)

    cbar = plt.colorbar(sc)
    tick_locator = ticker.MaxNLocator(nbins=5)  # colorbar上的刻度值个数
    cbar.locator = tick_locator
    cbar.set_ticks([np.min(color), np.min(color) + 0.25 * colorband, np.min(color) + 0.5 * colorband,
                    np.min(color) + 0.75 * colorband, max_color])
    # cbar.formatter.set_scientific(True)  # 设置科学计数法
    cbar.formatter.set_powerlimits((0, 0))  # 设置colorbar为科学计数法
    cbar.set_label("B/T")
    cbar.update_ticks()
    ax.set_xlabel('x/mm')
    ax.set_ylabel('y/mm')
    ax.set_zlabel('z/mm')
    # plt.title(ctype + 's_real')
    # plt.tight_layout()
    plt.savefig('../figure/original/' + ctype + 's_real.jpg', bbox_inches='tight')  # 设置bbox_inches解决显示不全
    # plt.show()
    plt.close()


def pre_visual():

    raw_data = np.loadtxt('../data/raw data/mag-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')
    data_axis = raw_data[:, :3]
    t0 = 0.0
    for i in range(raw_data.shape[1] - 3):
        mag_data = raw_data[:, 3 + i]   # (21912,)
        plot_data = np.c_[data_axis, mag_data.reshape(-1, 1)]
        plot_point(plot_data, '{:.4f}'.format(t0 + 5e-4 * i))


if __name__ == '__main__':
    pre_visual()
