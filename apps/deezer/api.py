import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DeezerAPI:
    BASE_URL = settings.DEEZER_BASE_URL

    @classmethod
    def _get_url(cls, endpoint):
        return f"{cls.BASE_URL}/{endpoint}"

    @classmethod
    def _make_request(cls, endpoint, params=None, cache_key=None, cache_timeout=3600):
        url = cls._get_url(endpoint)
        if cache_key:
            cached = cache.get(cache_key)
            if cached:
                return cached
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if cache_key and 'error' not in data:
                cache.set(cache_key, data, cache_timeout)
            return data
        except requests.RequestException as e:
            logger.error(f"Deezer API error: {e}")
            return {'error': str(e)}

    @classmethod
    def search_artists(cls, q, limit=20, index=0):
        params = {'q': q, 'limit': limit, 'index': index}
        return cls._make_request('search/artist', params=params,
                                 cache_key=f"deezer:artists:{q}:{limit}:{index}")

    @classmethod
    def search_tracks(cls, q, limit=20, index=0):
        params = {'q': q, 'limit': limit, 'index': index}
        return cls._make_request('search/track', params=params,
                                 cache_key=f"deezer:tracks:{q}:{limit}:{index}")

    @classmethod
    def search_albums(cls, q, limit=20, index=0):
        params = {'q': q, 'limit': limit, 'index': index}
        return cls._make_request('search/album', params=params,
                                 cache_key=f"deezer:albums:{q}:{limit}:{index}")

    @classmethod
    def get_artist(cls, artist_id):
        return cls._make_request(f"artist/{artist_id}",
                                cache_key=f"deezer:artist:{artist_id}")

    @classmethod
    def get_artist_albums(cls, artist_id):
        return cls._make_request(f"artist/{artist_id}/albums",
                                cache_key=f"deezer:artist:{artist_id}:albums")

    @classmethod
    def get_artist_top_tracks(cls, artist_id):
        return cls._make_request(f"artist/{artist_id}/top",
                                cache_key=f"deezer:artist:{artist_id}:top")

    @classmethod
    def get_album(cls, album_id):
        return cls._make_request(f"album/{album_id}",
                                cache_key=f"deezer:album:{album_id}")

    @classmethod
    def get_album_tracks(cls, album_id):
        return cls._make_request(f"album/{album_id}/tracks",
                                cache_key=f"deezer:album:{album_id}:tracks")

    @classmethod
    def get_track(cls, track_id):
        return cls._make_request(f"track/{track_id}",
                                cache_key=f"deezer:track:{track_id}")

    @classmethod
    def get_similar_tracks(cls, track_id):
        return cls._make_request(f"track/{track_id}/related",
                                cache_key=f"deezer:track:{track_id}:related")

    @classmethod
    def get_tracks_by_genre(cls, genre_id, limit=20):
        params = {'limit': limit}
        return cls._make_request(f"genre/{genre_id}/tracks", params=params,
                                cache_key=f"deezer:genre:{genre_id}:tracks:{limit}")

    @classmethod
    def get_recommendation(cls, limit=10):
        params = {'limit': limit}
        return cls._make_request('chart/0/tracks', params=params,
                                cache_key=f"deezer:chart:tracks:{limit}")