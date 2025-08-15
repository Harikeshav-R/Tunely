from pathlib import Path
from platformdirs import user_data_dir, user_log_dir, user_config_dir


class Constants:
    CONFIG_PATH = Path(user_config_dir("Tunely", "Tunely"), "config.db").resolve()
    DATABASE_PATH = Path(user_data_dir("Tunely", "Tunely"), "tunely.db").resolve()
    LOG_FILE_PATH = Path(user_log_dir("Tunely", "Tunely"), "tunely.log").resolve()
