# encoding:utf-8
from flask import Blueprint

from Utils.api_helper import *

bp = Blueprint("demo", __name__)  # Demo


@bp.route('/add', methods=['POST'])
@api_exceptions(need_admin=True, need_data=True, data_requires=['name'])
def demo_add(**kwargs):
    """
    swagger_from_file: Swagger/demo/add.yml
    """
    return quickly_add(Demo, kwargs['data'])


@bp.route('/<id>/delete', methods=['DELETE'])
@api_exceptions(need_admin=True)
def demo_delete(id, **kwargs):
    """
    swagger_from_file: Swagger/demo/del.yml
    """
    return quickly_del(Demo, id)


@bp.route('/list', methods=['GET'])
@api_exceptions()
def demo_list(**kwargs):
    """
    swagger_from_file: Swagger/demo/list.yml
    """
    return quickly_list(Demo)


@bp.route('/<id>/modify', methods=['PUT'])
@api_exceptions(need_admin=True, need_data=True)
def demo_modify(id, **kwargs):
    """
    swagger_from_file: Swagger/demo/mod.yml
    """
    return quickly_mod(Demo, id, kwargs['data'])
