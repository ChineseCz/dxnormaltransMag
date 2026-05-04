import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from abc import ABC, abstractmethod


# ==========================================
# 1. 抽象降维接口 (对应类图 AbstractReducer)
# ==========================================
class AbstractReducer(ABC):
    """降维算子策略接口，强制子类实现拟合与单向转换分离"""

    @abstractmethod
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def transform(self, X: np.ndarray) -> np.ndarray:
        pass


# ==========================================
# 2. 线性算子：PCA 策略实现
# ==========================================
class PCAReducer(AbstractReducer):
    def __init__(self, n_components: int):
        self.pca = PCA(n_components=n_components)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        # 计算协方差矩阵，提取并固化特征向量（投影矩阵）
        return self.pca.fit_transform(X)

    def transform(self, X: np.ndarray) -> np.ndarray:
        # 严格复用拟合好的投影矩阵，执行单向线性映射
        return self.pca.transform(X)


# ==========================================
# 3. 非线性算子：AE 策略实现
# ==========================================
class AutoEncoderReducer(AbstractReducer):
    def __init__(self, input_dim: int, latent_dim: int):
        # 初始化编码器网络拓扑
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, latent_dim)
        )
        # 此处省略 Decoder 的定义与完整的反向传播训练循环代码

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        # 伪代码：执行深度学习反向传播，更新并固化 Encoder 神经网络权重
        # self._train_autoencoder_with_backprop(X)
        return self.transform(X)

    def transform(self, X: np.ndarray) -> np.ndarray:
        # 冻结网络参数（复用权重），开启 eval 推理模式
        self.encoder.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X)
            # 复用神经网络参数执行非线性隐空间提取
            return self.encoder(X_tensor).numpy()


# ==========================================
# 核心引擎：上下文调度与防泄露流水线
# ==========================================
class SecureDataPipeline:
    def __init__(self, reducer_strategy: AbstractReducer):
        self.scaler = StandardScaler()
        # 动态注入具体算子 (PCA 或 AE)，实现控制反转
        self.reducer = reducer_strategy
        self.is_fitted = False

    def fit_transform_train(self, X_train: np.ndarray) -> np.ndarray:
        X_scaled = self.scaler.fit_transform(X_train)
        # 动态路由至底层算子，提取并固化特征提取权重
        X_reduced = self.reducer.fit_transform(X_scaled)
        self.is_fitted = True
        return X_reduced

    def transform_test(self, X_test: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("流水线未初始化，禁止处理测试集数据！")
        X_scaled = self.scaler.transform(X_test)
        return self.reducer.transform(X_scaled)







