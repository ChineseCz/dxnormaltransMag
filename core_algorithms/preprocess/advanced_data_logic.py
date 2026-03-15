import numpy as np
from scipy.fft import fft, fftfreq
import os
# 这个文件包含了智能数据质量评估、稳态识别和频谱分析的核心算法，适用于电压和电流的周期性数据处理。（ai）

def analyze_data_quality(file_path):
    """
    智能数据质量评估：检测缺失值、异常跳变及物理量程
    """
    try:
        data = np.loadtxt(file_path, encoding='utf-8', comments='%')
        
        # 统计学基础分析
        stats = {
            "rows": data.shape[0],
            "cols": data.shape[1],
            "has_nan": np.isnan(data).any(),
            "mean": np.mean(data),
            "std": np.std(data),
            "max": np.max(data),
            "min": np.min(data)
        }
        
        # 异常跳变检测 (梯度检测)
        if data.ndim == 2 and data.shape[1] > 3:
            # 假设前3列是坐标，后面是时间序列数据
            diff = np.diff(data[:, 3:], axis=1)
            stats["max_gradient"] = np.max(np.abs(diff))
            stats["is_smooth"] = stats["max_gradient"] < (stats["std"] * 5) # 简单启发式阈值
        
        return stats
    except Exception as e:
        return {"error": str(e)}

def detect_steady_state(time_series, dt=5e-4, threshold=0.01):
    """
    自适应稳态识别算法：
    基于滑动窗口的周期相似度比较 (RMS Error between cycles)
    """
    # 假设工频 50Hz, 一个周期 T = 0.02s
    points_per_cycle = int(0.02 / dt)
    num_points = len(time_series)
    
    if num_points < points_per_cycle * 2:
        return 0.0 # 数据不足
    
    # 计算相邻周期的 RMSE
    rmse_list = []
    for i in range(num_points - 2 * points_per_cycle):
        cycle1 = time_series[i : i + points_per_cycle]
        cycle2 = time_series[i + points_per_cycle : i + 2 * points_per_cycle]
        
        rmse = np.sqrt(np.mean((cycle1 - cycle2)**2))
        # 归一化 RMSE
        norm_rmse = rmse / (np.max(cycle1) - np.min(cycle1) + 1e-9)
        rmse_list.append(norm_rmse)
    
    # 寻找第一个稳定点
    for idx, val in enumerate(rmse_list):
        if val < threshold:
            # 找到稳定区间，返回时刻
            return idx * dt
            
    return 0.04 # 默认回退值

def get_fft_spectrum(time_series, dt=5e-4):
    """
    频谱分析：用于论文中展示数据处理前后的性能指标
    """
    n = len(time_series)
    yf = fft(time_series)
    xf = fftfreq(n, dt)[:n//2]
    power = 2.0/n * np.abs(yf[0:n//2])
    return xf.tolist(), power.tolist()

