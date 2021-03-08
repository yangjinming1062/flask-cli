# encoding:utf-8
import functools
import re
import subprocess
from collections import Iterable

from IPy import IP

from Utils.log_helper import *


def base_exceptions(flag_text=None, exception_return=None):
    """
    装饰器：异常捕获
    :param flag_text: [str]异常前的文本，标识是哪个请求出现异常，默认为None时使用方法名
    :param exception_return: [any]当发生异常时返回的内容，默认为None
    :return:[any]无异常则返回方法的返回值，异常返回exception_return
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except BaseException as ex:
                log_exception(f'{func.__name__ if flag_text is None else flag_text}异常:{ex}')
                return exception_return

        return wrapper

    return decorator
