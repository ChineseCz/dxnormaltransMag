"""快速本地推理测试，不启动服务器"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 模拟一个激活的 DNN 模型 (id=18)
from api.ml.predict import _get_model_record, _parse_hidden_layers, _load_torch_model
import numpy as np, torch

model_rec = _get_model_record(18)
print("model_rec:", {k: v for k, v in model_rec.items() if k != 'metrics'})

config  = model_rec['config'] or {}
metrics = model_rec['metrics'] or {}
input_dim  = int(metrics.get('input_dim', 4))
output_dim = int(metrics.get('output_dim', 60))
used_pca    = bool(metrics.get('used_pca', False))
used_zscore = bool(metrics.get('used_zscore', False))
print(f"input_dim={input_dim}, output_dim={output_dim}, pca={used_pca}, zscore={used_zscore}")

# 构建模型（仅测试 hidden_layers 解析）
from api.ml.predict import _parse_hidden_layers
hl = _parse_hidden_layers(config.get('hidden_layers'))
print("parsed hidden_layers:", hl)

# 加载模型文件
dataset_dir = os.path.join('backend', 'datasets', model_rec['dataset_id'])
model_file = os.path.basename(model_rec['file_path'])
model_path = os.path.join(dataset_dir, 'model', model_file)
print("model_path:", model_path, "exists:", os.path.exists(model_path))

if os.path.exists(model_path):
    net = _load_torch_model('DNN', model_path, input_dim, output_dim, config)
    print("Model loaded OK!")

    # 测试推理
    x = np.array([24.808141, 24.918424, -0.248081, -0.002492], dtype=np.float32)
    # zscore 归一化
    data_dir = os.path.join(dataset_dir, 'data')
    mu    = np.loadtxt(os.path.join(data_dir, 'zstrainmuInput.txt')).astype(np.float32)
    sigma = np.loadtxt(os.path.join(data_dir, 'zstrainsigmaInput.txt')).astype(np.float32)
    sigma = np.where(sigma < 1e-10, 1.0, sigma)
    x_norm = (x - mu) / sigma
    print("x_norm:", x_norm)

    with torch.no_grad():
        y_pca = net(torch.FloatTensor(x_norm.reshape(1, -1))).numpy()[0]
    print("y_pca shape:", y_pca.shape, "sample:", y_pca[:5])

    # 逆 PCA
    pca_dir = os.path.join(dataset_dir, 'pca_result')
    pca_mean = np.loadtxt(os.path.join(pca_dir, 'mean_pca.txt')).astype(np.float64)
    pca_vec  = np.loadtxt(os.path.join(pca_dir, 'vector_pca.txt')).astype(np.float64)
    field = y_pca.astype(np.float64) @ pca_vec + pca_mean
    print("field shape:", field.shape)
    print(f"field stats: min={field.min():.6f}, max={field.max():.6f}, mean={field.mean():.6f}")
    print("SUCCESS!")

