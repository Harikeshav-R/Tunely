from pathlib import Path

from appdirs import user_config_dir, user_cache_dir, user_data_dir


class Constants:
    APP_NAME = "Tunely"
    APP_AUTHOR = "Harikeshav R"

    CONFIG_DEFAULT_LOG_DIR = Path(user_cache_dir(APP_NAME, APP_AUTHOR), "logs").resolve()
    CONFIG_DEFAULT_LOG_FILE = "tunely.log"
    CONFIG_DEFAULT_LOG_MAX_BYTES = 10_000_000
    CONFIG_DEFAULT_LOG_BACKUP_COUNT = 5
    CONFIG_DEFAULT_LOG_LEVEL = "INFO"
    CONFIG_DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    CONFIG_DEFAULT_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    CONFIG_DEFAULT_CONFIG_DIR = Path(user_config_dir(APP_NAME, APP_AUTHOR)).resolve()
    CONFIG_DEFAULT_CONFIG_FILE = 'config.ini'

    CONFIG_DEFAULT_DATABASE_DIR = Path(user_data_dir(APP_NAME, APP_AUTHOR), 'databases').resolve()
    CONFIG_DEFAULT_DATABASE_FILE = 'tunely.db'

    SPOTIFY_FOLLOWED_ARTISTS_URL = 'https://api.spotify.com/v1/me/following?type=artist'

    SPOTIFY_SAVED_TRACKS_URL = 'https://api.spotify.com/v1/me/tracks'

    SPOTIFY_TRACKS_URL = 'https://api.spotify.com/v1/tracks'

    SPOTIFY_TRACK_STATS_URL = 'https://api.spotify.com/v1/audio-features/'

    SPOTIFY_TRACKNUMBER = 'tracknumber'

    SPOTIFY_DISCNUMBER = 'discnumber'

    SPOTIFY_YEAR = 'year'

    SPOTIFY_ALBUM = 'album'

    SPOTIFY_TRACKTITLE = 'tracktitle'

    SPOTIFY_ARTIST = 'artist'

    SPOTIFY_ARTISTS = 'artists'

    SPOTIFY_ALBUMARTIST = 'albumartist'

    SPOTIFY_GENRES = 'genres'

    SPOTIFY_GENRE = 'genre'

    SPOTIFY_ARTWORK = 'artwork'

    SPOTIFY_TRACKS = 'tracks'

    SPOTIFY_TRACK = 'track'

    SPOTIFY_ITEMS = 'items'

    SPOTIFY_NAME = 'name'

    SPOTIFY_HREF = 'href'

    SPOTIFY_ID = 'id'

    SPOTIFY_URL = 'url'

    SPOTIFY_RELEASE_DATE = 'release_date'

    SPOTIFY_IMAGES = 'images'

    SPOTIFY_LIMIT = 'limit'

    SPOTIFY_OFFSET = 'offset'

    SPOTIFY_AUTHORIZATION = 'Authorization'

    SPOTIFY_IS_PLAYABLE = 'is_playable'

    SPOTIFY_DURATION_MS = 'duration_ms'

    SPOTIFY_TRACK_NUMBER = 'track_number'

    SPOTIFY_DISC_NUMBER = 'disc_number'

    SPOTIFY_SHOW = 'show'

    SPOTIFY_ERROR = 'error'

    SPOTIFY_EXPLICIT = 'explicit'

    SPOTIFY_PLAYLIST = 'playlist'

    PLAYLISTS = 'playlists'

    SPOTIFY_OWNER = 'owner'

    SPOTIFY_DISPLAY_NAME = 'display_name'

    SPOTIFY_ALBUMS = 'albums'

    SPOTIFY_TYPE = 'type'

    SPOTIFY_PREMIUM = 'premium'

    SPOTIFY_WIDTH = 'width'

    SPOTIFY_USER_READ_EMAIL = 'user-read-email'

    SPOTIFY_USER_FOLLOW_READ = 'user-follow-read'

    SPOTIFY_PLAYLIST_READ_PRIVATE = 'playlist-read-private'

    SPOTIFY_USER_LIBRARY_READ = 'user-library-read'

    SPOTIFY_WINDOWS_SYSTEM = 'Windows'

    SPOTIFY_LINUX_SYSTEM = 'Linux'

    SPOTIFY_CODEC_MAP = {
        'aac': 'aac',
        'fdk_aac': 'libfdk_aac',
        'm4a': 'aac',
        'mp3': 'libmp3lame',
        'ogg': 'copy',
        'opus': 'libopus',
        'vorbis': 'copy',
    }

    SPOTIFY_EXT_MAP = {
        'aac': 'm4a',
        'fdk_aac': 'm4a',
        'm4a': 'm4a',
        'mp3': 'mp3',
        'ogg': 'ogg',
        'opus': 'ogg',
        'vorbis': 'ogg',
    }
