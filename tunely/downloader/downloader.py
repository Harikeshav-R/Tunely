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
from tunely.utils.db import Database

_logger = logging.getLogger(__name__)


class Downloader:
    session: Session = None

    @classmethod
    def login(cls, user_name: str = None) -> None:
        """
        Attempts to login a user either through stored credentials or OAuth. Handles retries in case of failure.
        If a username is provided, the method first attempts to use stored credentials associated with that username.
        Otherwise, it uses OAuth authentication and retries login according to the configured number of attempts.

        :param user_name: The username of the account to login with. Default is None.
        :type user_name: str, optional
        :return: None
        :rtype: None
        :raises ConnectionError: If unable to login after the configured number of retries.
        """

        def auth_url_callback(url):
            # TODO: Modify this to use a GUI or terminal interface for input
            print(url)

        if user_name:
            account = Database.get_account_by_user_name(user_name)

            if account is not None:
                try:
                    _logger.info("Stored credentials found, trying to login using stored credentials")
                    cls.session = Session.Builder().stored(
                        json.dumps(
                            {
                                "username": account.user_name,
                                "credentials": account.credentials,
                                "type": account.type
                            }
                        )
                    ).create()
                    _logger.info("Logged in successfully")
                    return

                except:
                    Database.delete_account(account=account)
                    _logger.warning(
                        f"Failed to login using stored credentials for user {account.user_name}, deleting account. Trying to login using OAuth."
                    )
                    pass

            else:
                _logger.warning("No stored credentials found, trying to login using OAuth")
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
                local_credentials_file_path = Path("credentials.json").resolve()

                if local_credentials_file_path.exists():
                    credentials = json.loads(local_credentials_file_path.read_text())

                    Database.create_account(user_name=credentials["username"], credentials=credentials["credentials"],
                                            type_=credentials["type"])

                    local_credentials_file_path.unlink(missing_ok=True)

                    _logger.info("Logged in successfully")

                    break

                else:
                    _logger.warning("Failed to log in, retrying login in 3 seconds...")
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
            'user-read-email', 'playlist-read-private',
            'user-library-read', 'user-follow-read'
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
        }, {'limit': limit, 'offset': offset}

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
    def invoke_url_with_params(cls, url: str, limit: int, offset: int, **kwargs) -> dict:
        """
        Invokes the specified URL with query parameters and authentication headers. Useful for
        making GET requests to endpoints requiring authentication. This method constructs
        parameters with pagination support and allows additional custom parameters.

        :param url: The URL to send the GET request to
        :type url: str
        :param limit: The pagination limit
        :type limit: int
        :param offset: The pagination offset
        :type offset: int
        :param kwargs: Additional parameters to include in the GET request
        :return: The response JSON from the GET request
        :rtype: dict
        """
        headers, params = cls.get_auth_header_and_params(limit=limit, offset=offset)
        params.update(kwargs)
        return requests.get(url, headers=headers, params=params).json()

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
        result = cls.session.get_user_attribute("type") == "premium"

        if result:
            _logger.info("User has a Spotify Premium subscription")

        else:
            _logger.info("User does not have a Spotify Premium subscription")

        return result
