from rest_framework import viewsets, mixins, status, parsers
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from apps.deezer.client import deezer_client
from .models import Favorite, PlaybackHistory
from .serializers import (
    UserSerializer, UserUpdateSerializer, PublicUserSerializer,
    FavoriteSerializer, FavoriteCreateSerializer,
    PlaybackHistorySerializer, AvatarUploadSerializer,
    RegisterSerializer
)

User = get_user_model()

class RegisterView(CreateAPIView):
    """
    API endpoint for registering new users.
    ---
    request_body:
      type: object
      required:
        - username
        - email
        - password
      properties:
        username:
          type: string
        email:
          type: string
          format: email
        password:
          type: string
          format: password
    responses:
      201:
        description: User created successfully
      400:
        description: Invalid registration data
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

class MeView(RetrieveAPIView):
    """
    API endpoint to retrieve the current user's profile.
    ---
    responses:
      200:
        description: Current user's profile
      401:
        description: Authentication required
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class MeUpdateView(UpdateAPIView):
    """
    API endpoint to update the current user's profile.
    ---
    request_body:
      type: object
      properties:
        bio:
          type: string
          description: User's bio/description
    responses:
      200:
        description: Profile updated successfully
      400:
        description: Invalid data
      401:
        description: Authentication required
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user

class AvatarUploadView(APIView):
    """
    API endpoint to upload a user avatar image.
    ---
    consumes:
      - multipart/form-data
    request_body:
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              avatar:
                type: string
                format: binary
    responses:
      200:
        description: Avatar uploaded successfully
      400:
        description: Invalid image
      401:
        description: Authentication required
    """
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data, instance=request.user)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserPublicView(RetrieveAPIView):
    """
    API endpoint to retrieve public user profiles.
    ---
    parameters:
      - name: pk
        in: path
        required: true
        schema:
          type: string
          format: uuid
        description: User ID
    responses:
      200:
        description: User profile (public data only)
      404:
        description: User not found
    """
    queryset = User.objects.all()
    serializer_class = PublicUserSerializer
    permission_classes = [AllowAny]

class FavoriteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint for managing favorite tracks.
    """
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Get favorites for the current user"""
        return Favorite.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def add(self, request):
        """
        Add a track to favorites.
        ---
        request_body:
          type: object
          required:
            - track_id
          properties:
            track_id:
              type: string
              description: Deezer track ID
        responses:
          201:
            description: Track added to favorites
          400:
            description: Track already in favorites
          404:
            description: Track not found
        """
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tid = serializer.validated_data['track_id']
        if Favorite.objects.filter(user=request.user, track_id=tid).exists():
            return Response({'detail': 'Already in favorites'}, status=status.HTTP_400_BAD_REQUEST)
        data = deezer_client.get_track(tid)
        if not data or data.get('error'):
            return Response({'detail': 'Track not found'}, status=status.HTTP_404_NOT_FOUND)
        artist = data.get('artist') or {}
        album = data.get('album') or {}
        fav = Favorite.objects.create(
            user=request.user,
            track_id=str(data.get('id')),
            artist_id=str(artist.get('id', '')),
            track_title=data.get('title', ''),
            artist_name=artist.get('name', ''),
            album_title=album.get('title', ''),
            album_cover=album.get('cover_medium') or album.get('cover') or '',
            duration=data.get('duration', 0)
        )
        return Response(FavoriteSerializer(fav).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def remove(self, request):
        """
        Remove a track from favorites.
        ---
        request_body:
          type: object
          required:
            - track_id
          properties:
            track_id:
              type: string
              description: Deezer track ID
        responses:
          204:
            description: Track removed from favorites
          404:
            description: Track not found in favorites
        """
        serializer = FavoriteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tid = serializer.validated_data['track_id']
        fav = get_object_or_404(Favorite, user=request.user, track_id=tid)
        fav.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class PlaybackHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to retrieve user's playback history.
    ---
    responses:
      200:
        description: User's playback history
      401:
        description: Authentication required
    """
    serializer_class = PlaybackHistorySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PlaybackHistory.objects.filter(user=self.request.user)

class PlaybackHistoryView(APIView):
    """
    API endpoint to retrieve all of a user's playback history.
    ---
    responses:
      200:
        description: Complete playback history
      401:
        description: Authentication required
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        hist = PlaybackHistory.objects.filter(user=request.user).order_by('-timestamp')
        return Response(PlaybackHistorySerializer(hist, many=True).data)
