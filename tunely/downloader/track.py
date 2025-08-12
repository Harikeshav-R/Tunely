import logging
import math

from pathlib import Path
from typing import Any

from tunely.utils.constants import Constants
from tunely.downloader.downloader import Downloader

_logger = logging.getLogger(__name__)


class Track:
    @staticmethod
    def get_user_saved_tracks() -> list[str]:
        """
        Retrieve the user's saved tracks from Spotify.

        This method fetches and compiles a complete list of saved tracks from Spotify.
        It uses pagination to fetch data in chunks of a predefined limit and continues
        fetching until there are no more tracks to retrieve. The saved tracks are
        then returned as a list of strings representing track details.

        :raises Exception: If an error occurs during the API call.

        :return: A list of strings containing links of the user's saved tracks.
        :rtype: list[str]
        """
        songs = []
        offset = 0
        limit = 50

        while True:
            resp = Downloader.invoke_url_with_params(
                Constants.SPOTIFY_SAVED_TRACKS_URL, limit=limit, offset=offset)

            offset += limit

            songs.extend(resp[Constants.SPOTIFY_ITEMS])

            if len(resp[Constants.SPOTIFY_ITEMS]) < limit:
                break

        return songs

    @staticmethod
    def get_followed_artists() -> list[str]:
        """
        Retrieve a list of artist IDs that the user follows on Spotify.

        This method fetches the data from the Spotify API's followed artists
        endpoint, extracts the artist IDs, and compiles them into a list.

        :returns: A list of Spotify artist IDs that the user follows.
        :rtype: list[str]
        """
        artists = []

        resp = Downloader.invoke_url(Constants.SPOTIFY_FOLLOWED_ARTISTS_URL)[1]

        for artist in resp[Constants.SPOTIFY_ARTISTS][Constants.SPOTIFY_ITEMS]:
            artists.append(artist[Constants.SPOTIFY_ID])

        return artists

    @staticmethod
    def get_song_info(song_id) -> tuple[list[str], list[Any], str, str, Any, Any, Any, Any, Any, Any, int]:
        """
        Fetches detailed information about a song from Spotify using its song ID.

        This function communicates with the Spotify API to retrieve metadata of the
        specified track, including information such as the artists, album, release year,
        track details, and other related data. The metadata is parsed and returned in a
        structured format.

        :param song_id: The Spotify ID of the song to retrieve information for.
        :type song_id: str
        :return: A tuple containing the following:
                 - list of artist names
                 - list of detailed artist information (raw data)
                 - album name
                 - song name
                 - album image URL
                 - release year (string format)
                 - disc number
                 - track number
                 - unique track ID
                 - playability status (boolean or None)
                 - duration in milliseconds (integer)
        :rtype: tuple[list[str], list[Any], str, str, Any, Any, Any, Any, Any, Any, int]
        :raises ValueError: If the response from Spotify API is invalid or cannot be parsed.
        """

        _logger.info(f"Getting song info for {song_id}")
        (raw, info) = Downloader.invoke_url(f'{Constants.SPOTIFY_TRACKS_URL}?ids={song_id}&market=from_token')

        if not Constants.SPOTIFY_TRACKS in info:
            _logger.error(f'Invalid response from TRACKS_URL:\n{raw}')
            raise ValueError(f'Invalid response from TRACKS_URL:\n{raw}')

        try:
            artists = []
            for data in info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ARTISTS]:
                artists.append(data[Constants.SPOTIFY_NAME])

            album_name = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ALBUM][Constants.SPOTIFY_NAME]
            name = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_NAME]
            release_year = \
                info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ALBUM][Constants.SPOTIFY_RELEASE_DATE].split('-')[0]
            disc_number = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_DISC_NUMBER]
            track_number = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_TRACK_NUMBER]
            scraped_song_id = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ID]
            is_playable = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_IS_PLAYABLE]
            duration_ms = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_DURATION_MS]

            image = info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ALBUM][Constants.SPOTIFY_IMAGES][0]
            for i in info[Constants.SPOTIFY_TRACKS][0][Constants.SPOTIFY_ALBUM][Constants.SPOTIFY_IMAGES]:
                if i[Constants.SPOTIFY_WIDTH] > image[Constants.SPOTIFY_WIDTH]:
                    image = i
            image_url = image[Constants.SPOTIFY_URL]

            _logger.info(f"Song info for {song_id} retrieved")

            return artists, info[Constants.SPOTIFY_TRACKS][0][
                Constants.SPOTIFY_ARTISTS], album_name, name, image_url, release_year, disc_number, track_number, scraped_song_id, is_playable, duration_ms

        except Exception as e:
            raise ValueError(f'Failed to parse TRACKS_URL response: {str(e)}\n{raw}')

    @staticmethod
    def get_song_lyrics(song_id: str, lyrics_file_path: Path) -> None:
        """
        Fetches and saves song lyrics, either unsynced or line synced, to a specified file path.

        This method communicates with an external API to download the lyrics associated
        with a given song ID. According to the sync type of the lyrics, it formats and
        saves either unsynced or line-synced lyrics into the file at the specified path.

        :param song_id: The unique identifier of the song.
        :type song_id: str
        :param lyrics_file_path: The path where the lyrics file will be saved.
        :type lyrics_file_path: Path
        :return: None
        :raises ValueError: Raised if the lyrics cannot be fetched or are unavailable.
        """
        raw, lyrics = Downloader.invoke_url(f'https://spclient.wg.spotify.com/color-lyrics/v2/track/{song_id}')

        if lyrics:
            try:
                formatted_lyrics = lyrics['lyrics']['lines']
            except KeyError:
                _logger.error(f'Failed to fetch lyrics: {song_id}')
                raise ValueError(f'Failed to fetch lyrics: {song_id}')

            if lyrics['lyrics']['syncType'] == "UNSYNCED":
                with open(lyrics_file_path, 'w+', encoding='utf-8') as file:
                    for line in formatted_lyrics:
                        file.writelines(line['words'] + '\n')

                _logger.info(f"Lyrics saved to {lyrics_file_path}")
                return

            elif lyrics['lyrics']['syncType'] == "LINE_SYNCED":
                with open(lyrics_file_path, 'w+', encoding='utf-8') as file:
                    for line in formatted_lyrics:
                        timestamp = int(line['startTimeMs'])
                        ts_minutes = str(math.floor(timestamp / 60000)).zfill(2)
                        ts_seconds = str(math.floor((timestamp % 60000) / 1000)).zfill(2)
                        ts_millis = str(math.floor(timestamp % 1000))[:2].zfill(2)
                        file.writelines(f'[{ts_minutes}:{ts_seconds}.{ts_millis}]' + line['words'] + '\n')

                _logger.info(f"Lyrics saved to {lyrics_file_path}")
                return

        _logger.error(f'Failed to fetch lyrics: {song_id}')
        raise ValueError(f'Failed to fetch lyrics: {song_id}')
