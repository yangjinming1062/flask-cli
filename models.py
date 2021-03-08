# encoding:utf-8
import time
import uuid
from collections import Iterable
from datetime import datetime
from functools import reduce

from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from sqlalchemy import and_, or_
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import generate_password_hash, check_password_hash
import Utils.database as RedisDatabase
import config

from Enums import *

scheduler = APScheduler()  # 定时任务
db = SQLAlchemy()  # 数据库连接

app_boot_time = datetime.fromtimestamp(0)

property_dict = {}  # dynamic_modify的字典，Key为赋值的属性的名称，Value为该属性对应的数据库映射类的名称


def dynamic_modify(obj, data):
    """
    实现动态的数据库模型赋值
    """
    for k, v in data.items():
        if k == 'update_date':
            if isinstance(v, int):
                real_value = datetime.fromtimestamp(v)
                data[k] = real_value

    for k, v in data.items():
        if type(v) == list:
            eval(f'obj.{k}.clear()')
            for vv in v:
                if type(vv) == str:
                    tmp = eval(f'{property_dict[k]}.find_by_id(vv)')
                    if tmp:
                        eval(f'obj.{k}.append(tmp)')
                elif type(vv) == dict:
                    sub_obj = dynamic_modify(eval(f'{property_dict[k]}()'), vv)
                    eval(f'obj.{k}.append(sub_obj)')
        elif type(v) == dict:
            old_attr = getattr(obj, k)
            if old_attr is None:
                old_attr = eval(f'{property_dict[k]}()')
            sub_obj = dynamic_modify(old_attr, v)
            setattr(obj, k, sub_obj)
        else:
            setattr(obj, k, v)
    return obj


def common_dump(obj, dump_fields=[]):
    """
    通用序列化方法：将DB类序列化
    :param obj:[any]
    :param exclude:[dict]
    :return:[any]
    """
    result = None
    if obj is not None:
        if isinstance(obj, Iterable):
            result = [common_dump(item, dump_fields) for item in obj]
        else:
            result = {}
            for field in dump_fields:
                if type(field) == dict:
                    for k, v in field.items():
                        result[k] = common_dump(getattr(obj, k, None), v)
                else:
                    field_value = getattr(obj, field, None)
                    result[field] = field_value
                    if isinstance(field_value, datetime):  # 主要是为了Redis保存，无法保存datetime类型，如果不考虑Redis无需转换成字符串
                        result[field] = field_value.strftime("%Y-%m-%d %H:%M:%S")

    return result


class ModelMixin(object):
    id = db.Column(db.String(32), primary_key=True, default=lambda: uuid.uuid4().hex)  # 主键
    update_date = db.Column(db.DateTime, server_default=db.func.now())

    def create(self):
        db.session.add(self)
        db.session.commit()
        if self.__class__.__name__ == 'UserOperateLog':
            # 记录日志信息，该信息不同步到redis
            pass
        else:
            if config.REDIS_SERVER_ENABLED:
                # 同步到redis
                RedisDatabase.redis_update(self)
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self, data, direct_commit=True):
        data['update_date'] = datetime.now()
        dynamic_modify(self, data)
        if direct_commit:
            db.session.commit()

    @classmethod
    def find_by_id(cls, query_id):
        if isinstance(query_id, list):
            return cls.query.filter(cls.id.in_(query_id)).all()
        else:
            return cls.query.filter_by(id=query_id).first()

    def dump(self):
        pass


class UserInfo(db.Model, ModelMixin):
    """
    数据库映射类：用户信息
    """

    email = db.Column(db.String(40), nullable=True, unique=True)  # 账号绑定的邮箱
    phone = db.Column(db.String(15), nullable=True, unique=True)  # 账号绑定的手机
    account = db.Column(db.String(20), unique=True)  # 账号对应的人员工号
    username = db.Column(db.String(40), nullable=False, unique=True)  # 用户名
    password = db.Column(db.String(120), nullable=False)  # 密码：加密存储在数据库中
    last_date = db.Column(db.DateTime, server_default=db.func.now())  # 最后一次访问时间
    created_date = db.Column(db.DateTime, server_default=db.func.now())  # 账号创建时间
    valid = db.Column(db.Boolean, default=True)  # 账号有效性
    admin = db.Column(db.Boolean, default=False)  # 是否是管理员
    logs = db.relationship("UserOperateLog", backref=db.backref("user"), cascade="all, delete-orphan")

    def dump(self):
        return common_dump(self, dump_fields=['id', 'update_date', 'created_date', 'email', 'phone', 'account', 'username', 'valid'])

    @classmethod
    def find(cls, query_key, query_key):
        return eval(f'cls.query.filter_by({query_key}={query_key}).first()')

    @staticmethod
    def generate_hash(raw_password):
        return generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password) or self.password == raw_password


class UserOperateLog(db.Model, ModelMixin):
    """
    数据库映射类：用户操作日志记录
    """

    __tablename__ = 'user_logs'
    user_id = db.Column(db.String(32), db.ForeignKey('users.id'))  # 用户ID
    request_ip = db.Column(db.String(15))  # 请求源地址
    request_api = db.Column(db.String(100))  # 请求操作的API
    request_data = db.Column(JSON)  # 请求参数
    request_date = db.Column(db.DateTime, server_default=db.func.now())  # 请求日期

    def dump(self):
        return common_dump(self, dump_fields=['id', 'update_date', 'user_id', 'request_ip', 'request_api', 'request_data', 'request_date'])

    @classmethod
    def filter_by_date_and_user(cls, begin_time, end_time, user_id):
        args = True if begin_time is None or end_time is None else and_(begin_time < cls.request_date, cls.request_date < end_time)
        if user_id is not None:
            args = and_(args, cls.user_id == user_id)
        return db.session.query(cls).filter(args).all()


class Demo(db.Model, ModelMixin):
    name = db.Column(db.String(50))
