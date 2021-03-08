# encoding:utf-8
from flask import Blueprint

from Utils.api_helper import *
from Utils.log_helper import *
from Utils.utils import time_parser

bp = Blueprint("user", __name__)


@bp.route('/register', methods=['POST'])
@api_exceptions(need_data=True, data_requires=['account', 'username', 'password'], skip_jwt=True)
def user_register(**kwargs):
    """
    swagger_from_file: Swagger/user/register.yml
    """
    data = kwargs['data']
    data['password'] = UserInfo.generate_hash(data['password'])
    try:
        obj = dynamic_modify(UserInfo(), data).create()
    except Exception as e:
        return response(ResponseEnum.INVALID_FIELD_VALUE_422, message=f'{e}')
    return response(ResponseEnum.SUCCESS_201, value=obj.dump())


@bp.route('/userinfo', methods=['GET'])
@api_exceptions(need_user=True)
def userinfo(**kwargs):
    """
    swagger_from_file: Swagger/user/userinfo.yml
    """
    return response(ResponseEnum.SUCCESS_200, value=kwargs['user'].dump())
