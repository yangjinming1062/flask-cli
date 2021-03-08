# encoding:utf-8
import functools
import json

from flask import make_response, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from Enums import *
from Utils.log_helper import *
from Utils.processer import Processor
from Utils.utils import base_exceptions, filtered_next
from models import *
import Utils.database as RedisDatabase


def response(base_response, value=None, message=None, error=None, headers={}, pagination=None):
    """
    API响应方法
    :param base_response: [ResponseEnum]基础响应信息
    :param value: [dict]响应内容，默认为None
    :param message: [str]响应消息，默认为None
    :param error: [str]错误消息，默认为None
    :param headers: [dict]响应头
    :param pagination: [dict]分页信息
    :return:[any]
    """
    base_response = base_response.value
    result = {'code': base_response['code']}

    if value is not None:
        result.update({'content': value})

    if message is not None:  # 优先使用输入的消息
        result.update({'msg': message})
    elif base_response.get('message', None) is not None:  # 其次使用默认的消息（如果有）
        result.update({'msg': base_response['message']})

    if error is not None:
        result.update({'errors': error})

    if pagination is not None:
        result.update({'pagination': pagination})

    headers.update({'Access-Control-Allow-Origin': '*', 'server': 'WhiteEnv Service'})
    return make_response(jsonify(result), base_response['http_code'], headers)


def api_exceptions(need_uid=False, need_manager=False, need_admin=False, need_user=False, need_data=False, data_requires=[], log_enable=True, skip_jwt=False):
    """
    装饰器：处理API响应异常以及必要参数的校验
    :return:[any/SERVER_EXCEPTION_500]无异常则返回方法的返回值，异常返回SERVER_EXCEPTION_500
    """

    def decorator(func):
        @jwt_required(optional=skip_jwt)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                data = None
                uid = get_jwt_identity()
                if uid and log_enable:  # 需要认证信息的接口通过认证信息获取用户信息
                    try:
                        UserOperateLog(user_id=uid, request_ip=request.remote_addr, request_api=request.path, request_data=data).create()
                    except BaseException as e:
                        log_warn(f'记录操作日志异常：{uid}|{request.remote_addr}|{request.path}|{data}')
                if need_uid or need_admin or need_user or need_manager:
                    if not uid:
                        return response(ResponseEnum.BAD_REQUEST_400)
                    kwargs['uid'] = uid
                if need_admin or need_user or need_manager:
                    user = UserInfo.find_by_id(uid)
                    if not user:
                        return response(ResponseEnum.NOT_FOUND_404, message='用户不存在')
                    if need_admin and not user.admin:
                        return response(ResponseEnum.FORBIDDEN_403)
                    if need_manager and not (user.admin or user.manager):
                        return response(ResponseEnum.FORBIDDEN_403)
                    kwargs['user'] = user
                if need_data:
                    # data = request.get_json()
                    data = request.get_data(as_text=True)
                    data = json.loads(data)
                    if data is None:
                        return response(ResponseEnum.INVALID_INPUT_422)
                    if 'id' in data:  # 防止恶意修改资源ID，如果在请求数据中检测到id直接剔除
                        return response(ResponseEnum.INVALID_INPUT_422, message='不允许输入id进行修改')  # 恶意请求就不想处理了
                    for r in data_requires:
                        if r not in data:
                            return response(ResponseEnum.MISSING_PARAMETERS_422, message=f'缺失{r}')
                    kwargs['data'] = data
                return func(*args, **kwargs)
            except Exception as ex:
                if str(ex).find('Signature') > -1:
                    return response(ResponseEnum.UNAUTHORIZED_401, message=f'{ex}')
                log_exception(f'{func.__module__}|{func.__name__}异常:{ex}')
                return response(ResponseEnum.SERVER_EXCEPTION_500, message=f'{ex}')

        return wrapper

    return decorator


def quickly_add(cls, data):
    """
    快捷添加数据
    """
    try:
        obj = dynamic_modify(cls(), data).create()
    except Exception as e:
        return response(ResponseEnum.INVALID_FIELD_VALUE_422, message=f'{e}')
    return response(ResponseEnum.SUCCESS_201, value=obj.id)


def quickly_del(cls, id):
    """
    数据快捷删除
    """
    obj = cls.find_by_id(id)
    if not obj:
        return response(ResponseEnum.NOT_FOUND_404)
    obj.delete()
    return response(ResponseEnum.SUCCESS_200)


def quickly_mod(cls, id, data):
    """
    数据的快捷修改
    """
    obj = cls.find_by_id(id)
    if not obj:
        return response(ResponseEnum.NOT_FOUND_404)
    obj.update(data)
    return response(ResponseEnum.SUCCESS_200)


def quickly_query(cls, id):
    """
    数据信息快捷查询
    """
    obj = cls.find_by_id(id)
    if not obj:
        return response(ResponseEnum.NOT_FOUND_404)
    return response(ResponseEnum.SUCCESS_200, value=obj.dump())


def quickly_list(cls):
    """
    快捷查询返回数据列表
    """
    if config.REDIS_SERVER_ENABLED:
        data_list_result = RedisDatabase.baseinfo_search(cls)
        if data_list_result:
            # redis数据库有，从redis数据库查询
            return data_list(data_list_result)
        else:
            # redis数据库有，从mysql数据库查询
            return data_list([obj.dump() for obj in cls.query.all()])
    else:
        # redis数据库未开启，从mysql数据库查询
        return data_list([obj.dump() for obj in cls.query.all()])


def data_list(data):
    """
    与simple_list规则相同，但是直接提供全部数据
    :param data:[list]全部数据
    :return:web响应
    """
    page = int(request.args.get('page', 0))
    limit = int(request.args.get('limit', 10))
    order_key = request.args.get('order_by', None)
    order_direction = request.args.get('order', 'asc')
    filter_by = request.args.get('filter_by', None)
    filter_value = request.args.get('filter', None)
    is_fuzzy = request.args.get('fuzzy', None) == 'true'
    if order_key:
        data.sort(key=lambda d: d.get(order_key, 0), reverse=order_direction != 'asc')
    if filter_by and filter_value:
        if is_fuzzy:
            tmp = filter(lambda d: str(getattr(d, filter_by, None)).find(filter_value) > -1, data)
        else:
            tmp = filter(lambda d: getattr(d, filter_by, None) == filter_value, data)
        data = list(tmp)
    if page > 0:
        pagination = {'page': page, 'limit': limit, 'total': len(data)}
        res = data[(page - 1) * limit:page * limit]
        return response(ResponseEnum.SUCCESS_200, value=res, pagination=pagination)
    else:
        return response(ResponseEnum.SUCCESS_200, value=data)
