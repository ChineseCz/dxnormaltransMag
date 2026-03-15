# 所有点上的磁通均值随着时间参数变化的曲线
import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt('../data/cutOutput.txt', comments='%', encoding='utf-8')


# 选第一个周期后的连续3个周期
time_data = np.linspace(0.04, 0.10, 121)
# mean_data = np.zeros((1, 1))
# for i in range(121):
#     data_i = data[:, i]
#     # print(np.mean(data_i))
#     mean_data = np.r_[mean_data, np.mean(data_i).reshape(-1, 1)]
# mean_data = np.delete(mean_data, 0, axis=0)
# print(mean_data.shape)  # (4000, 1)
# print(time_data.shape)  # (4000,)

# 第一个坐标点的磁通变化情况
first_data = data[1, :]
last_data = data[-1, :]
print(max(first_data))
print(min(first_data))

wrong_index = []
for i in range(len(time_data)):
    if time_data[i] == 0.0415:
        wrong_index.append(i)
    elif time_data[i] == 0.0615:
        wrong_index.append(i)
    elif time_data[i] == 0.0640:
        wrong_index.append(i)
    elif time_data[i] == 0.0840:
        wrong_index.append(i)

wrong_x = np.array([0.0415, 0.0615, 0.0640, 0.0840])
wrong_y = np.array([first_data[wrong_index[0]], first_data[wrong_index[1]], first_data[wrong_index[2]]])

plt.figure()
# 去除顶部和右边框框
ax = plt.axes()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.xlabel('time/s')  # x轴标签
plt.ylabel('mag/T')  # y轴标签

# plt.xticks(time_data[::5])
plt.yticks()
print(time_data.shape)
print(first_data.shape)

# 以x_train_loss为横坐标，y_train_loss为纵坐标，曲线宽度为1，实线，增加标签，训练损失，
# 默认颜色，如果想更改颜色，可以增加参数color='red',这是红色。
# plt.plot(time_data, mean_data, linewidth=1, linestyle="solid", label="test loss")
plt.scatter(time_data, first_data, s=1)
plt.scatter(wrong_x, wrong_y, s=1, color='red')
# plt.legend()
plt.title('variation curve')
plt.show()


