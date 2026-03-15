import math
import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

mpl.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(6, 4))
ax = fig.add_subplot(111)

x = np.arange(-10, 10)
y = np.where(x < 0, 0, x)

plt.xlim(-11, 11)
plt.ylim(-11, 11)

ax.spines['top'].set_color('none')
ax.spines['right'].set_color('none')

ax.xaxis.set_ticks_position('bottom')
ax.spines['bottom'].set_position(('data', 0))
ax.set_xticks([-10, -5, 0, 5, 10])
ax.yaxis.set_ticks_position('left')
ax.spines['left'].set_position(('data', 0))
ax.set_yticks([-10, -5, 5, 10])

plt.plot(x, y, label="ReLU", color="black")
# plt.legend()
plt.show()