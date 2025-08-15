import inspect
import logging

from logging.handlers import RotatingFileHandler

from tunely.utils.constants import Constants


class Logger:
    _logger = None
    _log_file = Constants.LOG_FILE_PATH
    _max_bytes = 10 * 1024 * 1024  # 10 MB
    _backup_count = 5
    _log_level = logging.DEBUG
    _formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    @staticmethod
    def _initialize():
        if Logger._logger is not None:
            return

        Logger._logger = logging.getLogger("PackageLogger")
        Logger._logger.setLevel(Logger._log_level)
        Logger._logger.propagate = False

        Logger._log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=Logger._log_file,
            maxBytes=Logger._max_bytes,
            backupCount=Logger._backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(Logger._formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(Logger._formatter)

        Logger._logger.addHandler(file_handler)
        Logger._logger.addHandler(console_handler)

        root_logger = logging.getLogger()
        root_logger.setLevel(Logger._log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    @staticmethod
    def get_logger():
        Logger._initialize()
        return Logger._logger

    @staticmethod
    def _log(level, msg, *args, **kwargs):
        frame = inspect.currentframe()

        caller_frame = frame.f_back.f_back
        extra = {
            "module": caller_frame.f_globals.get("__name__", ""),
            "funcName": caller_frame.f_code.co_name
        }
        Logger.get_logger().log(level, msg, *args, extra=extra, **kwargs)

    @staticmethod
    def debug(msg, *args, **kwargs):
        Logger._log(logging.DEBUG, msg, *args, **kwargs)

    @staticmethod
    def info(msg, *args, **kwargs):
        Logger._log(logging.INFO, msg, *args, **kwargs)

    @staticmethod
    def warning(msg, *args, **kwargs):
        Logger._log(logging.WARNING, msg, *args, **kwargs)

    @staticmethod
    def error(msg, *args, **kwargs):
        Logger._log(logging.ERROR, msg, *args, **kwargs)

    @staticmethod
    def critical(msg, *args, **kwargs):
        Logger._log(logging.CRITICAL, msg, *args, **kwargs)
