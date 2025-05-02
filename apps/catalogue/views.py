import requests
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.deezer.client import deezer_client
from django.conf import settings

class SearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        q = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))
        if not q:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)
        artists = deezer_client.search_artists(q, limit=limit).get('data', [])
        tracks = deezer_client.search_tracks(q, limit=limit).get('data', [])
        return Response({'artists': artists, 'tracks': tracks})

class ArtistDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, artist_id):
        art = deezer_client.get_artist(artist_id)
        if not art:
            return Response({'error': 'Artist not found'}, status=status.HTTP_404_NOT_FOUND)
        albums = deezer_client.get_artist_albums(artist_id).get('data', [])
        top = deezer_client.get_artist_top_tracks(artist_id).get('data', [])
        return Response({'artist': art, 'albums': albums, 'top_tracks': top})

class AlbumDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, album_id):
        alb = deezer_client.get_album(album_id)
        if not alb:
            return Response({'error': 'Album not found'}, status=status.HTTP_404_NOT_FOUND)
        tracks = deezer_client.get_album_tracks(album_id).get('data', [])
        return Response({'album': alb, 'tracks': tracks})

class TrackDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, track_id):
        tr = deezer_client.get_track(track_id)
        if not tr:
            return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
        related = deezer_client.get_related_tracks(track_id).get('data', [])
        return Response({'track': tr, 'related_tracks': related})

class StreamTrackView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, track_id):
        tr = deezer_client.get_track(track_id)
        if not tr or 'preview' not in tr:
            return Response({'error': 'Track preview not available'}, status=status.HTTP_404_NOT_FOUND)
        url = tr['preview']
        if settings.USE_DIRECT_AUDIO_REDIRECT:
            return Response({'preview_url': url})
        try:
            resp = requests.get(url, stream=True, timeout=10)
            resp.raise_for_status()
            streamer = StreamingHttpResponse(resp.raw, content_type=resp.headers.get('Content-Type', 'audio/mpeg'), status=resp.status_code)
            for h in ['Content-Length', 'Accept-Ranges']:
                if h in resp.headers:
                    streamer[h] = resp.headers[h]
            return streamer
        except:
            return Response({'error': 'Failed to stream track preview'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
