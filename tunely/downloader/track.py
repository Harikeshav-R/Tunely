from tunely.utils.constants import Constants
from tunely.downloader.downloader import Downloader


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
