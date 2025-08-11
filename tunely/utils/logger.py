import glob
import logging
import os
import sys
import time

from pathlib import Path
from logging.handlers import RotatingFileHandler

from colorlog import ColoredFormatter

from tunely.utils.constants import Constants
from tunely.utils.config import Config


class TimestampedRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        rollover_filename = f"{self.baseFilename}.{timestamp}"
        self.rotate(self.baseFilename, rollover_filename)
        self._cleanup_old_logs()
        self.mode = 'w'
        self.stream = self._open()

    def _cleanup_old_logs(self):
        log_files = sorted(
            glob.glob(f"{self.baseFilename}.*"),
            key=os.path.getmtime,
            reverse=True
        )
        for old_log in log_files[self.backupCount:]:
            try:
                os.remove(old_log)
            except OSError:
                pass


class Logger:
    _console_handler: logging.StreamHandler = None
    _file_handler: RotatingFileHandler = None
    _root_logger = logging.getLogger()

    @classmethod
    def _setup_handlers(cls, log_dir: str, log_file: str, max_bytes: int, backup_count: int, level: str,
                        log_format: str,
                        log_date_format: str):
        """
        Configures logging handlers for the application, including a console handler
        with colored log output and a file handler with timestamped rotating file
        behavior. Ensures the logging configuration is set up properly and existing
        handlers are cleared prior to setup.

        :param log_dir: Directory where the log files will be stored.
        :type log_dir: str
        :param log_file: Name of the log file.
        :type log_file: str
        :param max_bytes: Maximum size of the log file in bytes before rotation occurs.
        :type max_bytes: int
        :param backup_count: Number of backup log files to keep.
        :type backup_count: int
        :param level: Logging level as a string (e.g., "INFO", "DEBUG").
        :type level: str
        :param log_format: Log message format string.
        :type log_format: str
        :param log_date_format: Date format string for log messages.
        :type log_date_format: str
        :return: None
        """
        os.makedirs(log_dir, exist_ok=True)
        log_path = Path(log_dir, log_file).resolve()
        log_level = getattr(logging, level.upper(), logging.INFO)

        cls._console_handler = logging.StreamHandler(sys.stdout)
        cls._console_handler.setFormatter(ColoredFormatter(
            fmt="%(log_color)s" + log_format,
            datefmt=log_date_format,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red,bg_white',
            },
        ))
        cls._console_handler.setLevel(log_level)

        cls._file_handler = TimestampedRotatingFileHandler(
            log_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
        )
        cls._file_handler.setFormatter(logging.Formatter(
            fmt=log_format,
            datefmt=log_date_format
        ))
        cls._file_handler.setLevel(log_level)

        if cls._root_logger.handlers:
            cls._root_logger.handlers.clear()

        cls._root_logger.setLevel(log_level)
        cls._root_logger.addHandler(cls._console_handler)
        cls._root_logger.addHandler(cls._file_handler)

    @classmethod
    def init_default_logging(cls):
        """
        Initializes the default logging configuration for the class.

        This class method sets up the logging handlers with pre-defined
        default parameters determined by the class constants. It configures
        the logging directory, file, maximum file size, backup file count,
        log level, log format, and date format.

        :raise ValueError: If any of the constants used for initialization
            are invalid or incompatible with the logging setup.

        :return: None
        """
        cls._setup_handlers(
            Constants.DEFAULT_LOG_DIR,
            Constants.DEFAULT_LOG_FILE,
            Constants.DEFAULT_LOG_MAX_BYTES,
            Constants.DEFAULT_LOG_BACKUP_COUNT,
            Constants.DEFAULT_LOG_LEVEL,
            Constants.DEFAULT_LOG_FORMAT,
            Constants.DEFAULT_LOG_DATE_FORMAT
        )

    @classmethod
    def configure_from_settings(cls) -> None:
        """
        Configures the logging settings for the application using predefined values or defaults
        from the configuration file. This method reads necessary configurations like log directory,
        log file name, log rotation settings, log level, log format, and log date format. Once the
        configuration values are retrieved, it delegates to the `_setup_handlers` method to initialize
        the logging handlers with the appropriate settings.

        :raises ValueError: If any of the configuration values are invalid.
        """
        log_dir = Config.get('logging', 'log_dir', default=Constants.DEFAULT_LOG_DIR)
        log_file = Config.get('logging', 'log_file', default=Constants.DEFAULT_LOG_FILE)
        max_bytes = int(Config.get('logging', 'log_max_bytes', default=Constants.DEFAULT_LOG_MAX_BYTES))
        backup_count = int(
            Config.get('logging', 'log_backup_count', default=Constants.DEFAULT_LOG_BACKUP_COUNT))
        level = Config.get('logging', 'log_level', default=Constants.DEFAULT_LOG_LEVEL)
        log_format = Config.get('logging', 'log_format', default=Constants.DEFAULT_LOG_FORMAT)
        log_date_format = Config.get('logging', 'log_date_format', default=Constants.DEFAULT_LOG_DATE_FORMAT)

        cls._setup_handlers(log_dir, log_file, max_bytes, backup_count, level, log_format, log_date_format)

    @classmethod
    def set_log_level(cls, level: str) -> None:
        """
        Sets the logging level for the root logger and optional handlers. This allows
        for controlling the verbosity of the logging output based on the specified
        logging level.

        :param level: The string representation of the logging level to set. Accepted
            values are 'DEBUG', 'INFO', 'WARNING', 'ERROR', and 'CRITICAL'.
        :raises ValueError: If the provided level is not a valid logging level.
        :return: None
        """
        level = level.upper()
        valid_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        if level not in valid_levels:
            raise ValueError(f"Invalid log level: {level}")

        cls._root_logger.setLevel(valid_levels[level])
        if cls._console_handler:
            cls._console_handler.setLevel(valid_levels[level])
        if cls._file_handler:
            cls._file_handler.setLevel(valid_levels[level])

    @classmethod
    def debug(cls, message: str) -> None:
        """
        Logs a debug message using the root logger instance of the class.

        :param message: The debug message to be logged.
        :type message: str
        :return: None
        """
        cls._root_logger.debug(message)

    @classmethod
    def info(cls, message: str) -> None:
        """
        Logs an informational message using the root logger instance of the class.

        :param message: The informational message to be logged.
        :type message: str
        :return: None
        """
        cls._root_logger.info(message)

    @classmethod
    def warning(cls, message: str) -> None:
        """
        Logs a warning message using the root logger instance of the class.

        :param message: The warning message to be logged.
        :type message: str
        :return: None
        """
        cls._root_logger.warning(message)

    @classmethod
    def error(cls, message: str) -> None:
        """
        Logs an error message using the root logger instance of the class.

        :param message: The error message to be logged.
        :type message: str
        :return: None
        """
        cls._root_logger.error(message)

    @classmethod
    def critical(cls, message: str) -> None:
        """
        Logs a critical message using the root logger instance of the class.

        :param message: The critical message to be logged.
        :type message: str
        :return: None
        """
        cls._root_logger.critical(message)
