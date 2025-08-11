import configparser
import logging
import os
import shutil

from datetime import datetime
from pathlib import Path
from typing import Any

from tunely.utils.constants import Constants

_logger = logging.getLogger(__name__)


class Config:
    _config = configparser.ConfigParser()
    _config_file_path = Constants.CONFIG_DEFAULT_CONFIG_FILE

    os.makedirs(Constants.CONFIG_DEFAULT_CONFIG_DIR, exist_ok=True)

    @classmethod
    def _generate_default_settings(cls) -> None:
        """
        Generates and configures the default settings for the system.

        This method initializes default configurations for various components
        like database and logging and stores them into a configuration dictionary
        accessible throughout the system.

        :raises RuntimeError: If the configuration dictionary or logging constants
            are not defined or inaccessible.
        """
        _logger.info("Generating default settings")

        cls._config['database'] = {
            'db_file': Constants.CONFIG_DEFAULT_DATABASE_FILE,
        }
        cls._config['logging'] = {
            'log_dir': Constants.CONFIG_DEFAULT_LOG_DIR,
            'log_file': Constants.CONFIG_DEFAULT_LOG_FILE,
            'log_level': Constants.CONFIG_DEFAULT_LOG_LEVEL,
            'log_max_bytes': Constants.CONFIG_DEFAULT_LOG_MAX_BYTES,
            'log_backup_count': Constants.CONFIG_DEFAULT_LOG_BACKUP_COUNT,
            'log_format': Constants.CONFIG_DEFAULT_LOG_FORMAT,
            'log_date_format': Constants.CONFIG_DEFAULT_LOG_DATE_FORMAT,
        }
        cls._config['downloader'] = {
            'login_retry_attempts': Constants.CONFIG_DOWNLOADER_LOGIN_RETRY_ATTEMPTS,
            'language': Constants.CONFIG_DOWNLOADER_LANGUAGE,
            'output_format': Constants.CONFIG_DOWNLOADER_OUTPUT_FORMAT,
            'output_dir': Constants.CONFIG_DOWNLOADER_OUTPUT_DIR,
            'download_lyrics': Constants.CONFIG_DOWNLOADER_DOWNLOAD_LYRICS,
            'format': Constants.CONFIG_DOWNLOADER_FORMAT,
            'quality': Constants.CONFIG_DOWNLOADER_QUALITY,
            'transcode_bitrate': Constants.CONFIG_DOWNLOADER_TRANSCODE_BITRATE,
            'skip_existing_files': Constants.CONFIG_DOWNLOADER_SKIP_EXISTING_FILES,
            'skip_previously_downloaded': Constants.CONFIG_DOWNLOADER_SKIP_PREVIOUSLY_DOWNLOADED,
            'skip_download_on_error': Constants.CONFIG_DOWNLOADER_SKIP_DOWNLOAD_ON_ERROR,
            'retry_attempts': Constants.CONFIG_DOWNLOADER_RETRY_ATTEMPTS,
            'bulk_wait_time': Constants.CONFIG_DOWNLOADER_BULK_WAIT_TIME,
            'override_auto_wait': Constants.CONFIG_DOWNLOADER_OVERRIDE_AUTO_WAIT,
            'chunk_size': Constants.CONFIG_DOWNLOADER_CHUNK_SIZE,
            'real_time': Constants.CONFIG_DOWNLOADER_REAL_TIME,
        }

    @classmethod
    def _save_settings(cls) -> None:
        """
        Save settings to the configuration file.

        Attempts to write the current settings stored in the configuration object
        to the pre-defined configuration file path. If successful, logs an
        informational message indicating the file path. If it fails, logs an
        error message with details of the exception.

        :raises Exception: If the settings cannot be saved due to file writing
            errors or other issues.
        """
        try:
            with open(cls._config_file_path, 'w') as configfile:
                cls._config.write(configfile)

            _logger.info(f"Settings saved to {cls._config_file_path}")

        except Exception as e:
            _logger.error(f"Failed to save settings: {e}")

    @classmethod
    def _backup_corrupt_config(cls) -> None:
        """
        Backs up a corrupt configuration file by renaming it with a timestamp.

        This method checks if the configuration file exists and, if so, tries to move it
        to a new location with a name indicating that it is a corrupt backup,
        appending a timestamp to the file name. If the operation fails, an error is logged.

        :raises Exception: If the process of moving the corrupt configuration file fails.
        """
        if cls._config_file_path.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = cls._config_file_path.with_name(f"{cls._config_file_path.stem}_corrupt_{timestamp}.ini")

            try:
                shutil.move(cls._config_file_path, backup_path)

                _logger.warning(f"Backed up corrupt config to {backup_path}")

            except Exception as e:
                _logger.error(f"Failed to back up corrupt config: {e}")

    @classmethod
    def _load_settings(cls) -> None:
        """
        Loads settings from the configuration file. If the configuration file does not exist, generates
        default settings and saves them to a new file. If the file is malformed, creates a backup of
        the corrupt file, generates default settings, and then saves to a new configuration file.

        This method ensures that the class-level settings are properly initialized and that corrupt
        configuration files are handled appropriately.

        :raises configparser.Error: If any parsing error occurs in configuration processing.
        :raises Exception: For any unexpected exceptions encountered while loading configuration.
        """
        if not cls._config_file_path.exists():
            _logger.info("Config file does not exist. Creating new one.")

            cls._generate_default_settings()
            cls._save_settings()

        else:
            try:
                cls._config.read(cls._config_file_path)
                list(cls._config.sections())  # Trigger potential parse errors

                _logger.info("Settings loaded successfully")

            except (configparser.Error, Exception) as e:
                _logger.warning(f"Malformed config file detected: {e}")

                cls._backup_corrupt_config()

                cls._config = configparser.ConfigParser()

                cls._generate_default_settings()
                cls._save_settings()

    @classmethod
    def get(cls, section: str, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value from a specified section and key. If the key
        does not exist within the specified section, the provided default value
        is returned instead.

        :param section: The section in the configuration file to search within.
        :param key: The name of the key to retrieve the value for.
        :param default: The value to return if the key does not exist.
        :return: The value retrieved from the configuration if the key exists,
            otherwise the provided default value.
        """
        if cls._config.has_option(section, key):
            value = cls._config.get(section, key)

            _logger.debug(f"Retrieved [{section}] {key} = {value}")

            return value

        _logger.debug(f"Key not found: [{section}] {key}, returning default: {default}")

        return default

    @classmethod
    def set(cls, section: str, key: str, value: Any) -> None:
        """
        Sets a configuration value for a specific section and key. If the specified
        section does not exist, it will be created.

        :param section: The name of the section where the configuration key belongs.
        :type section: str
        :param key: The configuration key to be set.
        :type key: str
        :param value: The value to be assigned to the configuration key.
        :type value: Any
        :return: None
        """
        if not cls._config.has_section(section):
            cls._config.add_section(section)

            _logger.debug(f"Created new section: [{section}]")

        cls._config.set(section, key, str(value))

        _logger.info(f"Set [{section}] {key} = {value}")

        cls._save_settings()

    @classmethod
    def remove(cls, section: str, key: str) -> None:
        """
        Class method to remove a specific configuration key from a given section. If the key exists
        under the specified section in the configuration, it removes the key, logs the action,
        and saves the updated settings. If the key does not exist, a debug log is issued to indicate
        the attempted removal of a nonexistent key.

        :param section: The section in the configuration from which the key is to be removed
        :type section: str
        :param key: The key to remove from the specified section
        :type key: str
        :return: None
        """
        if cls._config.has_option(section, key):
            cls._config.remove_option(section, key)

            _logger.info(f"Removed key: [{section}] {key}")

            cls._save_settings()
        else:
            _logger.debug(f"Tried to remove nonexistent key: [{section}] {key}")
