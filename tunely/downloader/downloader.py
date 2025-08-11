import json
import logging
import time

import librespot
import librespot.mercury
import requests

from pathlib import Path

from librespot.audio.decoders import VorbisOnlyAudioQuality, AudioQuality
from librespot.core import Session
from librespot.metadata import PlayableId

from tunely.utils.config import Config
from tunely.utils.constants import Constants

_logger = logging.getLogger(__name__)


class Downloader:
    session: Session = None

    @classmethod
    def login(cls):
        def auth_url_callback(url):
            print(url)

        credentials_file_path = Path(
            Config.get("downloader", "credentials_file", Constants.CONFIG_DOWNLOADER_CREDENTIALS_FILE)).resolve()

        if credentials_file_path.exists():
            try:
                _logger.info("Stored credentials found, trying to login using stored credentials")
                cls.session = Session.Builder().stored_file().create()
                _logger.info("Logged in successfully")
                return

            except:
                _logger.warning("Failed to login using stored credentials, trying to login using OAuth")
                pass

        login_retry_attempts = int(
            Config.get("downloader", "login_retry_attempts", Constants.CONFIG_DOWNLOADER_LOGIN_RETRY_ATTEMPTS))

        for i in range(login_retry_attempts):
            _logger.info(f"Attempting to login to Spotify (attempt {i + 1}/{login_retry_attempts})...")

            try:
                cls.session = Session.Builder() \
                    .oauth(auth_url_callback) \
                    .create()

            except librespot.mercury.MercuryClient.MercuryException:
                pass

            except ConnectionError:
                time.sleep(3)
                _logger.warning("Connection error, retrying login in 3 seconds...")
                continue

            finally:
                _logger.info("Logged in successfully")

                local_credentials_file_path = Path("credentials.json").resolve()

                if local_credentials_file_path.exists():
                    with open(credentials_file_path, "w") as credentials_file:
                        credentials_file.write(open(local_credentials_file_path).read())
                        local_credentials_file_path.unlink(missing_ok=True)

                    _logger.info("Login saved for future use")

                    break

                else:
                    _logger.warning("Failed to save login credentials, retrying login in 3 seconds...")
                    time.sleep(3)

                    continue

        else:
            _logger.error("Failed to login to Spotify")
            raise ConnectionError("Could not login to Spotify")

    @classmethod
    def get_content_stream(cls, content_id: PlayableId, quality: AudioQuality):
        return cls.session.content_feeder().load(content_id, VorbisOnlyAudioQuality(quality), False, None)

    @classmethod
    def __get_auth_token(cls):
        return cls.session.tokens().get_token(
            Constants.SPOTIFY_USER_READ_EMAIL, Constants.SPOTIFY_PLAYLIST_READ_PRIVATE,
            Constants.SPOTIFY_USER_LIBRARY_READ, Constants.SPOTIFY_USER_FOLLOW_READ
        ).access_token

    @classmethod
    def get_auth_header(cls):
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{Config.get("downloader", "language", Constants.CONFIG_DOWNLOADER_LANGUAGE)}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }

    @classmethod
    def get_auth_header_and_params(cls, limit, offset):
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{Config.get("downloader", "language", Constants.CONFIG_DOWNLOADER_LANGUAGE)}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }, {Constants.SPOTIFY_LIMIT: limit, Constants.SPOTIFY_OFFSET: offset}


