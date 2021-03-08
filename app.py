# encoding:utf-8
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify
from flask_cors import CORS  # 解决前后端联调的跨域问题
from flask_jwt_extended import JWTManager  # 登录认证，JWT解决方案
from flask_swagger import swagger  # 生成API文档
from flask_swagger_ui import get_swaggerui_blueprint

import config
from APIs import *
from Enums import ResponseEnum
from Utils.api_helper import response
from Utils.log_helper import *
from crontab import rsync_elk, start_crontab_task
from models import *
import Utils.database as RedisDatabase

jwt = JWTManager()
cors = CORS()


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    register_plugins(app)  # 注册插件
    register_blueprints(app)  # 注册蓝图
    register_logging(app)  # 注册日志处理器
    register_errors(app)  # 注册错误处理函数

    app.logger.info('Flask-Cli-API开启')
    return app


def register_logging(app):
    app.logger.name = 'Flask-Cli'
    log_level = app.config.get("LOG_LEVEL", logging.INFO)
    if app.config['LOG_TO_STDOUT']:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        app.logger.addHandler(stream_handler)
    else:
        file_handler = RotatingFileHandler(os.path.join(log_dir, 'api.log'), maxBytes=1024 * 1024 * 50, backupCount=5, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(log_level)
        app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)


def register_plugins(app):
    jwt.init_app(app)

    cors.init_app(app, supports_credentials=True)

    db.init_app(app)


def register_blueprints(app):
    app.register_blueprint(authbp, url_prefix='/api/auth')
    app.register_blueprint(baseinfobp, url_prefix='/api/demo')
    app.register_blueprint(userbp, url_prefix='/api/user')

    @app.route("/api/swagger")
    def spec():
        swag = swagger(app, prefix='/api', from_file_keyword="swagger_from_file")
        swag['info']['base'] = "http://locahost/api"
        swag['info']['version'] = "1.0"
        swag['info']['title'] = 'API Docs'
        return jsonify(swag)

    swaggerbp = get_swaggerui_blueprint('/api/docs', '/api/swagger', config={'app_name': 'API Docs'})
    app.register_blueprint(swaggerbp, url_prefix='/api/docs')


def register_errors(app):
    @app.after_request
    def add_header(response_content):
        return response_content

    @app.errorhandler(400)
    def bad_request(e):
        log_error(e)
        return response(ResponseEnum.BAD_REQUEST_400)

    @app.errorhandler(404)
    def not_found(e):
        log_error(e)
        return response(ResponseEnum.REQUEST_404)

    @app.errorhandler(500)
    def server_error(e):
        log_error(e)
        return response(ResponseEnum.SERVER_ERROR_500)

    @jwt.expired_token_loader
    def expired_token_callback():
        return response(ResponseEnum.UNAUTHORIZED_401, message='认证过期，请重新认证')

    @jwt.invalid_token_loader
    def invalid_token_callback(error):  # we have to keep the argument here, since it's passed in by the caller internally
        return response(ResponseEnum.UNAUTHORIZED_401, message='认证失效，请重新获取')


def init_crontab(app):
    scheduler.init_app(app)
    scheduler.add_job(id='__start__', func=start_crontab_task, trigger='interval', seconds=10, args=[app, scheduler])
    scheduler.start()

    global app_boot_time
    app_boot_time = datetime.now()


def init_redis(app):
    # 拷贝mysql初始数据至redis（redis初始化）
    # 需要先进行一次请求才能执行下面代码
    @app.before_first_request  # 只执行一次
    def init_db():
        try:
            RedisDatabase.redis_init(AccountGroup)
            RedisDatabase.redis_init(FileDict)
            RedisDatabase.redis_init(BusinessDict)
        except:
            print("与redis建立链接异常")
            config.REDIS_SERVER_ENABLED = False


app = create_app()
# init_crontab(app)  # 定时任务功能按需使用
if config.REDIS_SERVER_ENABLED:
    init_redis(app)

if __name__ == '__main__':  # Debug时使用该方法
    app.run(host="0.0.0.0", port=5001, debug=True)
