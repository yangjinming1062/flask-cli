# encoding:utf-8
from enum import Enum


class ResponseEnum(Enum):
    """
    统一接口响应枚举，统一接口的返回信息（响应）格式
    """
    SUCCESS_200 = {'http_code': 200, 'code': 'Success', "message": "请求成功"}

    SUCCESS_201 = {'http_code': 201, 'code': 'Success', "message": "创建成功"}

    BAD_REQUEST_400 = {"http_code": 400, "code": "Bad Request", "message": "请求无效"}

    UNAUTHORIZED_401 = {"http_code": 401, "code": "Unauthorized", "message": "认证失效"}

    FORBIDDEN_403 = {"http_code": 403, "code": "Not Authorized", "message": "未授权进行该操作"}

    REQUEST_404 = {"http_code": 404, "code": "Not Found", "message": "API地址错误，请检查请求地址"}

    NOT_FOUND_404 = {"http_code": 404, "code": "Not Found", "message": "未找到对应资源"}

    INVALID_INPUT_422 = {"http_code": 422, "code": "Invalid Input", "message": "无效输入"}

    MISSING_PARAMETERS_422 = {"http_code": 422, "code": "Missing Parameter"}

    INVALID_FIELD_VALUE_422 = {"http_code": 422, "code": "Invalid Field Value", "message": "参数赋值范围出错"}

    SERVER_ERROR_500 = {"http_code": 500, "code": "Server Error", "message": "服务端响应失败"}

    SERVER_EXCEPTION_500 = {"http_code": 500, "code": "Server Exception"}
