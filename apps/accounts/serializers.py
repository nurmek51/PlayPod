from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Favorite, PlaybackHistory
from apps.playlists.serializers import PlaylistSerializer

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm']
        
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})
        return attrs
        
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'avatar', 'bio']
        read_only_fields = ['id', 'email']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'avatar', 'bio']


class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']


class PublicUserSerializer(serializers.ModelSerializer):
    public_playlists = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'bio', 'public_playlists']
        read_only_fields = ['id', 'username', 'avatar', 'bio', 'public_playlists']

    def get_public_playlists(self, user):
        qs = user.playlists.filter(is_public=True).order_by('-created_at')
        return PlaylistSerializer(qs, many=True, context=self.context).data


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['added_at'] = representation.pop('created_at')
        return representation


class FavoriteCreateSerializer(serializers.Serializer):
    track_id = serializers.CharField()
    album_title = serializers.CharField(required=False, allow_blank=True)
    album_cover = serializers.URLField(required=False, allow_blank=True)
    duration = serializers.IntegerField(required=False, default=0)


class PlaybackHistorySerializer(serializers.ModelSerializer):
    in_queue = serializers.SerializerMethodField()
    
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
            'timestamp',
            'in_queue'
        ]
        read_only_fields = ['id', 'timestamp', 'in_queue']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['played_at'] = representation.pop('timestamp')
        return representation
        
    def get_in_queue(self, obj):
        """Check if this track is currently in the user's queue"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
            
        user = request.user
        try:
            queue = user.queue
            return queue.tracks.filter(track_id=obj.track_id).exists()
        except:
            return False