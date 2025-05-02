from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from apps.deezer.client import deezer_client
from .models import Favorite, PlaybackHistory
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    PublicUserSerializer,
    FavoriteSerializer,
    FavoriteCreateSerializer,
    PlaybackHistorySerializer,
)

User = get_user_model()

class MeView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class MeUpdateView(UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class UserPublicView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

class FavoriteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def add(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tid = serializer.validated_data['track_id']
        if Favorite.objects.filter(user=request.user, track_id=tid).exists():
            return Response({'detail': 'Already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        data = deezer_client.get_track(tid)
        if not data:
            return Response({'detail': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
        artist = data.get('artist', {})
        album  = data.get('album', {})
        fav = Favorite.objects.create(
            user=request.user,
            track_id   = data['id'],
            artist_id  = artist.get('id'),
            track_title= data.get('title'),
            artist_name= artist.get('name'),
            album_title= album.get('title', ''),
            album_cover= album.get('cover_medium', '') or album.get('cover', ''),
            duration   = data.get('duration', 0)
        )
        return Response(FavoriteSerializer(fav).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def remove(self, request):
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tid = serializer.validated_data['track_id']
        fav = get_object_or_404(Favorite, user=request.user, track_id=tid)
        fav.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PlaybackHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PlaybackHistorySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PlaybackHistory.objects.filter(user=self.request.user)
