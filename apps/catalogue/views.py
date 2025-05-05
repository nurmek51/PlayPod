import requests
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.deezer.client import deezer_client
from django.conf import settings
from apps.accounts.models import PlaybackHistory


class SearchView(APIView):
    """
    API endpoint for searching for tracks, artists, and albums.
    ---
    parameters:
      - name: q
        in: query
        required: true
        schema:
          type: string
        description: Search query
      - name: limit
        in: query
        schema:
          type: integer
          default: 10
        description: Maximum number of results to return per category
    responses:
      200:
        description: Search results
      400:
        description: Search query is required
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '')
        limit = int(request.query_params.get('limit', 10))

        if not q:
            return Response({'error': 'Search query is required'}, status=status.HTTP_400_BAD_REQUEST)

        artists_data = deezer_client.search_artists(q, limit=limit)
        artists = artists_data.get('data', []) if artists_data else []

        tracks_data = deezer_client.search_tracks(q, limit=limit)
        tracks = tracks_data.get('data', []) if tracks_data else []

        albums_data = deezer_client.search_albums(q, limit=limit)
        albums = albums_data.get('data', []) if albums_data else []

        return Response({
            'artists': artists,
            'tracks': tracks,
            'albums': albums
        })


class GenresView(APIView):
    """
    API endpoint to retrieve all available music genres from Deezer.
    This is useful for generating playlists by genre.
    ---
    responses:
      200:
        description: List of available genres
    """
    permission_classes = [AllowAny]

    def get(self, request):
        genres = deezer_client.get_genres()
        return Response(genres)


class ArtistDetailView(APIView):
    """
    API endpoint to retrieve details about a specific artist.
    ---
    parameters:
      - name: artist_id
        in: path
        required: true
        schema:
          type: integer
        description: Deezer artist ID
    responses:
      200:
        description: Artist details, including albums and top tracks
      404:
        description: Artist not found
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, artist_id):
        artist = deezer_client.get_artist(artist_id)
        if not artist:
            return Response({'error': 'Artist not found'}, status=status.HTTP_404_NOT_FOUND)

        albums_data = deezer_client.get_artist_albums(artist_id)
        albums = albums_data.get('data', []) if albums_data else []

        top_tracks_data = deezer_client.get_artist_top_tracks(artist_id)
        top_tracks = top_tracks_data.get('data', []) if top_tracks_data else []

        return Response({
            'artist': artist,
            'albums': albums,
            'top_tracks': top_tracks
        })


class AlbumDetailView(APIView):
    """
    API endpoint to retrieve details about a specific album.
    ---
    parameters:
      - name: album_id
        in: path
        required: true
        schema:
          type: integer
        description: Deezer album ID
    responses:
      200:
        description: Album details, including tracks
      404:
        description: Album not found
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, album_id):
        album = deezer_client.get_album(album_id)
        if not album:
            return Response({'error': 'Album not found'}, status=status.HTTP_404_NOT_FOUND)

        tracks_data = deezer_client.get_album_tracks(album_id)
        tracks = tracks_data.get('data', []) if tracks_data else []

        return Response({
            'album': album,
            'tracks': tracks
        })


class TrackDetailView(APIView):
    """
    API endpoint to retrieve details about a specific track.
    ---
    parameters:
      - name: track_id
        in: path
        required: true
        schema:
          type: integer
        description: Deezer track ID
    responses:
      200:
        description: Track details with related tracks
      404:
        description: Track not found
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, track_id):
        track = deezer_client.get_track(track_id)
        if not track:
            return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)

        related_data = deezer_client.get_related_tracks(track_id)
        related_tracks = related_data.get('data', []) if related_data else []

        return Response({
            'track': track,
            'related_tracks': related_tracks
        })


class StreamTrackView(APIView):
    """
    API endpoint to stream a track or get its streaming URL.
    Records playback history when a track is streamed.
    ---
    parameters:
      - name: track_id
        in: path
        required: true
        schema:
          type: integer
        description: Deezer track ID
    responses:
      200:
        description: Track streaming URL or streaming response
      404:
        description: Track not found or preview not available
      500:
        description: Streaming error
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, track_id):
        track = deezer_client.get_track(track_id)
        if not track or 'preview' not in track:
            return Response({'error': 'Track preview not available'}, status=status.HTTP_404_NOT_FOUND)

        url = track['preview']

        try:
            PlaybackHistory.objects.create(
                user=request.user,
                track_id=str(track.get('id', '')),
                artist_id=str(track.get('artist', {}).get('id', '')),
                track_title=track.get('title', ''),
                artist_name=track.get('artist', {}).get('name', ''),
                album_title=track.get('album', {}).get('title', ''),
                album_cover=track.get('album', {}).get('cover_medium', ''),
                position=0
            )
        except Exception as e:
            print(f"Failed to save playback history: {str(e)}")

        if settings.USE_DIRECT_AUDIO_REDIRECT:
            return Response({'preview_url': url})

        try:
            resp = requests.get(url, stream=True, timeout=10)
            resp.raise_for_status()
            streamer = StreamingHttpResponse(
                resp.raw,
                content_type=resp.headers.get('Content-Type', 'audio/mpeg'),
                status=resp.status_code
            )

            for h in ['Content-Length', 'Accept-Ranges']:
                if h in resp.headers:
                    streamer[h] = resp.headers[h]

            return streamer
        except Exception as e:
            return Response(
                {'error': f'Failed to stream track preview: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )