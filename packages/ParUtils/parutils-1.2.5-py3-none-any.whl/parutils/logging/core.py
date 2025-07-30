from functools import wraps

from . import g
from .logger import Logger


def get_logger() -> Logger:

    if g.logger is None:
        logger = Logger(file_write=False)
        g.logger = logger
    else:
        logger = g.logger
    return logger


def set_logger(logger):

    g.logger = logger


def close_logger():

    if g.logger:
        return g.logger.close()


def logger_methode(func):

    @wraps(func)
    def new(*args, **kwargs):
        logger = get_logger()
        logger_methode = getattr(logger, func.__name__)
        return logger_methode(*args, **kwargs)

    return new


def get_logs():
    return get_logger().logs


def update_logs(logs):
    from parutils.file import save_list

    logger = get_logger()
    logger.logs = logs
    save_list(logs + [''], logger.log_path)
