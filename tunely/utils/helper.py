import re
from pathlib import Path

import music_tag
import requests

from tunely.utils.constants import Constants


class Helper:
    @staticmethod
    def set_audio_tags(file_path: Path, artists: list[str], name: str, album_name: str, release_year,
                       disc_number, track_number) -> None:
        """
        Set audio tags for a music file using the given metadata.

        This method sets various metadata fields on a music file, such as album artist,
        track artist(s), track title, album name, release year, disc number, and track
        number. The file is updated with the provided information, ensuring accurate
        and organized tagging for usage in music libraries or media players.

        :param file_path: The path of the audio file to which tags need to be applied.
        :type file_path: Path
        :param artists: A list of artist names associated with the track.
        :type artists: list[str]
        :param name: The title of the track.
        :type name: str
        :param album_name: The name of the album to which the track belongs.
        :type album_name: str
        :param release_year: The year the track or album was released.
        :type release_year: Any
        :param disc_number: The disc number the track is located on within the album.
        :type disc_number: Any
        :param track_number: The track number within the disc or album.
        :type track_number: Any
        :return: None
        """

        tag = music_tag.load_file(file_path)
        tag["albumartist"] = artists[0]
        tag["artist"] = ", ".join(artists).strip(" ,")
        tag["tracktitle"] = name
        tag["album"] = album_name
        tag["year"] = release_year
        tag["discnumber"] = disc_number
        tag["tracknumber"] = track_number
        tag.save()

    @staticmethod
    def set_music_thumbnail(file_path: str, thumbnail_url: str) -> None:
        """
        Sets a thumbnail image for the provided music file from a specified URL.

        This method downloads an image from the given URL and sets it as the
        album artwork for the provided music file. It relies on the `music_tag`
        library to load and modify the file's tags and applies the thumbnail
        retrieved via the given URL.

        :param file_path: The path to the music file for which the thumbnail
            will be set.
        :param thumbnail_url: The URL from which the thumbnail image is
            downloaded.
        """
        image = requests.get(thumbnail_url).content
        tags = music_tag.load_file(file_path)
        tags["artwork"] = image
        tags.save()

    @staticmethod
    def regex_input_for_urls(search_input: str) -> tuple[str, str, str, str, str, str]:
        """
        Extracts and matches Spotify-related URIs or URLs from the given input string.

        This static method scans an input string and identifies specific patterns related
        to Spotify URIs and URLs, such as tracks, albums, playlists, episodes, shows, and
        artists. The method attempts to match each type of URI or URL using regular expressions
        and then extracts the associated ID for the matched entity. If no match is found for
        a particular category, the corresponding return value will be ``None``.

        :param search_input: The input string to be processed, which may contain Spotify-related
            URIs or URLs.
        :type search_input: str

        :return: A tuple containing the extracted IDs for Spotify entities. The tuple contains IDs
            for a track, album, playlist, episode, show, and artist in that order. If no ID is
            found for a specific entity, the respective value in the tuple will be ``None``.
        :rtype: tuple[str, str, str, str, str, str]
        """
        track_uri_search = re.search(
            r'^spotify:track:(?P<TrackID>[0-9a-zA-Z]{22})$', search_input)
        track_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/track/(?P<TrackID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        album_uri_search = re.search(
            r'^spotify:album:(?P<AlbumID>[0-9a-zA-Z]{22})$', search_input)
        album_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/album/(?P<AlbumID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        playlist_uri_search = re.search(
            r'^spotify:playlist:(?P<PlaylistID>[0-9a-zA-Z]{22})$', search_input)
        playlist_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/playlist/(?P<PlaylistID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        episode_uri_search = re.search(
            r'^spotify:episode:(?P<EpisodeID>[0-9a-zA-Z]{22})$', search_input)
        episode_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/episode/(?P<EpisodeID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        show_uri_search = re.search(
            r'^spotify:show:(?P<ShowID>[0-9a-zA-Z]{22})$', search_input)
        show_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/show/(?P<ShowID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        artist_uri_search = re.search(
            r'^spotify:artist:(?P<ArtistID>[0-9a-zA-Z]{22})$', search_input)
        artist_url_search = re.search(
            r'^(https?://)?open\.spotify\.com/artist/(?P<ArtistID>[0-9a-zA-Z]{22})(\?si=.+?)?$',
            search_input,
        )

        if track_uri_search is not None or track_url_search is not None:
            track_id_str = (track_uri_search
                            if track_uri_search is not None else
                            track_url_search).group('TrackID')
        else:
            track_id_str = None

        if album_uri_search is not None or album_url_search is not None:
            album_id_str = (album_uri_search
                            if album_uri_search is not None else
                            album_url_search).group('AlbumID')
        else:
            album_id_str = None

        if playlist_uri_search is not None or playlist_url_search is not None:
            playlist_id_str = (playlist_uri_search
                               if playlist_uri_search is not None else
                               playlist_url_search).group('PlaylistID')
        else:
            playlist_id_str = None

        if episode_uri_search is not None or episode_url_search is not None:
            episode_id_str = (episode_uri_search
                              if episode_uri_search is not None else
                              episode_url_search).group('EpisodeID')
        else:
            episode_id_str = None

        if show_uri_search is not None or show_url_search is not None:
            show_id_str = (show_uri_search
                           if show_uri_search is not None else
                           show_url_search).group('ShowID')
        else:
            show_id_str = None

        if artist_uri_search is not None or artist_url_search is not None:
            artist_id_str = (artist_uri_search
                             if artist_uri_search is not None else
                             artist_url_search).group('ArtistID')
        else:
            artist_id_str = None

        return track_id_str, album_id_str, playlist_id_str, episode_id_str, show_id_str, artist_id_str

    @staticmethod
    def fix_file_name(file_name: str):
        """
        Cleans and modifies the given file name to ensure it adheres to file system constraints.

        This method replaces invalid characters or reserved names with underscores. It ensures
        that the file name can safely exist across various operating systems by adhering to their
        naming conventions.

        :param file_name: The input file name string that needs to be corrected, to comply
                          with file naming guidelines.
        :type file_name: str
        :return: A sanitized version of the file name with invalid characters replaced.
        :rtype: str
        """
        return re.sub(r'[/\\:|<>"?*\0-\x1f]|^(AUX|COM[1-9]|CON|LPT[1-9]|NUL|PRN)(?![^.])|^\s|[\s.]$', "_",
                      str(file_name),
                      flags=re.IGNORECASE)
