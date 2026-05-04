from flask import Flask
from flask_cors import CORS
import os

# 导入各模块蓝图
from api.user import user_bp
from api.data import data_bp
from api.model import model_bp
from api.predict import predict_bp
from api.dataset import dataset_bp
from api.gaoya import gaoya_bp
from api.reactor import reactor_bp
from api.transfield import transfield_bp
from api.ai import ai_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(user_bp,      url_prefix='/api/user')
    app.register_blueprint(data_bp,      url_prefix='/api/data')
    app.register_blueprint(model_bp,     url_prefix='/api/model')
    app.register_blueprint(predict_bp,   url_prefix='/api/predict')
    app.register_blueprint(dataset_bp,   url_prefix='/api/dataset')
    app.register_blueprint(gaoya_bp,     url_prefix='/api/gaoya')
    app.register_blueprint(reactor_bp,   url_prefix='/api/reactor')
    app.register_blueprint(transfield_bp, url_prefix='/api/transfield')
    app.register_blueprint(ai_bp,        url_prefix='/api/ai')

    @app.route('/')
    def index():
        return "Transformer Physical Field Platform API Service"

    return app

# 模块级实例 —— waitress 用 "server:app" 启动时需要
app = create_app()

if __name__ == '__main__':
    app = create_app()
    print("Transformer Backend Service Running on http://127.0.0.1:5000")
    # debug=False + threaded=True 才能承受并发压测
    # 生产/压测建议改用: waitress-serve --host=0.0.0.0 --port=5000 "server:create_app()"
    app.run(debug=False, threaded=True, host='0.0.0.0', port=5000)
