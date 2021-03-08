import redis
import config
from models import *
import datetime
import json

if config.REDIS_SERVER_ENABLED:
    REDIS_CONNECTION_POOL = config.REDIS_CONNECTION_POOL
    redis_db = redis.Redis(connection_pool=REDIS_CONNECTION_POOL)


def change_name(str):
    """
    将驼峰式命名转换为下划线式命名

    :param str: 驼峰命名字符串
    :return: 下划线命名字符串
    """
    lst = []
    for index, char in enumerate(str):
        if char.isupper() and index != 0:
            lst.append("_")
        lst.append(char)

    return "".join(lst).lower()


def redis_init(models):
    """
    redis数据库初始化

    :param models: 传入models类、如FileDic
    :return: 无返回值
    """
    # 初始化models,由mysql数据库进行同步
    name = models.__name__
    # 如果mysql表中第一列非id可启用下面column
    # try:
    #     first_column = models.column[0]
    # except:
    #     first_column = 'id'  # 默认为id
    # 默认第一列为id
    first_column = 'id'  # 默认为id
    file_dict_obj = models.query.all()

    for obj in file_dict_obj:
        obj_dic = obj.dump()
        obj_str = json.dumps(obj_dic)
        primary_key = obj_dic.get(first_column)
        redis_key = name+":"+primary_key
        redis_db.set(redis_key,obj_str)
        # for column_name, value in obj_dic.items():
        #     redis_key = name+':'+primary_key+':'+column_name
        #     if value is None:
        #         value = ''
        #     if type(value) is datetime.datetime:
        #         value = value.strftime("%Y-%m-%d %H:%M:%S")
        #         # print(1)
        #     redis_db.set(redis_key,value)


def baseinfo_search(models):
    """
    baseinfo查询

    :param models: 传入models类、如FileDic
    :return: [list] 查询结果，适配api_helper的data_list
    """
    # 1千条数据的情况下查询约0.4s
    # name = models.__name__
    # pattern = name+'*'
    # list = []
    # for key in redis_db.keys(pattern):
    #     value_str = redis_db.get(key)
    #     value_dic = json.loads(value_str)
    #     list.append(value_dic)
    # return list

    # 优化
    # 1千条数据的情况下查询约0.008s
    name = models.__name__
    pattern = name+'*'
    keys_list = redis_db.keys(pattern)
    data_list = redis_db.mget(keys_list)
    list = [json.loads(data) for data in data_list]
    return list


def redis_update(models):
    """
    redis数据库更新

    :param models:
    :return:
    """
    # 当有一条create数据commit到mysql的同时，同步到redis
    name = models.__class__.__name__
    data = models.dump()
    # 如果mysql表中第一列非id可启用下面column
    # try:
    #     primary_key = models.column[0]
    # except:
    #     primary_key = 'id'  # 默认为id
    # 默认第一列为id
    primary_key = 'id'  # 默认为id

    redis_key = name+':'+data.get(primary_key)
    redis_value = json.dumps(data)
    redis_db.set(redis_key, redis_value)