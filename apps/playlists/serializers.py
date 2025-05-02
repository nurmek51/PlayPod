from rest_framework import serializers
from .models import Playlist, PlaylistTrack, Queue, QueueTrack

class PlaylistTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistTrack
        fields = [
            'id','track_id','artist_id','track_title',
            'artist_name','album_title','album_cover',
            'duration','position','added_at'
        ]
        read_only_fields = ['id','added_at','position']

class PlaylistSerializer(serializers.ModelSerializer):
    track_count = serializers.IntegerField(read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Playlist
        fields = [
            'id','name','description','cover_image',
            'is_public','created_at','updated_at',
            'track_count','user_username'
        ]
        read_only_fields = ['id','created_at','updated_at']

class PlaylistDetailSerializer(PlaylistSerializer):
    tracks = PlaylistTrackSerializer(many=True, read_only=True)
    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ['tracks']

class PlaylistCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Playlist
        fields = ['name','description','cover_image','is_public']

class PlaylistTrackAddSerializer(serializers.Serializer):
    track_id = serializers.CharField()

class QueueTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueueTrack
        fields = [
            'id','track_id','artist_id','track_title',
            'artist_name','album_title','album_cover',
            'duration','position','added_at'
        ]
        read_only_fields = ['id','position','added_at']

class QueueSerializer(serializers.ModelSerializer):
    tracks = QueueTrackSerializer(many=True, read_only=True)
    class Meta:
        model = Queue
        fields = ['id','current_track_id','current_position','updated_at','tracks']
        read_only_fields = ['id','updated_at']

class QueueTrackAddSerializer(serializers.Serializer):
    track_id = serializers.CharField()
