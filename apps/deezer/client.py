import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class DeezerClient:
    BASE_URL = 'https://api.deezer.com'

    def __init__(self):
        self.base_url = settings.DEEZER_BASE_URL
        self.session = requests.Session()

    def _make_request(self, endpoint, params=None, cache_key=None, cache_time=3600):
        if cache_key:
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

        url = f"{self.base_url}/{endpoint}"
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if cache_key and data:
                cache.set(cache_key, data, cache_time)

            return data
        except requests.RequestException as e:
            logger.error(f"Deezer API error: {str(e)}")
            return None

    def search_artists(self, query, limit=20, offset=0):
        params = {'q': query, 'limit': limit, 'index': offset}
        cache_key = f"deezer:artist_search:{query}:{limit}:{offset}"
        return self._make_request('search/artist', params, cache_key)

    def search_tracks(self, query, limit=20):
        url = f'{self.BASE_URL}/search'
        resp = requests.get(url, params={'q': query, 'limit': limit}, timeout=10)
        resp.raise_for_status()
        items = resp.json().get('data', [])
        results = []
        for d in items:
            results.append({
                'id': str(d.get('id')),
                'title': d.get('title'),
                'duration': d.get('duration'),
                'artist': {
                    'id': str(d.get('artist', {}).get('id')),
                    'name': d.get('artist', {}).get('name')
                },
                'album': {
                    'id': str(d.get('album', {}).get('id')),
                    'title': d.get('album', {}).get('title'),
                    'cover_medium': d.get('album', {}).get('cover_medium')
                }
            })
        return results

    def get_artist(self, artist_id):
        cache_key = f"deezer:artist:{artist_id}"
        return self._make_request(f"artist/{artist_id}", cache_key=cache_key)

    def get_artist_albums(self, artist_id, limit=20, offset=0):
        params = {'limit': limit, 'index': offset}
        cache_key = f"deezer:artist_albums:{artist_id}:{limit}:{offset}"
        return self._make_request(f"artist/{artist_id}/albums", params, cache_key)

    def get_artist_top_tracks(self, artist_id, limit=20):
        params = {'limit': limit}
        cache_key = f"deezer:artist_top:{artist_id}:{limit}"
        return self._make_request(f"artist/{artist_id}/top", params, cache_key)

    def get_album(self, album_id):
        cache_key = f"deezer:album:{album_id}"
        return self._make_request(f"album/{album_id}", cache_key=cache_key)

    def get_album_tracks(self, album_id):
        cache_key = f"deezer:album_tracks:{album_id}"
        return self._make_request(f"album/{album_id}/tracks", cache_key=cache_key)

    def get_track(self, track_id):
        url = f'{self.BASE_URL}/track/{track_id}'
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get('error'):
            return None
        return {
            'id': str(data.get('id')),
            'title': data.get('title'),
            'preview': data.get('preview'),
            'duration': data.get('duration'),
            'artist': {
                'id': str(data.get('artist', {}).get('id')),
                'name': data.get('artist', {}).get('name'),
                'picture': data.get('artist', {}).get('picture_medium')
            },
            'album': {
                'id': str(data.get('album', {}).get('id')),
                'title': data.get('album', {}).get('title'),
                'cover_medium': data.get('album', {}).get('cover_medium'),
                'cover_big': data.get('album', {}).get('cover_big')
            }
        }

    def get_related_tracks(self, track_id, limit=10):
        url = f'{self.BASE_URL}/track/{track_id}/related'
        resp = requests.get(url, params={'limit': limit}, timeout=10)
        resp.raise_for_status()
        items = resp.json().get('data', [])
        results = []
        for d in items:
            results.append({
                'id': str(d.get('id')),
                'title': d.get('title'),
                'duration': d.get('duration'),
                'artist': {
                    'id': str(d.get('artist', {}).get('id')),
                    'name': d.get('artist', {}).get('name')
                },
                'album': {
                    'id': str(d.get('album', {}).get('id')),
                    'title': d.get('album', {}).get('title'),
                    'cover_medium': d.get('album', {}).get('cover_medium')
                }
            })
        return results

    def get_tracks_by_genre(self, genre_id, limit=20, offset=0):
        params = {'limit': limit, 'index': offset}
        cache_key = f"deezer:genre_tracks:{genre_id}:{limit}:{offset}"
        return self._make_request(f"genre/{genre_id}/tracks", params, cache_key)

    def get_genres(self):
        cache_key = "deezer:genres"
        return self._make_request("genre", cache_key=cache_key, cache_time=86400)  # Cache for 24 hours

deezer_client = DeezerClient()