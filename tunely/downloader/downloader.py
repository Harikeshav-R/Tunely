import json
import logging
import time

import librespot
import librespot.mercury
import requests

from pathlib import Path

from librespot.audio import PlayableContentFeeder
from librespot.audio.decoders import VorbisOnlyAudioQuality, AudioQuality
from librespot.core import Session
from librespot.metadata import PlayableId

from tunely.utils.config import Config
from tunely.utils.constants import Constants

_logger = logging.getLogger(__name__)


class Downloader:
    session: Session = None

    @classmethod
    def login(cls) -> None:
        """
        Attempts to login to Spotify using stored credentials or OAuth authentication.

        First, the method checks for stored credentials at a predefined location. If stored
        credentials exist, it will attempt to use them for login. If that fails or the credentials
        do not exist, the method performs an OAuth login, allowing multiple retry attempts as
        configured.

        If login is successful, the credentials are saved locally to enable easier logins in
        future sessions. The credentials file is securely written to its specified location and
        deleted from the local directory afterward. The method also executes a callback function
        to handle the OAuth URL during the login flow.

        If all login attempts fail due to connection issues or other errors, the method raises
        a `ConnectionError`.

        :raises ConnectionError: If all attempts to log in to Spotify fail due to network issues
            or invalid credentials.
        """

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
    def get_content_stream(cls, content_id: PlayableId,
                           quality: AudioQuality) -> PlayableContentFeeder.LoadedStream | None:
        """
        Retrieves a content stream based on the given content ID and audio quality.

        This method interacts with the session object to access the content feeder
        and retrieve the audio stream corresponding to the specified content ID and
        audio quality settings. The function ensures compatibility with Vorbis-only
        audio formats.

        :param content_id: The unique identifier of the content to load.
        :param quality: The desired audio quality for the content, used to determine
            the appropriate stream settings.
        :return: The loaded content stream provided by the content feeder.
        """
        return cls.session.content_feeder().load(content_id, VorbisOnlyAudioQuality(quality), False, None)

    @classmethod
    def __get_auth_token(cls) -> str:
        """
        Fetches and returns the Spotify authentication token by requesting the required scopes.

        This method is used to retrieve the access token with the appropriate permissions
        required for performing actions like reading the user's email, accessing private
        playlists, reading the user's library, and accessing the user's follow information.

        The token retrieved is scoped to the permissions defined in the parameters passed
        to the method.

        :raises Exception: If the token retrieval fails.

        :return: The Spotify authentication token with the requested permissions.
        :rtype: str
        """
        return cls.session.tokens().get_token(
            Constants.SPOTIFY_USER_READ_EMAIL, Constants.SPOTIFY_PLAYLIST_READ_PRIVATE,
            Constants.SPOTIFY_USER_LIBRARY_READ, Constants.SPOTIFY_USER_FOLLOW_READ
        ).access_token

    @classmethod
    def get_auth_header(cls) -> dict:
        """
        Generates the authentication header required for making authorized requests.

        This class method retrieves the authentication token and constructs a dictionary
        containing the necessary headers for API requests, including authorization, language,
        acceptance type, and platform information.

        :return: A dictionary containing header information required for authorization.
        :rtype: dict
        """
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{Config.get("downloader", "language", Constants.CONFIG_DOWNLOADER_LANGUAGE)}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }

    @classmethod
    def get_auth_header_and_params(cls, limit, offset) -> tuple[dict, dict]:
        """
        Generates authentication headers and parameters for API requests.

        This method is a class method used for constructing HTTP headers and
        query parameters required to interact with the Spotify API. It
        dynamically includes authentication tokens and pre-defined
        header fields with their corresponding values.

        :param limit: The maximum number of items to return
            from the API (pagination limit).
        :type limit: int
        :param offset: The index of the first item to return from the
            API (pagination offset).
        :type offset: int
        :return: A tuple containing two dictionaries:
            1. The HTTP headers required for the request.
            2. The query parameters for controlling API responses.
        :rtype: tuple[dict, dict]
        """
        return {
            'Authorization': f'Bearer {cls.__get_auth_token()}',
            'Accept-Language': f'{Config.get("downloader", "language", Constants.CONFIG_DOWNLOADER_LANGUAGE)}',
            'Accept': 'application/json',
            'app-platform': 'WebPlayer'
        }, {Constants.SPOTIFY_LIMIT: limit, Constants.SPOTIFY_OFFSET: offset}

    @classmethod
    def invoke_url(cls, url: str, try_count: int = 0) -> tuple[str, dict]:
        headers = cls.get_auth_header()
        response = requests.get(url, headers=headers)
        response_text = response.text
        try:
            response_json = response.json()
        except json.decoder.JSONDecodeError:
            response_json = {"error": {"status": "unknown", "message": "received an empty response"}}

        if not response_json or 'error' in response_json:
            if try_count < (Config.get("downloader", "retry_attempts", Constants.CONFIG_DOWNLOADER_RETRY_ATTEMPTS) - 1):
                _logger.warning(
                    f"Spotify API Error (try {try_count + 1}) ({response_json['error']['status']}): {response_json['error']['message']}")
                time.sleep(5)
                return cls.invoke_url(url, try_count + 1)

            _logger.warning(
                f"Spotify API Error ({response_json['error']['status']}): {response_json['error']['message']}")

        return response_text, response_json

    @classmethod
    def check_premium(cls) -> bool:
        """
        Checks if the current user has a Spotify Premium subscription.

        This method checks the user's subscription type by retrieving the relevant
        attribute from the session. It will return whether the user has a Spotify
        Premium account.

        :rtype: bool
        :return: True if the user has a Spotify Premium subscription, False otherwise.
        """
        result = cls.session.get_user_attribute(Constants.SPOTIFY_TYPE) == Constants.SPOTIFY_PREMIUM

        if result:
            _logger.info("User has a Spotify Premium subscription")

        else:
            _logger.info("User does not have a Spotify Premium subscription")

        return result
