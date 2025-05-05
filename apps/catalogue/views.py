import requests
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.deezer.client import deezer_client
from django.conf import settings
from apps.accounts.models import PlaybackHistory
from apps.catalogue.models import Artist
import uuid
import logging


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

        artists = deezer_client.search_artists(q, limit=limit)
        tracks = deezer_client.search_tracks(q, limit=limit)
        albums = deezer_client.search_albums(q, limit=limit)

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
          type: integer or string
        description: Deezer artist ID or artist UUID
    responses:
      200:
        description: Artist details, including albums and top tracks
      404:
        description: Artist not found
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, artist_id):
        # Try to get the artist directly from the database first (as UUID)
        try:
            # Check if artist_id could be a UUID
            try:
                uuid_obj = uuid.UUID(str(artist_id))
                artist_obj = Artist.objects.filter(id=uuid_obj).first()
                if artist_obj:
                    # Use the Deezer ID from the database
                    artist_id = artist_obj.deezer_id
            except (ValueError, TypeError):
                # Not a valid UUID, continue with numeric ID
                pass
                
            # Get the artist from Deezer API
            artist = deezer_client.get_artist(artist_id)
            if not artist:
                return Response({'error': 'Artist not found'}, status=status.HTTP_404_NOT_FOUND)

            # The get_artist_albums and get_artist_top_tracks methods already return lists, 
            # not dictionaries with 'data' attribute
            albums = deezer_client.get_artist_albums(artist_id)
            top_tracks = deezer_client.get_artist_top_tracks(artist_id)

            return Response({
                'artist': artist,
                'albums': albums,
                'top_tracks': top_tracks
            })
        except Exception as e:
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Artist detail error: {str(e)}\n{traceback.format_exc()}")
            return Response({'error': f'Error retrieving artist: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        try:
            album = deezer_client.get_album(album_id)
            if not album:
                return Response({'error': 'Album not found'}, status=status.HTTP_404_NOT_FOUND)

            # get_album_tracks already returns a list
            tracks = deezer_client.get_album_tracks(album_id)

            return Response({
                'album': album,
                'tracks': tracks
            })
        except Exception as e:
            logger.error(f"Album detail error: {str(e)}")
            return Response({'error': f'Error retrieving album: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        try:
            track = deezer_client.get_track(track_id)
            if not track:
                return Response({'error': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)

            # get_related_tracks already returns a list
            related_tracks = deezer_client.get_related_tracks(track_id)

            return Response({
                'track': track,
                'related_tracks': related_tracks
            })
        except Exception as e:
            logger.error(f"Track detail error: {str(e)}")
            return Response({'error': f'Error retrieving track: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        # First try to get the track info from Deezer
        track = deezer_client.get_track(track_id)
        if not track or 'preview' not in track:
            return Response({'error': 'Track preview not available'}, status=status.HTTP_404_NOT_FOUND)

        url = track['preview']

        try:
            # Record playback history
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

            # If direct redirect is enabled, just return the URL
            if settings.USE_DIRECT_AUDIO_REDIRECT:
                return Response({'preview_url': url})

            # Prepare headers for Deezer request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://www.deezer.com/',
                'Origin': 'https://www.deezer.com',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            # Try to stream the preview
            try:
                resp = requests.get(url, stream=True, timeout=10, headers=headers)
                resp.raise_for_status()
                
                streamer = StreamingHttpResponse(
                    resp.raw,
                    content_type=resp.headers.get('Content-Type', 'audio/mpeg'),
                    status=resp.status_code
                )

                # Copy relevant headers
                for h in ['Content-Length', 'Accept-Ranges', 'Content-Type']:
                    if h in resp.headers:
                        streamer[h] = resp.headers[h]

                return streamer
                
            except requests.HTTPError as e:
                if e.response.status_code == 403:
                    # If forbidden, the URL might have expired
                    # Refresh the track info and try again
                    deezer_client.clear_cache_for_track(track_id)
                    fresh_track = deezer_client.get_track(track_id, skip_cache=True)
                    
                    if fresh_track and 'preview' in fresh_track:
                        # Return the refreshed URL for client-side redirect
                        return Response({
                            'preview_url': fresh_track['preview'],
                            'refreshed': True,
                            'message': 'Preview URL refreshed due to expiration'
                        })
                    else:
                        return Response(
                            {'error': 'Track preview expired and refresh failed'},
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    raise
                    
        except Exception as e:
            # Fallback to direct URL if streaming fails
            return Response({
                'error': f'Failed to stream track preview: {str(e)}',
                'preview_url': url,
                'fallback': True,
                'message': 'Unable to proxy stream. Try direct playback with this URL.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)