# encoding:utf-8
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from Enums.PlatformStateKey import PlatformStateKeyEnum
from app import create_app
from models import *

app = create_app()
db.init_app(app)
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)

"""
执行数据库迁移操作，迁移命令如下
#1.初始化迁移文件
# python manager.py db init
#2.将模型添加到迁移文件
# python manager.py db migrate
#3.迁移文件中的模型映射到数据库中
# python manager.py db upgrade
#4.添加必要数据
# python manager.py init_sys
#5.添加ELK服务器信息
# python manager.py add_es -h {ip_address} -p {port}
"""


@manager.command
def init_sys():
    """
    初始化数据库状态表中的数据（完成数据库初始化后）
    :return:
    """

    if not UserInfo.find_by_username('admin'):
        admin_user = UserInfo(username='admin', account='001', admin=True)
        admin_user.password = UserInfo.generate_hash('admin123')
        db.session.add(admin_user)

    db.session.commit()
    print('init_sys Success')


@manager.option('-h', '--host', dest='host')
@manager.option('-p', '--port', dest='port')
def add_es(host, port):
    """
    添加一些需要参数的数据（完成数据库初始化后）
    :return:
    """
    print('Success')


if __name__ == '__main__':
    manager.run()
