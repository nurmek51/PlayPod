import requests
from django.conf import settings
from django.core.cache import cache
import logging
import random

logger = logging.getLogger(__name__)


class DeezerClient:
    BASE_URL = 'https://api.deezer.com'

    def __init__(self):
        self.base_url = settings.DEEZER_BASE_URL or self.BASE_URL
        self.session = requests.Session()

    def _make_request(self, endpoint, params=None, cache_key=None, cache_time=3600):
        """Make a request to the Deezer API with caching support"""
        if cache_key:
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

        url = f"{self.base_url}/{endpoint}"
        logger.info(f"Making request to Deezer API: {url} with params: {params}")
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            try:
                data = response.json()
            except ValueError as e:
                logger.error(f"Invalid JSON response from Deezer API {url}: {str(e)}")
                return None
            
            # Check for Deezer error response
            if isinstance(data, dict) and data.get('error'):
                error_msg = data.get('error', {}).get('message', 'Unknown Deezer API error')
                error_code = data.get('error', {}).get('code', 0)
                logger.error(f"Deezer API error for {url}: {error_code} - {error_msg}")
                return None
            
            if isinstance(data, dict):
                if 'data' in data:
                    logger.info(f"Received {len(data.get('data', []))} items from {url}")
                else:
                    logger.info(f"Received response from {url}: {list(data.keys())}")
            else:
                logger.info(f"Received non-dictionary response from {url}: {type(data)}")

            if cache_key and data:
                cache.set(cache_key, data, cache_time)

            return data
        except requests.RequestException as e:
            logger.error(f"Deezer API error for {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error accessing Deezer API {url}: {str(e)}")
            return None

    def search_artists(self, query, limit=20, offset=0):
        """Search for artists by query string"""
        params = {'q': query, 'limit': limit, 'index': offset}
        cache_key = f"deezer:artist_search:{query}:{limit}:{offset}"
        response = self._make_request('search/artist', params, cache_key)
        return response.get('data', []) if response else []

    def search_tracks(self, query, limit=20, offset=0):
        """Search for tracks by query string"""
        params = {'q': query, 'limit': limit, 'index': offset}
        cache_key = f"deezer:track_search:{query}:{limit}:{offset}"
        response = self._make_request('search/track', params, cache_key)
        return response.get('data', []) if response else []

    def search_albums(self, query, limit=20, offset=0):
        """Search for albums by query string"""
        params = {'q': query, 'limit': limit, 'index': offset}
        cache_key = f"deezer:album_search:{query}:{limit}:{offset}"
        response = self._make_request('search/album', params, cache_key)
        return response.get('data', []) if response else []

    def get_artist(self, artist_id):
        """Get information about a specific artist"""
        cache_key = f"deezer:artist:{artist_id}"
        return self._make_request(f"artist/{artist_id}", cache_key=cache_key)

    def get_artist_albums(self, artist_id, limit=20, offset=0):
        """Get albums for a specific artist"""
        params = {'limit': limit, 'index': offset}
        cache_key = f"deezer:artist_albums:{artist_id}:{limit}:{offset}"
        response = self._make_request(f"artist/{artist_id}/albums", params, cache_key)
        return response.get('data', []) if isinstance(response, dict) else []

    def get_artist_top_tracks(self, artist_id, limit=20):
        """Get top tracks for a specific artist"""
        params = {'limit': limit}
        cache_key = f"deezer:artist_top:{artist_id}:{limit}"
        response = self._make_request(f"artist/{artist_id}/top", params, cache_key)
        return response.get('data', []) if isinstance(response, dict) else []

    def get_album(self, album_id):
        """Get information about a specific album"""
        cache_key = f"deezer:album:{album_id}"
        return self._make_request(f"album/{album_id}", cache_key=cache_key)

    def get_album_tracks(self, album_id):
        """Get tracks for a specific album"""
        cache_key = f"deezer:album_tracks:{album_id}"
        response = self._make_request(f"album/{album_id}/tracks", cache_key=cache_key)
        return response.get('data', []) if response else []

    def get_track(self, track_id, skip_cache=False):
        """Get information about a specific track"""
        cache_key = f"deezer:track:{track_id}"
        
        # Skip cache if requested
        if skip_cache:
            return self._make_request(f"track/{track_id}")
            
        return self._make_request(f"track/{track_id}", cache_key=cache_key)

    def get_related_tracks(self, track_id, limit=10):
        """Get tracks related to a specific track"""
        params = {'limit': limit}
        cache_key = f"deezer:track_related:{track_id}:{limit}"
        response = self._make_request(f"track/{track_id}/related", params, cache_key)
        return response.get('data', []) if response else []
        
    def get_track_recommendations(self, track_id, limit=20):
        """Get track recommendations based on a track ID"""
        return self.get_related_tracks(track_id, limit=limit)

    def get_genres(self):
        """Get all available music genres"""
        cache_key = "deezer:genres"
        response = self._make_request("genre", cache_key=cache_key, cache_time=86400)
        return response.get('data', []) if response else []

    def get_genre(self, genre_id):
        """Get information about a specific genre"""
        cache_key = f"deezer:genre:{genre_id}"
        return self._make_request(f"genre/{genre_id}", cache_key=cache_key, cache_time=86400)

    def get_genre_tracks(self, genre_name, limit=30):
        """Get tracks for a specific genre by name"""
        genre_id = self._get_genre_id_by_name(genre_name)
        if not genre_id:
            return []
            
        params = {'limit': limit}
        cache_key = f"deezer:genre_tracks:{genre_id}:{limit}"
        response = self._make_request(f"genre/{genre_id}/tracks", params, cache_key)
        return response.get('data', []) if response else []
        
    def get_genre_tracks_by_id(self, genre_id, limit=30):
        """Get tracks for a specific genre ID"""
        if not genre_id:
            return []
        
        try:
            genre_id = int(genre_id)
            
            if genre_id == 0:
                return self.get_top_charts(limit=limit)
                
            params = {'limit': limit}
            cache_key = f"deezer:genre_tracks:{genre_id}:{limit}"
            
            response = self._make_request(f"genre/{genre_id}/tracks", params, cache_key)
            
            if not response or not response.get('data'):
                genre_info = self.get_genre(genre_id)
                if genre_info and 'name' in genre_info:
                    genre_name = genre_info['name']
                    search_params = {'q': f'genre:"{genre_name}"', 'limit': limit}
                    return self._make_request("search/track", search_params)['data']
            
            return response.get('data', []) if response else []
        except (ValueError, TypeError) as e:
            logger.error(f"Error retrieving tracks for genre ID {genre_id}: {str(e)}")
            return []

    def _get_genre_id_by_name(self, genre_name):
        """Convert a genre name to its ID by matching against available genres"""
        genres = self.get_genres()
        for genre in genres:
            if genre.get('name', '').lower() == genre_name.lower():
                return genre.get('id')
                
        for genre in genres:
            if genre_name.lower() in genre.get('name', '').lower():
                return genre.get('id')
                
        return 132

    def get_artist_genres(self, artist_id):
        """Get genres associated with an artist"""
        artist = self.get_artist(artist_id)
        if not artist:
            return []
            
        albums = self.get_artist_albums(artist_id, limit=5)
        genres = []
        
        for album in albums:
            album_detail = self.get_album(album.get('id'))
            if album_detail and 'genres' in album_detail:
                album_genres = album_detail.get('genres', {}).get('data', [])
                for genre in album_genres:
                    genres.append(genre.get('name'))
                    
        if not genres:
            common_genres = ["pop", "rock", "hip hop", "electronic", "jazz", "r&b", "classical"]
            return [random.choice(common_genres)]
            
        return list(set(genres))

    def get_top_charts(self, limit=50):
        """Get the top charting tracks from Deezer"""
        params = {'limit': limit}
        cache_key = f"deezer:top_charts:{limit}"
        response = self._make_request("chart/0/tracks", params, cache_key, cache_time=7200)
        return response.get('data', []) if response else []
        
    def get_top_albums(self, limit=25):
        """Get the top albums from Deezer"""
        params = {'limit': limit}
        cache_key = f"deezer:top_albums:{limit}"
        response = self._make_request("chart/0/albums", params, cache_key, cache_time=7200)
        return response.get('data', []) if response else []
        
    def get_new_releases(self, limit=50):
        """Get new album releases from Deezer"""
        params = {'limit': limit}
        cache_key = f"deezer:new_releases:{limit}"
        response = self._make_request("editorial/0/releases", params, cache_key, cache_time=7200)
        return response.get('data', []) if response else []

    def clear_cache_for_track(self, track_id):
        """Clear cache for a specific track"""
        cache_key = f"deezer:track:{track_id}"
        cache.delete(cache_key)
        
        # Also clear related cache entries
        cache.delete(f"deezer:track_related:{track_id}:10")
        return True


deezer_client = DeezerClient()