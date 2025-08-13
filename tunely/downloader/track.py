import logging
import math
import shutil

import ffmpeg

from pathlib import Path
from typing import Any

from librespot.metadata import TrackId

from tunely.utils.config import Config
from tunely.utils.constants import Constants
from tunely.utils.db import Database
from tunely.utils.helper import Helper
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

            songs.extend(resp["items"])

            if len(resp["items"]) < limit:
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

        for artist in resp["artists"]["items"]:
            artists.append(artist["id"])

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
        raw, info = Downloader.invoke_url(f'{Constants.SPOTIFY_TRACKS_URL}?ids={song_id}&market=from_token')

        if not "tracks" in info:
            _logger.error(f'Invalid response from TRACKS_URL:\n{raw}')
            raise ValueError(f'Invalid response from TRACKS_URL:\n{raw}')

        try:
            artists = []
            for data in info["tracks"][0]["artists"]:
                artists.append(data["name"])

            album_name = info["tracks"][0]["album"]["name"]
            name = info["tracks"][0]["name"]
            release_year = \
                info["tracks"][0]["album"]["release_date"].split('-')[0]
            disc_number = info["tracks"][0]["disc_number"]
            track_number = info["tracks"][0]["track_number"]
            scraped_song_id = info["tracks"][0]["id"]
            is_playable = info["tracks"][0]["is_playable"]
            duration_ms = info["tracks"][0]["duration_ms"]

            image = info["tracks"][0]["album"]["images"][0]
            for i in info["tracks"][0]["album"]["images"]:
                if i["width"] > image["width"]:
                    image = i
            image_url = image["url"]

            _logger.info(f"Song info for {song_id} retrieved")

            return artists, info["tracks"][0][
                "artists"], album_name, name, image_url, release_year, disc_number, track_number, scraped_song_id, is_playable, duration_ms

        except Exception as e:
            raise ValueError(f'Failed to parse TRACKS_URL response: {e.with_traceback(NameError)}\n{raw}')

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

    @staticmethod
    def convert_raw_to_audio(source_file_path: Path) -> None:
        temp_file_path = source_file_path.with_suffix('.temp')
        shutil.move(source_file_path, temp_file_path)

        download_format = Config.get("downloader", "format", Constants.CONFIG_DOWNLOADER_FORMAT)
        codec = Constants.SPOTIFY_CODEC_MAP.get(download_format.lower(), "copy")

        if codec != "copy":
            bitrates = {
                'auto': '320k' if Downloader.check_premium() else '160k',
                'normal': '96k',
                'high': '160k',
                'very_high': '320k'
            }
            bitrate = bitrates[Config.get("downloader", "quality", Constants.CONFIG_DOWNLOADER_QUALITY)]

        else:
            bitrate = None

        try:
            stream = ffmpeg.input(temp_file_path)

            ffmpeg.output(
                stream,
                source_file_path,
                **{
                    'c:a': codec,
                    **({'b:a': bitrate} if bitrate else {})
                }
            )

            temp_file_path.unlink(missing_ok=True)
            _logger.info(f"Converted raw to audio: {source_file_path}")

        except ffmpeg.Error as e:
            _logger.error(f"Failed to convert raw to audio: {e.stderr.decode()}")

    @staticmethod
    def download_track(track_id: str):
        try:
            artists, raw_artists, album_name, name, image_url, release_year, disc_number, track_number, scraped_song_id, is_playable, duration_ms = Track.get_song_info(
                track_id)

            song_name = Helper.fix_file_name(name)
            extension = Constants.SPOTIFY_EXT_MAP.get(
                Config.get("downloader", "format", Constants.CONFIG_DOWNLOADER_FORMAT).lower())

            file_path = Path(Config.get("downloader", "output_dir", Constants.CONFIG_DOWNLOADER_OUTPUT_DIR),
                             Helper.fix_file_name(artists[0]),
                             Helper.fix_file_name(album_name),
                             f"{track_number} - {Helper.fix_file_name(song_name)}.{extension}")

        except Exception as e:
            _logger.error(f"Failed to download track {track_id}: {e.with_traceback(None)}")
            return

        _logger.info(f"Downloading track {track_id} to {file_path}")

        try:
            if not is_playable:
                _logger.error(f"Skipping track {track_id} because it is not playable")
                return

            if Database.get_downloaded_songs_by_id(track_id) is not None or file_path.exists():
                _logger.info(f"Skipping track {track_id} because it is already downloaded")
                return

            if track_id != scraped_song_id:
                track_id = scraped_song_id

            track = TrackId.from_base62(track_id)
            stream = Downloader.get_content_stream(track, Config.get("downloader", "quality",
                                                                     Constants.CONFIG_DOWNLOADER_QUALITY))

            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'wb') as f:
                b = 0

                while b < 5:
                    data = stream.input_stream.stream().read(
                        Config.get("downloader", "chunk_size", Constants.CONFIG_DOWNLOADER_CHUNK_SIZE))
                    f.write(data)
                    b += 1 if data == b'' else 0

            _logger.info(f"Raw data for track {track_id} downloaded")

            download_lyrics = Config.get("downloader", "download_lyrics", Constants.CONFIG_DOWNLOADER_DOWNLOAD_LYRICS)
            download_lyrics_flag = True
            if isinstance(download_lyrics, bool) and download_lyrics:
                download_lyrics_flag = download_lyrics

            elif isinstance(download_lyrics, str) and download_lyrics.lower() == "true":
                download_lyrics_flag = True

            elif isinstance(download_lyrics, str) and download_lyrics.lower() == "false":
                download_lyrics_flag = False

            if download_lyrics_flag:
                try:
                    Track.get_song_lyrics(track_id, file_path.with_suffix('.lrc'))
                    _logger.info(f"Lyrics downloaded for track {track_id}")

                except ValueError:
                    _logger.error(f"Failed to download lyrics for track {track_id}")

            Track.convert_raw_to_audio(file_path)

            _logger.info(
                f"Audio converted to {Config.get('downloader', 'format', Constants.CONFIG_DOWNLOADER_FORMAT)} for track {track_id}")

            try:
                Helper.set_audio_tags(file_path, artists, name, album_name, release_year, disc_number, track_number)
                Helper.set_music_thumbnail(file_path, image_url)
                _logger.info(f"Audio tags set for track {track_id}")

            except Exception as e:
                _logger.error(f"Failed to set audio tags for track {track_id}: {e.with_traceback(None)}")

            Database.create_downloaded_song(track_id, Downloader.account, str(file_path))

        except Exception as e:
            _logger.error(f"Failed to download track {track_id}: {e.with_traceback(None)}")
