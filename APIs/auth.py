# encoding:utf-8
from flask import Blueprint
from flask_jwt_extended import create_access_token

from Utils.api_helper import *

bp = Blueprint("auth", __name__)


@bp.route('/login', methods=['POST'])
@api_exceptions(need_data=True, data_requires=['method', 'account', 'password'], skip_jwt=True)
def login(**kwargs):
    """
    swagger_from_file: Swagger/auth/login.yml
    """
    data = kwargs['data']
    user = UserInfo.find(data['method'], data['account'])
    if not user:
        return response(ResponseEnum.NOT_FOUND_404)
    if user.check_password(data['password']):
        UserOperateLog(user_id=user.id, request_ip=request.remote_addr, request_api=request.path, request_data=data)
        user.update({'last_date': datetime.now()})
        return response(ResponseEnum.SUCCESS_201, value={"username": user.username, "access_token": create_access_token(identity=user.id)})
    else:
        return response(ResponseEnum.FORBIDDEN_403, message='密码错误，请检查后重新输入')
