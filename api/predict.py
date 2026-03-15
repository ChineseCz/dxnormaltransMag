from flask import Blueprint, request, jsonify

predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/realtime', methods=['POST'])
def realtime_predict():
    """实时磁场预测接口"""
    req_data = request.json
    # 获取电压电流输入
    inputs = req_data.get('inputs') # [v_prim, v_sec, i_prim, i_sec]
    
    # 这里模拟预测逻辑
    # 实际流程：加载模型 -> 归一化输入 -> 预测PCA系数 -> 逆PCA变换 -> 返回物理场
    return jsonify({
        "status": "success",
        "predicted_point": [0.0012, 0.0015, -0.0008], # 样例输出
        "msg": "预测计算完成"
    })

