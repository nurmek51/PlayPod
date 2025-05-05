from rest_framework import serializers
from .models import Playlist, PlaylistTrack, Queue, QueueTrack


class PlaylistSerializer(serializers.ModelSerializer):
    track_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'cover_image',
            'is_public', 'track_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'track_count', 'created_at', 'updated_at']


class PlaylistDetailSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()
    track_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'cover_image',
            'is_public', 'track_count', 'created_at', 'updated_at',
            'tracks'
        ]
        read_only_fields = ['id', 'track_count', 'created_at', 'updated_at', 'tracks']

    def get_tracks(self, obj):
        qs = PlaylistTrack.objects.filter(playlist=obj).order_by('position')
        return PlaylistTrackSerializer(qs, many=True).data


class PlaylistTrackSerializer(serializers.ModelSerializer):
    genre = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = PlaylistTrack
        fields = [
            'id', 'track_id', 'artist_id', 'track_title',
            'artist_name', 'album_title', 'album_cover',
            'duration', 'position', 'added_at', 'genre'
        ]


class PlaylistTrackAddSerializer(serializers.Serializer):
    track_id = serializers.IntegerField()


class QueueSerializer(serializers.ModelSerializer):
    tracks = serializers.SerializerMethodField()

    class Meta:
        model = Queue
        fields = [
            'id', 'current_track_id', 'current_position',
            'updated_at', 'tracks'
        ]
        read_only_fields = ['id', 'updated_at', 'tracks']

    def get_tracks(self, obj):
        return QueueTrackSerializer(
            obj.tracks.order_by('position'),
            many=True
        ).data


class QueueTrackSerializer(serializers.ModelSerializer):
    genre = serializers.CharField(read_only=True, required=False)
    
    class Meta:
        model = QueueTrack
        fields = [
            'id', 'track_id', 'artist_id', 'track_title',
            'artist_name', 'album_title', 'album_cover',
            'duration', 'position', 'added_at', 'genre'
        ]


class QueueTrackAddSerializer(serializers.Serializer):
    track_id = serializers.IntegerField()


class QueueUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ['current_track_id', 'current_position']


class RecommendedTrackSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()
    artist = serializers.DictField()
    album = serializers.DictField()
    duration = serializers.IntegerField()
    genre = serializers.CharField(required=False)


class RecommendedPlaylistSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    tracks = serializers.ListField(child=serializers.DictField())