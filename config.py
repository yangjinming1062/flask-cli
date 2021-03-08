# encoding:utf-8
import redis
import logging
import random

SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://username:password@db_host:3306/app_schema'
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 动态追踪修改设置
REDIS_CONNECTION_POOL = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
REDIS_SERVER_ENABLED = True  # 是否启用redis
# JWT_SECRET_KEY = secrets.token_hex(16)  # 正式用的时候使用随机字符串进行加密
JWT_SECRET_KEY = 'App-Debug'  # JWT token密钥
JWT_COOKIE_CSRF_PROTECT = True
JWT_CSRF_CHECK_FORM = True
JWT_ACCESS_TOKEN_EXPIRES = 86400 * 30
LOG_LEVEL = logging.INFO
LOG_TO_STDOUT = True
JSON_AS_ASCII = False
SCHEDULER_API_ENABLED = True
