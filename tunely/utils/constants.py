from pathlib import Path

from appdirs import user_config_dir, user_cache_dir, user_data_dir

APP_NAME = "Tunely"
APP_AUTHOR = "Harikeshav R"

DEFAULT_LOG_DIR = Path(user_cache_dir(APP_NAME, APP_AUTHOR), "logs").resolve()
DEFAULT_LOG_FILE = "tunely.log"
DEFAULT_MAX_BYTES = 10_000_000
DEFAULT_BACKUP_COUNT = 5
DEFAULT_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR)).resolve()
DEFAULT_CONFIG_FILE = 'config.ini'

DEFAULT_DATABASE_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR), 'databases').resolve()
DEFAULT_DATABASE_FILE = 'tunely.db'
