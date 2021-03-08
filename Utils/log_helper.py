# encoding:utf-8
import datetime
import logging
import os
from logging.handlers import BaseRotatingHandler

"""
提供日志记录功能
"""

basedir = os.getcwd()
log_dir = os.path.join(basedir, 'Logs')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)


class DayRotatingHandler(BaseRotatingHandler):
    """
    日志按天分割
    """

    def __init__(self, log_type, mode, encoding=None, delay=False):
        log_type_dir = os.path.join(log_dir, log_type)
        if not os.path.exists(log_type_dir):
            os.mkdir(log_type_dir)
        self.date = datetime.date.today()
        self.suffix = "%Y-%m-%d.log"
        filename = os.path.join(log_type_dir, self.date.strftime(self.suffix))
        super(BaseRotatingHandler, self).__init__(filename, mode, encoding, delay)

    def shouldRollover(self, record):
        return self.date != datetime.date.today()

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None
        new_log_file = os.path.join(os.path.split(self.baseFilename)[0], datetime.date.today().strftime(self.suffix))
        self.baseFilename = f"{new_log_file}"
        self._open()


# ----定义日志的配置----#
cls_handler = logging.StreamHandler()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(filename)s[%(lineno)d] %(funcName)s(): %(message)s", datefmt="%Y/%m/%d %H:%M:%S", handlers=[cls_handler])
# ----结束定义日志配置----#

# ----主动信息记录，创建全局日志记录程序----#
_InfoLogger = logging.getLogger("Info日志")
_InfoLogger.addHandler(DayRotatingHandler('Info', mode="a", encoding="utf-8"))

_WarnLogger = logging.getLogger("Warn日志")
_WarnLogger.addHandler(DayRotatingHandler('Warn', mode="a", encoding="utf-8"))

_ErrorLogger = logging.getLogger("Error日志")
_ErrorLogger.addHandler(DayRotatingHandler('Error', mode="a", encoding="utf-8"))

_ExceptionLogger = logging.getLogger("Exception日志")
_ExceptionLogger.addHandler(DayRotatingHandler('Exception', mode="a", encoding="utf-8"))
# ----结束创建全局日志记录程序----#


def log_info(msg):
    """
    记录Info级日志
    :param msg:[any]日志内容
    :return:[None]
    """
    _InfoLogger.info(msg)


def log_warn(msg):
    """
    记录Warning级日志
    :param msg:[any]日志内容
    :return:[None]
    """
    _WarnLogger.warning(msg)


def log_error(msg):
    """
    记录Error级日志
    :param msg:[any]日志内容
    :return:[None]
    """
    _ErrorLogger.error(msg)


def log_exception(msg):
    """
    记录Exception级日志
    :param msg:[any]日志内容
    :return:[None]
    """
    _ExceptionLogger.exception(msg)
