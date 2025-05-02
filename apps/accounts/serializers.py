from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Favorite, PlaybackHistory

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'bio']
        read_only_fields = ['id', 'email']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'avatar', 'bio']

class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio']
        read_only_fields = ['id', 'username', 'avatar', 'bio']

class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = [
            'id',
            'track_id',
            'artist_id',
            'track_title',
            'artist_name',
            'album_title',
            'album_cover',
            'duration',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class FavoriteCreateSerializer(serializers.Serializer):
    track_id = serializers.IntegerField()

class PlaybackHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaybackHistory
        fields = [
            'id',
            'track_id',
            'artist_id',
            'track_title',
            'artist_name',
            'album_title',
            'album_cover',
            'position',
            'played_at'
        ]
        read_only_fields = ['id', 'played_at']
