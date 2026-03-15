from flask import Blueprint, request, jsonify
import os
import numpy as np
from core_algorithms.preprocess.advanced_data_logic import analyze_data_quality, detect_steady_state

data_bp = Blueprint('data', __name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'core_algorithms', 'data', 'raw data')
DATA_SPLIT_DIR = os.path.join(BASE_DIR, 'core_algorithms', 'data', 'splited data')

@data_bp.route('/upload/raw', methods=['POST'])
def upload_raw_data():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    file_path = os.path.join(DATA_RAW_DIR, filename)
    file.save(file_path)
    
    stats = analyze_data_quality(file_path)
    
    return jsonify({
        "message": f"File {filename} uploaded successfully.",
        "analysis": stats,
        "filename": filename
    })

@data_bp.route('/auto-detect', methods=['POST'])
def auto_detect_stable_point():
    filenames = os.listdir(DATA_RAW_DIR)
    vol_file = next((f for f in filenames if 'vol' in f.lower() or 'cur' in f.lower()), None)
    
    if not vol_file:
        return jsonify({"error": "No voltage/current data found to analyze."}), 404
    
    file_path = os.path.join(DATA_RAW_DIR, vol_file)
    data = np.loadtxt(file_path, encoding='utf-8', comments='%')[:, 1]
    
    t0 = detect_steady_state(data)
    
    return jsonify({
        "t0": t0,
        "suggested_msg": f"Detected steady state around {t0:.4f}s based on cycle RMSE."
    })

@data_bp.route('/processed-status', methods=['GET'])
def processed_data_status():
    """检查数据处理流水线各步骤产出文件是否存在，以及训练集/测试集的维度信息"""
    DATA_DIR = os.path.join(BASE_DIR, 'core_algorithms', 'data')
    PCA_DIR = os.path.join(BASE_DIR, 'core_algorithms', 'pca result')

    # 定义流水线各阶段关键产出文件
    pipeline_files = {
        'cut': {
            'label': '稳态截取',
            'files': ['cutInput.txt', 'cutOutput.txt'],
        },
        'split': {
            'label': '训练/测试划分',
            'files': ['trainInput.txt', 'trainOutput.txt', 'testInput.txt', 'testOutput.txt'],
        },
        'pca': {
            'label': 'PCA 降维',
            'files': ['trainPCA.txt', 'testPCA.txt'],
            'extra_dir': PCA_DIR,
            'extra_files': ['mean_pca.txt', 'vector_pca.txt'],
        },
        'zscore': {
            'label': 'Z-Score 归一化',
            'files': ['zstrainInput.txt', 'zstestInput.txt', 'zstrainPCA.txt', 'zstestPCA.txt'],
        },
    }

    result = {}
    for step, info in pipeline_files.items():
        files_exist = all(os.path.isfile(os.path.join(DATA_DIR, f)) for f in info['files'])
        if 'extra_dir' in info:
            files_exist = files_exist and all(
                os.path.isfile(os.path.join(info['extra_dir'], f)) for f in info['extra_files']
            )
        result[step] = {'done': files_exist, 'label': info['label']}

    # 如果最终训练文件就绪，返回维度信息
    train_info = {}
    all_ready = result.get('zscore', {}).get('done', False) and result.get('pca', {}).get('done', False)
    if all_ready:
        try:
            train_x = np.loadtxt(os.path.join(DATA_DIR, 'zstrainInput.txt'))
            train_y = np.loadtxt(os.path.join(DATA_DIR, 'zstrainPCA.txt'))
            test_x = np.loadtxt(os.path.join(DATA_DIR, 'zstestInput.txt'))
            test_y = np.loadtxt(os.path.join(DATA_DIR, 'zstestPCA.txt'))
            train_info = {
                'trainSamples': int(train_x.shape[0]),
                'testSamples': int(test_x.shape[0]),
                'inputDim': int(train_x.shape[1]) if train_x.ndim > 1 else 1,
                'outputDim': int(train_y.shape[1]) if train_y.ndim > 1 else 1,
                'trainRatio': round(train_x.shape[0] / (train_x.shape[0] + test_x.shape[0]), 2),
            }
        except Exception:
            pass

    return jsonify({
        'pipeline': result,
        'ready': all_ready,
        'trainInfo': train_info,
    })


@data_bp.route('/execute', methods=['POST'])
def execute_processing():
    req_data = request.json
    p_type = req_data.get('type')
    
    try:
        import contextlib
        @contextlib.contextmanager
        def cd_preprocess():
            old_path = os.getcwd()
            os.chdir(os.path.join(BASE_DIR, 'core_algorithms', 'preprocess'))
            try:
                yield
            finally:
                os.chdir(old_path)

        with cd_preprocess():
            if p_type == 'split':
                from core_algorithms.preprocess.splitData import splitFiles
                splitFiles()
                return jsonify({"status": "success", "msg": "数据物理步长切分完成"})
            elif p_type == 'partition':
                from core_algorithms.preprocess.splitData import splitTrainTest, combineTrainTest
                splitTrainTest()
                combineTrainTest()
                return jsonify({"status": "success", "msg": "数据样本拓扑划分成功"})
            elif p_type == 'normalize':
                from core_algorithms.preprocess.splitData import indataNormalize
                indataNormalize()
                return jsonify({"status": "success", "msg": "归一化统计算子生成成功"})
            elif p_type == 'pca':
                from core_algorithms.preprocess.splitData import outdataNormalize
                outdataNormalize()
                return jsonify({"status": "success", "msg": "PCA 线性流形投影成功"})
        
        return jsonify({"status": "pending", "msg": f"Task {p_type} executed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
