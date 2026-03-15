import numpy as np
import random
from sklearn import model_selection
from sklearn.decomposition import PCA
import os
import shutil
from sklearn.metrics import mean_absolute_error, mean_squared_error,r2_score

# inputs = np.loadtxt('../data/cutInput.txt')  # (120, 4)
# outputs = np.loadtxt('../data/cutOutput.txt').T  # (1241, 120)
# print(inputs.shape)
# axis = np.loadtxt('../data/raw data/mag-100-10k-50-0.2-0.0005.txt', encoding='utf-8', comments='%')[:, :3]  # (1421, 3)
# print(axis)
# print("-----------------------")
# t0 = 0.04
# for i in range(outputs.shape[0]):
#     print(outputs[i, :].shape)  # (1241,)
#     data1 = np.c_[axis, outputs[i, :].reshape(-1, 1)]  # 将axis和磁场混合到一起
#     data2 = inputs[i, :]
#     print("data1.shape:",data1)
#     print("data2.shape:",data2)
def remove_last_column(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            # 分割每行为列
            columns = line.split()
            # 确保至少有一列（避免空行报错）
            if columns:
                # 删除最后一列并重新组合为字符串
                new_line = " ".join(columns[:-1])
            else:
                new_line = ""
            # 写入新行到输出文件
            outfile.write(new_line + "\n")

# 使用示例
input_filename = "E:/朱浩玮文件/Pycharm_Projects/dxnormaltransMag/data/train data/output/0.0405.txt"  # 替换为你的文件名
output_filename = "zuobiao.txt"  # 输出文件名

remove_last_column(input_filename, output_filename)
print(f"已删除最后一列，结果保存至: {output_filename}")

