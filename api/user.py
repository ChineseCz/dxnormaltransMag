from flask import Blueprint, request, jsonify

user_bp = Blueprint('user', __name__)

@user_bp.route('/list', methods=['GET'])
def get_users():
    # 模拟用户列表
    users = [
        {"id": 1, "username": "admin", "role": "管理员", "dept": "技术部"},
        {"id": 2, "username": "user1", "role": "工程师", "dept": "研发部"}
    ]
    return jsonify(users)

@user_bp.route('/roles', methods=['GET'])
def get_roles():
    roles = ["超级管理员", "普工管理员", "普通用户"]
    return jsonify(roles)

