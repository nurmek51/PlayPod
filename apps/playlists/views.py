from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Max
import random

from apps.deezer.client import deezer_client
from apps.accounts.models import PlaybackHistory
from apps.accounts.serializers import PlaybackHistorySerializer
from .models import Playlist, PlaylistTrack, Queue, QueueTrack
from .serializers import (
    PlaylistSerializer, PlaylistDetailSerializer,
    PlaylistTrackSerializer, PlaylistTrackAddSerializer,
    QueueSerializer, QueueTrackSerializer, QueueTrackAddSerializer,
    QueueUpdateSerializer, RecommendedPlaylistSerializer
)
from .permissions import IsPlaylistOwner, IsPlaylistOwnerOrReadOnly, IsQueueOwner
from .tasks import generate_radio_recommendations, generate_recommended_playlists
from apps.core.cache import get_cached_data, cache_data


RECOMMENDATION_CACHE = {}

class PlaylistViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing playlists.
    """
    permission_classes = [IsAuthenticated, IsPlaylistOwnerOrReadOnly]

    def get_queryset(self):
        """Get playlists visible to the user (public ones and user's own)"""
        user = self.request.user
        return Playlist.objects.filter(Q(is_public=True) | Q(user=user))

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return PlaylistSerializer
        if self.action == 'list' and self.request.query_params.get('me') == 'true':
            return PlaylistSerializer
        if self.action == 'list':
            return PlaylistSerializer
        return PlaylistDetailSerializer

    def perform_create(self, serializer):
        """Create a new playlist for the authenticated user"""
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        List playlists.
        Use ?me=true query parameter to filter for current user's playlists only.
        """
        if request.query_params.get('me') == 'true':
            self.queryset = Playlist.objects.filter(user=request.user)
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        """
        List all tracks in a playlist.
        """
        playlist = self.get_object()
        tracks = PlaylistTrack.objects.filter(playlist=playlist).order_by('position')
        serializer = PlaylistTrackSerializer(tracks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPlaylistOwner])
    def add_track(self, request, pk=None):
        """
        Add a track to a playlist.
        ---
        request_body:
          type: object
          required:
            - track_id
          properties:
            track_id:
              type: integer
              description: Deezer track ID to add
        responses:
          201:
            description: Track added successfully
          400:
            description: Track already in playlist
          404:
            description: Track not found
        """
        pl = self.get_object()
        ser = PlaylistTrackAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tid = ser.validated_data['track_id']
        if PlaylistTrack.objects.filter(playlist=pl, track_id=tid).exists():
            return Response({'detail': 'Track already in playlist'}, status=status.HTTP_400_BAD_REQUEST)
        data = deezer_client.get_track(tid)
        if not data or data.get('error'):
            return Response({'detail': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
        art = data.get('artist') or {}
        alb = data.get('album') or {}
        pos = PlaylistTrack.objects.filter(playlist=pl).count()
        item = PlaylistTrack.objects.create(
            playlist=pl,
            track_id=str(data.get('id')),
            artist_id=str(art.get('id', '')),
            track_title=data.get('title', ''),
            artist_name=art.get('name', ''),
            album_title=alb.get('title', ''),
            album_cover=alb.get('cover_medium') or alb.get('cover') or '',
            duration=data.get('duration', 0),
            position=pos
        )
        return Response(PlaylistTrackSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPlaylistOwner])
    def add_tracks(self, request, pk=None):
        """
        Add multiple tracks to a playlist.
        ---
        request_body:
          type: object
          required:
            - tracks
          properties:
            tracks:
              type: array
              items:
                type: integer
              description: List of Deezer track IDs to add
        responses:
          201:
            description: Tracks added successfully
          400:
            description: Invalid request format
        """
        pl = self.get_object()
        arr = request.data.get('tracks', [])
        if not isinstance(arr, list):
            return Response({'detail': 'tracks must be a list'}, status=status.HTTP_400_BAD_REQUEST)
        added = 0
        pos = PlaylistTrack.objects.filter(playlist=pl).count()
        with transaction.atomic():
            for tid in arr:
                try:
                    tid = int(tid)
                except:
                    continue
                if PlaylistTrack.objects.filter(playlist=pl, track_id=tid).exists():
                    continue
                data = deezer_client.get_track(tid)
                if not data or data.get('error'):
                    continue
                art = data.get('artist') or {}
                alb = data.get('album') or {}
                PlaylistTrack.objects.create(
                    playlist=pl,
                    track_id=str(data.get('id')),
                    artist_id=str(art.get('id', '')),
                    track_title=data.get('title', ''),
                    artist_name=art.get('name', ''),
                    album_title=alb.get('title', ''),
                    album_cover=alb.get('cover_medium') or alb.get('cover') or '',
                    duration=data.get('duration', 0),
                    position=pos
                )
                pos += 1
                added += 1
        return Response({'added_count': added, 'total': pos}, status=status.HTTP_201_CREATED)
        
    @action(detail=True, methods=['delete'])
    def remove_track(self, request, pk=None):
        """
        Remove a track from a playlist.
        ---
        parameters:
          - name: track_id
            in: query
            required: true
            schema:
              type: string
            description: Deezer track ID to remove
        responses:
          204:
            description: Track removed successfully
          400:
            description: track_id parameter missing
          404:
            description: Track not found in playlist
        """
        playlist = self.get_object()
        track_id = request.query_params.get('track_id')
        if not track_id:
            return Response({'detail': 'track_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        track = get_object_or_404(PlaylistTrack, playlist=playlist, track_id=track_id)
        position = track.position
        track.delete()
        
        with transaction.atomic():
            tracks_to_update = PlaylistTrack.objects.filter(
                playlist=playlist, 
                position__gt=position
            )
            for track in tracks_to_update:
                track.position -= 1
                track.save()
                
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        """
        Start playing a playlist by adding its tracks to the user's queue.
        ---
        request_body:
          type: object
          properties:
            position:
              type: integer
              description: Position to start playing from (defaults to 0)
            shuffle:
              type: boolean
              description: Whether to shuffle the playlist tracks (defaults to false)
        responses:
          200:
            description: Playlist queued successfully
          400:
            description: Playlist is empty
          404:
            description: Playlist not found
        """
        playlist = self.get_object()
        start_position = request.data.get('position', 0)
        shuffle = request.data.get('shuffle', False)
        
        try:
            start_position = int(start_position)
        except ValueError:
            start_position = 0
            
        tracks = PlaylistTrack.objects.filter(playlist=playlist).order_by('position')
        
        if not tracks:
            return Response({'detail': 'Playlist is empty'}, status=status.HTTP_400_BAD_REQUEST)
            
        if start_position >= tracks.count():
            start_position = 0
            
        queue, _ = Queue.objects.get_or_create(user=request.user)
        QueueTrack.objects.filter(queue=queue).delete()
        
        if shuffle:
            tracks_to_queue = list(tracks)
            start_track = tracks_to_queue[start_position]
            tracks_to_queue.pop(start_position)
            random.shuffle(tracks_to_queue)
            tracks_to_queue.insert(0, start_track)
            
            position_in_queue = 0
            for track in tracks_to_queue:
                QueueTrack.objects.create(
                    queue=queue,
                    track_id=track.track_id,
                    artist_id=track.artist_id,
                    track_title=track.track_title,
                    artist_name=track.artist_name,
                    album_title=track.album_title,
                    album_cover=track.album_cover,
                    duration=track.duration,
                    position=position_in_queue
                )
                position_in_queue += 1
        else:
            position_in_queue = 0
            for track in tracks[start_position:]:
                QueueTrack.objects.create(
                    queue=queue,
                    track_id=track.track_id,
                    artist_id=track.artist_id,
                    track_title=track.track_title,
                    artist_name=track.artist_name,
                    album_title=track.album_title,
                    album_cover=track.album_cover,
                    duration=track.duration,
                    position=position_in_queue
                )
                position_in_queue += 1
            
        if position_in_queue > 0:
            first_track = QueueTrack.objects.filter(queue=queue).order_by('position').first()
            queue.current_track_id = first_track.track_id
            queue.current_position = 0
            queue.save()
            
            PlaybackHistory.objects.create(
                user=request.user,
                track_id=first_track.track_id,
                artist_id=first_track.artist_id,
                track_title=first_track.track_title,
                artist_name=first_track.artist_name,
                album_title=first_track.album_title,
                album_cover=first_track.album_cover,
                position=0
            )
            
        return Response(QueueSerializer(queue).data)
        
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """
        Get personalized track recommendations based on listening history.
        ---
        responses:
          200:
            description: List of recommended tracks
        """
        cache_key = f"user_recommendations_{request.user.id}"
        cached_recommendations = get_cached_data(cache_key)
        
        if cached_recommendations:
            return Response(cached_recommendations)
            
        tracks = []
        user_playback_history = PlaybackHistory.objects.filter(user=request.user).order_by('-timestamp')[:20]
        
        if user_playback_history:
            genres = []
            artist_ids = []
            track_ids = []
            
            for item in user_playback_history:
                if item.artist_id and item.artist_id not in artist_ids:
                    artist_ids.append(item.artist_id)
                if item.track_id and item.track_id not in track_ids:
                    track_ids.append(item.track_id)
            
            if track_ids:
                tracks = deezer_client.get_track_recommendations(track_ids[0])
            
            if not tracks and artist_ids:
                for artist_id in artist_ids[:5]:
                    artist_tracks = deezer_client.get_artist_top_tracks(artist_id, limit=3)
                    if artist_tracks:
                        tracks.extend(artist_tracks)
                        if len(tracks) >= 10:
                            break
            
            if not tracks and artist_ids:
                for artist_id in artist_ids[:3]:
                    related_artists = deezer_client.get_related_artists(artist_id)
                    if related_artists:
                        for related_artist in related_artists[:3]:
                            related_id = related_artist.get('id')
                            if related_id:
                                artist_tracks = deezer_client.get_artist_top_tracks(related_id, limit=3)
                                if artist_tracks:
                                    tracks.extend(artist_tracks)
                                    if len(tracks) >= 10:
                                        break
            
            if not tracks:
                tracks = deezer_client.get_top_charts(limit=10)
            
        else:
            tracks = deezer_client.get_top_charts(limit=10)
        
        if tracks:
            cache_data(cache_key, tracks, timeout=3600)
            
        return Response(tracks)
    
    @action(detail=False, methods=['post'])
    def play_recommendation(self, request):
        """
        Start playing a recommended track and add similar tracks to the queue.
        ---
        request_body:
          type: object
          required:
            - track_id
          properties:
            track_id:
              type: string
              description: Deezer track ID to play
        responses:
          200:
            description: Track queued successfully with similar tracks
          400:
            description: track_id parameter missing
          404:
            description: Track not found
        """
        track_id = request.data.get('track_id')
        
        if not track_id:
            return Response({"detail": "track_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        track_data = deezer_client.get_track(track_id)
        if not track_data:
            return Response({"detail": "Track not found"}, status=status.HTTP_404_NOT_FOUND)
            
        queue = Queue.objects.filter(user=request.user).first()
        if not queue:
            queue = Queue.objects.create(user=request.user)
            
        QueueTrack.objects.filter(queue=queue).delete()
        
        artist_name = track_data.get('artist', {}).get('name', '')
        album_title = track_data.get('album', {}).get('title', '')
        album_cover = track_data.get('album', {}).get('cover', '')
        artist_id = track_data.get('artist', {}).get('id', '')
        
        queue_track = QueueTrack.objects.create(
            queue=queue,
            track_id=track_id,
            track_title=track_data.get('title', ''),
            artist_name=artist_name,
            artist_id=artist_id,
            album_title=album_title,
            album_cover=album_cover,
            duration=track_data.get('duration', 0),
            position=0
        )
        
        queue.current_track_id = track_id
        queue.save()
        
        similar_tracks = deezer_client.get_track_recommendations(track_id)
        
        if similar_tracks:
            for i, track in enumerate(similar_tracks[:20]):
                if str(track.get('id')) != str(track_id):
                    artist = track.get('artist', {})
                    album = track.get('album', {})
                    
                    QueueTrack.objects.create(
                        queue=queue,
                        track_id=track.get('id'),
                        track_title=track.get('title', ''),
                        artist_name=artist.get('name', ''),
                        artist_id=artist.get('id', ''),
                        album_title=album.get('title', ''),
                        album_cover=album.get('cover', ''),
                        duration=track.get('duration', 0),
                        position=i + 1
                    )
                    
        serializer = QueueSerializer(queue)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """
        Generate a new playlist based on a specified genre.
        ---
        request_body:
          type: object
          required:
            - genre
          properties:
            genre:
              type: string
              description: Name of the genre
            genre_id:
              type: integer
              description: Optional Deezer genre ID
            name:
              type: string
              description: Optional custom name for the playlist
        responses:
          201:
            description: Playlist generated successfully
          400:
            description: Missing genre information
          404:
            description: No tracks found for genre
        """
        genre = request.data.get('genre')
        genre_id = request.data.get('genre_id')
        name = request.data.get('name')
        
        if not (genre or genre_id):
            return Response({'detail': 'Either genre or genre_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if genre and not genre_id:
            try:
                int_genre = int(genre)
                genre_id = int_genre
                genre = None
            except (ValueError, TypeError):
                pass
        
        genre_info = None
        genre_name = None
        if genre_id:
            genre_info = deezer_client.get_genre(genre_id)
            if genre_info and 'name' in genre_info:
                genre_name = genre_info['name']
        
        if not name:
            if genre_name:
                name = f"{genre_name} Mix"
            elif genre:
                name = f"{genre.title()} Mix"
            else:
                name = "Genre Mix"
        
        tracks = []
        if genre_id:
            tracks = deezer_client.get_genre_tracks_by_id(genre_id, limit=30)
        else:
            tracks = deezer_client.get_genre_tracks(genre, limit=30)
        
        if not tracks:
            if genre_name:
                search_query = f'genre:"{genre_name}"'
                search_results = deezer_client.search_tracks(search_query, limit=30)
                if search_results:
                    tracks = search_results
        
        if not tracks:
            return Response({'detail': 'No tracks found for genre'}, status=status.HTTP_404_NOT_FOUND)
        

        description = f"A playlist of {genre_name or genre or 'genre'} music"
        playlist = Playlist.objects.create(
            user=request.user,
            name=name,
            description=description
        )
        
        for i, track in enumerate(tracks):
            artist = track.get('artist', {})
            album = track.get('album', {})
            genre_info = track.get('genre', {})
            genre_name = genre_info.get('name', '') if isinstance(genre_info, dict) else ''
            track_genre_id = genre_info.get('id', '') if isinstance(genre_info, dict) else ''
            
            PlaylistTrack.objects.create(
                playlist=playlist,
                track_id=track.get('id'),
                track_title=track.get('title', ''),
                artist_name=artist.get('name', ''),
                artist_id=artist.get('id', ''),
                album_title=album.get('title', ''),
                album_cover=album.get('cover', ''),
                genre=genre_name,
                genre_id=track_genre_id,
                duration=track.get('duration', 0),
                position=i
            )
        
        serializer = PlaylistDetailSerializer(playlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class QueueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing the user's playback queue.
    """
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated, IsQueueOwner]

    def get_queryset(self):
        """Get the queue for the current user"""
        return Queue.objects.filter(user=self.request.user)

    def get_object(self):
        """Get or create queue for the current user"""
        q, _ = Queue.objects.get_or_create(user=self.request.user)
        return q

    def get_serializer_class(self):
        """Return appropriate serializer based on request method"""
        if self.request.method == 'PATCH':
            return QueueUpdateSerializer
        return QueueSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def enqueue(self, request):
        """
        Add a track to the end of the queue.
        ---
        request_body:
          type: object
          required:
            - track_id
          properties:
            track_id:
              type: integer
              description: Deezer track ID to add
        responses:
          201:
            description: Track added to queue successfully
          400:
            description: Track already in queue
          404:
            description: Track not found
        """
        q = self.get_object()
        ser = QueueTrackAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tid = ser.validated_data['track_id']
        if QueueTrack.objects.filter(queue=q, track_id=tid).exists():
            return Response({'detail': 'Already in queue'}, status=status.HTTP_400_BAD_REQUEST)
        data = deezer_client.get_track(tid)
        if not data or data.get('error'):
            return Response({'detail': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
        art = data.get('artist') or {}
        alb = data.get('album') or {}
        pos = QueueTrack.objects.filter(queue=q).count()
        qt = QueueTrack.objects.create(
            queue=q,
            track_id=str(data.get('id')),
            artist_id=str(art.get('id', '')),
            track_title=data.get('title', ''),
            artist_name=art.get('name', ''),
            album_title=alb.get('title', ''),
            album_cover=alb.get('cover_medium') or alb.get('cover') or '',
            duration=data.get('duration', 0),
            position=pos
        )
        
        if not q.current_track_id:
            q.current_track_id = qt.track_id
            q.current_position = qt.position
            q.save()
            
        return Response(QueueTrackSerializer(qt).data, status=status.HTTP_201_CREATED)
        
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def tracks(self, request):
        """
        List all tracks in the user's queue.
        ---
        responses:
          200:
            description: List of tracks in queue
        """
        queue = self.get_object()
        tracks = QueueTrack.objects.filter(queue=queue).order_by('position')
        serializer = QueueTrackSerializer(tracks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def history(self, request):
        """
        Get user's playback history.
        ---
        responses:
          200:
            description: List of recently played tracks
        """
        history = PlaybackHistory.objects.filter(user=request.user).order_by('-timestamp')[:50]
        serializer = PlaybackHistorySerializer(history, many=True, context={'request': request})
        return Response(serializer.data)
        
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def stream(self, request):
        """
        Start streaming a track, adding it to queue if not present.
        ---
        request_body:
          type: object
          properties:
            track_id:
              type: string
              description: Deezer track ID to stream
        responses:
          200:
            description: Track streaming started
          400:
            description: No current track
          404:
            description: Track not found
        """
        queue = self.get_object()
        track_id = request.data.get('track_id')
        
        if not track_id:
            if not queue.current_track_id:
                return Response({'detail': 'No current track'}, status=status.HTTP_400_BAD_REQUEST)
            track_id = queue.current_track_id
        
        try:
            track = QueueTrack.objects.get(queue=queue, track_id=track_id)
            
            queue.current_track_id = track.track_id
            queue.current_position = track.position
            queue.save()
            
            PlaybackHistory.objects.create(
                user=request.user,
                track_id=track.track_id,
                artist_id=track.artist_id,
                track_title=track.track_title,
                artist_name=track.artist_name,
                album_title=track.album_title,
                album_cover=track.album_cover,
                position=0
            )
            
            return Response(QueueTrackSerializer(track).data)
            
        except QueueTrack.DoesNotExist:
            data = deezer_client.get_track(track_id)
            if not data or data.get('error'):
                return Response({'detail': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
                
            art = data.get('artist') or {}
            alb = data.get('album') or {}
            pos = QueueTrack.objects.filter(queue=queue).count()
            
            track = QueueTrack.objects.create(
                queue=queue,
                track_id=str(data.get('id')),
                artist_id=str(art.get('id', '')),
                track_title=data.get('title', ''),
                artist_name=art.get('name', ''),
                album_title=alb.get('title', ''),
                album_cover=alb.get('cover_medium') or alb.get('cover') or '',
                duration=data.get('duration', 0),
                position=pos
            )
            
            queue.current_track_id = track.track_id
            queue.current_position = track.position
            queue.save()
            
            PlaybackHistory.objects.create(
                user=request.user,
                track_id=track.track_id,
                artist_id=track.artist_id,
                track_title=track.track_title,
                artist_name=track.artist_name,
                album_title=track.album_title,
                album_cover=track.album_cover,
                position=0
            )
            
            return Response(QueueTrackSerializer(track).data)
        
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def next(self, request):
        """
        Skip to next track in queue.
        ---
        responses:
          200:
            description: Moved to next track successfully
          400:
            description: No current track
          404:
            description: End of queue reached or track not found
        """
        queue = self.get_object()
        if not queue.current_track_id:
            return Response({'detail': 'No current track'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            current_track = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
            
            PlaybackHistory.objects.create(
                user=request.user,
                track_id=current_track.track_id,
                artist_id=current_track.artist_id,
                track_title=current_track.track_title,
                artist_name=current_track.artist_name,
                album_title=current_track.album_title,
                album_cover=current_track.album_cover
            )
            
            next_track = QueueTrack.objects.filter(
                queue=queue, 
                position__gt=current_track.position
            ).order_by('position').first()
            
            if next_track:
                queue.current_track_id = next_track.track_id
                queue.current_position = next_track.position
                queue.save()
                return Response(QueueTrackSerializer(next_track).data)
            else:
                return Response({'detail': 'End of queue reached'}, status=status.HTTP_404_NOT_FOUND)
                
        except QueueTrack.DoesNotExist:
            return Response({'detail': 'Current track not found in queue'}, status=status.HTTP_404_NOT_FOUND)
                
    @action(detail=False, methods=['post'])
    def previous(self, request):
        """
        Go back to previous track in queue.
        ---
        responses:
          200:
            description: Moved to previous track successfully
          400:
            description: No current track
          404:
            description: No previous track or track not found
        """
        queue = self.get_object()
        if not queue.current_track_id:
            return Response({'detail': 'No current track'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            current_track = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
            
            if current_track.position > 0:
                prev_track = QueueTrack.objects.filter(
                    queue=queue, 
                    position=current_track.position - 1
                ).first()
                
                if prev_track:
                    queue.current_track_id = prev_track.track_id
                    queue.current_position = prev_track.position
                    queue.save()
                    
                    PlaybackHistory.objects.create(
                        user=request.user,
                        track_id=prev_track.track_id,
                        artist_id=prev_track.artist_id,
                        track_title=prev_track.track_title,
                        artist_name=prev_track.artist_name,
                        album_title=prev_track.album_title,
                        album_cover=prev_track.album_cover,
                        position=0
                    )
                    
                    return Response(QueueTrackSerializer(prev_track).data)
                
            return Response(QueueTrackSerializer(current_track).data)
                
        except QueueTrack.DoesNotExist:
            return Response({'detail': 'Current track not found in queue'}, 
                          status=status.HTTP_404_NOT_FOUND)
                          
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """
        Clear all tracks from the queue.
        ---
        responses:
          204:
            description: Queue cleared successfully
        """
        queue = self.get_object()
        QueueTrack.objects.filter(queue=queue).delete()
        queue.current_track_id = None
        queue.current_position = 0
        queue.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    @action(detail=False, methods=['get'])
    def current(self, request):
        """
        Get current track information.
        ---
        responses:
          200:
            description: Current track information
          404:
            description: No current track
        """
        queue = self.get_object()
        if not queue.current_track_id:
            return Response({'detail': 'No current track'}, status=status.HTTP_404_NOT_FOUND)
            
        try:
            current_track = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
            return Response(QueueTrackSerializer(current_track).data)
        except QueueTrack.DoesNotExist:
            queue.current_track_id = None
            queue.save()
            return Response({'detail': 'Current track not found in queue'}, 
                          status=status.HTTP_404_NOT_FOUND)
                          
    @action(detail=False, methods=['post'])
    def position(self, request):
        """
        Jump to a specific position in the queue.
        ---
        request_body:
          type: object
          required:
            - position
          properties:
            position:
              type: integer
              description: Position in queue to jump to
        responses:
          200:
            description: Jumped to position successfully
          400:
            description: Invalid position parameter
          404:
            description: No track at specified position
        """
        queue = self.get_object()
        position = request.data.get('position')
        
        if position is None:
            return Response({'detail': 'position is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            position = int(position)
        except ValueError:
            return Response({'detail': 'position must be an integer'}, 
                          status=status.HTTP_400_BAD_REQUEST)
                          
        track = QueueTrack.objects.filter(queue=queue, position=position).first()
        if not track:
            return Response({'detail': 'Track at position not found'}, 
                          status=status.HTTP_404_NOT_FOUND)
                          
        if queue.current_track_id and queue.current_track_id != track.track_id:
            try:
                current_track = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
                PlaybackHistory.objects.create(
                    user=request.user,
                    track_id=current_track.track_id,
                    artist_id=current_track.artist_id,
                    track_title=current_track.track_title,
                    artist_name=current_track.artist_name,
                    album_title=current_track.album_title,
                    album_cover=current_track.album_cover,
                    position=50
                )
            except QueueTrack.DoesNotExist:
                pass
        
        queue.current_track_id = track.track_id
        queue.current_position = position
        queue.save()
        
        PlaybackHistory.objects.create(
            user=request.user,
            track_id=track.track_id,
            artist_id=track.artist_id,
            track_title=track.track_title,
            artist_name=track.artist_name,
            album_title=track.album_title,
            album_cover=track.album_cover,
            position=0
        )
        
        return Response(QueueTrackSerializer(track).data)
        
    @action(detail=False, methods=['post'])
    def shuffle(self, request):
        """
        Shuffle tracks in the queue.
        ---
        responses:
          200:
            description: Queue shuffled successfully
          400:
            description: Queue is empty
        """
        queue = self.get_object()
        
        try:
            if queue.current_track_id:
                current_track = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
                other_tracks = list(QueueTrack.objects.filter(queue=queue).exclude(id=current_track.id))
                
                random.shuffle(other_tracks)
                
                with transaction.atomic():
                    current_track.position = 0
                    current_track.save()
                    
                    for i, track in enumerate(other_tracks, 1):
                        track.position = i
                        track.save()
            else:
                tracks = list(QueueTrack.objects.filter(queue=queue))
                random.shuffle(tracks)
                
                with transaction.atomic():
                    for i, track in enumerate(tracks):
                        track.position = i
                        track.save()
                        
                if tracks:
                    queue.current_track_id = tracks[0].track_id
                    queue.current_position = 0
                    queue.save()
                
            return Response(QueueSerializer(queue).data)
            
        except QueueTrack.DoesNotExist:
            tracks = list(QueueTrack.objects.filter(queue=queue))
            if not tracks:
                return Response({'detail': 'Queue is empty'}, status=status.HTTP_400_BAD_REQUEST)
                
            random.shuffle(tracks)
            with transaction.atomic():
                for i, track in enumerate(tracks):
                    track.position = i
                    track.save()
            
            queue.current_track_id = tracks[0].track_id
            queue.current_position = 0
            queue.save()
            
            return Response(QueueSerializer(queue).data)
