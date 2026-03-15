from flask import Flask
from flask_cors import CORS
import os

# 导入各模块蓝图
from api.user import user_bp
from api.data import data_bp
from api.model import model_bp
from api.predict import predict_bp
from api.dataset import dataset_bp

def create_app():
    app = Flask(__name__)
    CORS(app) # 允许跨域

    # 注册路由蓝图
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(model_bp, url_prefix='/api/model')
    app.register_blueprint(predict_bp, url_prefix='/api/predict')
    app.register_blueprint(dataset_bp, url_prefix='/api/dataset')

    @app.route('/')
    def index():
        return "Transformer Physical Field Platform API Service"

    return app

if __name__ == '__main__':
    app = create_app()
    print("Transformer Backend Service Running on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
