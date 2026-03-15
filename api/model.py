from flask import Blueprint, request, jsonify
import os

model_bp = Blueprint('model', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'core_algorithms', 'model')

@model_bp.route('/list', methods=['GET'])
def list_models():
    """获取已训练模型列表"""
    try:
        files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pth')]
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@model_bp.route('/train', methods=['POST'])
def train_model():
    """触发模型训练"""
    req_data = request.json
    m_type = req_data.get('model_type', 'DNN')
    # 这里后续可以调用 modeltrain 目录下的脚本
    return jsonify({"status": "starting", "msg": f"正在启动 {m_type} 模型训练任务..."})
