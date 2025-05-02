from rest_framework import viewsets, generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import F
from .models import Playlist, PlaylistTrack, Queue, QueueTrack
from .serializers import (
    PlaylistSerializer,
    PlaylistDetailSerializer,
    PlaylistCreateUpdateSerializer,
    PlaylistTrackSerializer,
    PlaylistTrackAddSerializer,
    QueueSerializer,
    QueueTrackSerializer,
    QueueTrackAddSerializer
)
from .permissions import (
    IsPlaylistOwnerOrReadOnly,
    IsPlaylistOwner,
    IsQueueOwner
)
from apps.deezer.client import deezer_client
import random

class PlaylistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsPlaylistOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']

    def get_queryset(self):
        user = self.request.user
        return (Playlist.objects.filter(user=user) |
                Playlist.objects.filter(is_public=True))

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PlaylistDetailSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return PlaylistCreateUpdateSerializer
        return PlaylistSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPlaylistOwner])
    def add_track(self, request, pk=None):
        playlist = self.get_object()
        ser = PlaylistTrackAddSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tid = ser.validated_data['track_id']
        if PlaylistTrack.objects.filter(playlist=playlist, track_id=tid).exists():
            return Response({'error': 'already in playlist'}, status=status.HTTP_400_BAD_REQUEST)
        d = deezer_client.get_track(tid)
        if not d:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        artist = d['artist']
        album = d['album']
        pos = PlaylistTrack.objects.filter(playlist=playlist).count()
        pt = PlaylistTrack.objects.create(
            playlist=playlist,
            track_id=tid,
            artist_id=str(artist['id']),
            track_title=d['title'],
            artist_name=artist['name'],
            album_title=album['title'],
            album_cover=album['cover_medium'],
            duration=d['duration'],
            position=pos
        )
        return Response(PlaylistTrackSerializer(pt).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsPlaylistOwner])
    def remove_track(self, request, pk=None):
        playlist = self.get_object()
        pos = request.data.get('position')
        if pos is None:
            return Response({'error': 'position required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            pos = int(pos)
        except ValueError:
            return Response({'error': 'position must be integer'}, status=status.HTTP_400_BAD_REQUEST)
        pt = get_object_or_404(PlaylistTrack, playlist=playlist, position=pos)
        pt.delete()
        with transaction.atomic():
            for t in PlaylistTrack.objects.filter(playlist=playlist, position__gt=pos):
                t.position -= 1
                t.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FavoritesPlaylistView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PlaylistDetailSerializer

    def get_object(self):
        user = self.request.user
        playlist = Playlist(id='favorites', user=user, name='My Favorites', is_public=False)
        playlist.tracks = []
        for i, f in enumerate(user.favorite_set.all()):
            pt = PlaylistTrack(
                id=f.id,
                playlist=playlist,
                track_id=f.track_id,
                artist_id=f.artist_id,
                track_title=f.track_title,
                artist_name=f.artist_name,
                album_title=f.album_title,
                album_cover=f.album_cover,
                position=i,
                added_at=f.added_at
            )
            playlist.tracks.append(pt)
        return playlist

class PlaylistRadioView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsPlaylistOwnerOrReadOnly]

    def get(self, request, pk=None):
        pl = get_object_or_404(Playlist, pk=pk)
        if not pl.is_public and pl.user != request.user:
            return Response({'error': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
        pts = pl.tracks.all()[:5]
        if not pts:
            return Response({'error': 'no tracks'}, status=status.HTTP_400_BAD_REQUEST)
        tid = random.choice(pts).track_id
        recs = deezer_client.get_related_tracks(tid, limit=10)
        if not recs:
            return Response({'error': 'no recommendations'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'tracks': recs})

class PlaylistReorderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsPlaylistOwner]

    def post(self, request, pk=None):
        pl = get_object_or_404(Playlist, pk=pk)
        tid = request.data.get('track_id')
        newpos = request.data.get('new_position')
        if not tid or newpos is None:
            return Response({'error': 'track_id & new_position required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            newpos = int(newpos)
        except ValueError:
            return Response({'error': 'new_position must be integer'}, status=status.HTTP_400_BAD_REQUEST)
        pts = PlaylistTrack.objects.filter(playlist=pl)
        count = pts.count()
        if newpos < 0 or newpos >= count:
            return Response({'error': f'new_position out of range 0–{count-1}'}, status=status.HTTP_400_BAD_REQUEST)
        pt = get_object_or_404(PlaylistTrack, playlist=pl, track_id=tid)
        oldpos = pt.position
        if oldpos == newpos:
            return Response(status=status.HTTP_204_NO_CONTENT)
        with transaction.atomic():
            if oldpos < newpos:
                pts.filter(position__gt=oldpos, position__lte=newpos).update(position=F('position') - 1)
            else:
                pts.filter(position__lt=oldpos, position__gte=newpos).update(position=F('position') + 1)
            pt.position = newpos
            pt.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PlaylistBulkActionView(generics.GenericAPIView):
    permission_permissions = [IsAuthenticated, IsPlaylistOwner]

    def post(self, request, pk=None, action=None):
        pl = get_object_or_404(Playlist, pk=pk)
        if action == 'add_tracks':
            tracks_data = request.data.get('tracks', [])
            if not isinstance(tracks_data, list):
                return Response({'error': 'tracks must be list'}, status=status.HTTP_400_BAD_REQUEST)
            added = 0
            pos = pl.tracks.count()
            for item in tracks_data:
                tid = item.get('track_id')
                if not tid or PlaylistTrack.objects.filter(playlist=pl, track_id=tid).exists():
                    continue
                d = deezer_client.get_track(tid)
                if not d:
                    continue
                art = d.get('artist', {})
                alb = d.get('album', {})
                PlaylistTrack.objects.create(
                    playlist=pl,
                    track_id=tid,
                    artist_id=str(art.get('id','')),
                    track_title=d.get('title',''),
                    artist_name=art.get('name',''),
                    album_title=alb.get('title',''),
                    album_cover=alb.get('cover_medium',''),
                    duration=d.get('duration',0),
                    position=pos
                )
                pos += 1
                added += 1
            return Response({'added_count': added, 'total_tracks': pl.tracks.count()}, status=status.HTTP_201_CREATED)
        if action == 'clear':
            PlaylistTrack.objects.filter(playlist=pl).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)

class QueueView(generics.RetrieveAPIView):
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated, IsQueueOwner]

    def get_object(self):
        queue, _ = Queue.objects.get_or_create(user=self.request.user)
        return queue

class QueueActionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, action):
        queue, _ = Queue.objects.get_or_create(user=request.user)

        if action == 'enqueue':
            ser = QueueTrackAddSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            tid = ser.validated_data['track_id']
            if QueueTrack.objects.filter(queue=queue, track_id=tid).exists():
                return Response({'error': 'already in queue'}, status=status.HTTP_400_BAD_REQUEST)
            d = deezer_client.get_track(tid)
            if not d:
                return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
            artist = d['artist']
            album = d['album']
            pos = queue.tracks.count()
            QueueTrack.objects.create(
                queue=queue,
                track_id=tid,
                artist_id=str(artist['id']),
                track_title=d['title'],
                artist_name=artist['name'],
                album_title=album['title'],
                album_cover=album['cover_medium'],
                duration=d['duration'],
                position=pos
            )
            return Response(QueueSerializer(queue).data, status=status.HTTP_201_CREATED)

        if action == 'dequeue':
            pos = request.data.get('position')
            if pos is None:
                return Response({'error': 'position required'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                pos = int(pos)
            except ValueError:
                return Response({'error': 'position must be integer'}, status=status.HTTP_400_BAD_REQUEST)
            qt = get_object_or_404(QueueTrack, queue=queue, position=pos)
            qt.delete()
            with transaction.atomic():
                for t in QueueTrack.objects.filter(queue=queue, position__gt=pos):
                    t.position -= 1
                    t.save()
            return Response(QueueSerializer(queue).data)

        if action == 'clear':
            QueueTrack.objects.filter(queue=queue).delete()
            queue.current_track_id = None
            queue.current_position = 0
            queue.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if action == 'next':
            if queue.current_track_id:
                try:
                    cur = QueueTrack.objects.get(queue=queue, track_id=queue.current_track_id)
                    nxt = QueueTrack.objects.filter(queue=queue, position=cur.position+1).first()
                    if nxt:
                        queue.current_track_id = nxt.track_id
                        queue.current_position = 0
                        queue.save()
                        return Response({'track': deezer_client.get_track(nxt.track_id)}, status=status.HTTP_200_OK)
                except QueueTrack.DoesNotExist:
                    pass
            genre = random.choice(['pop','rock','electronic','hip-hop','rap'])
            recs = deezer_client.search_tracks(query=genre, limit=10)
            if not recs:
                return Response({'error': 'no recommendations'}, status=status.HTTP_404_NOT_FOUND)
            rec = recs[0]
            pos = queue.tracks.count()
            QueueTrack.objects.create(
                queue=queue,
                track_id=rec['id'],
                artist_id=str(rec['artist']['id']),
                track_title=rec['title'],
                artist_name=rec['artist']['name'],
                album_title=rec['album']['title'],
                album_cover=rec['album']['cover_medium'],
                duration=rec['duration'],
                position=pos
            )
            queue.current_track_id = rec['id']
            queue.current_position = 0
            queue.save()
            return Response({'track': rec, 'source': 'recommendation'}, status=status.HTTP_200_OK)

        return Response({'error': 'invalid action'}, status=status.HTTP_400_BAD_REQUEST)