from rest_framework import serializers
from .models import Artist, Album, Track


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ['id', 'name', 'image_url', 'bio', 'website', 'deezer_id']


class ArtistDetailSerializer(serializers.ModelSerializer):
    album_count = serializers.SerializerMethodField()
    track_count = serializers.SerializerMethodField()

    class Meta:
        model = Artist
        fields = ['id', 'name', 'image_url', 'bio', 'website', 'deezer_id', 'album_count', 'track_count']

    def get_album_count(self, obj):
        return obj.albums.count()

    def get_track_count(self, obj):
        return obj.tracks.count()


class AlbumSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)

    class Meta:
        model = Album
        fields = ['id', 'title', 'artist', 'artist_name', 'cover_url', 'release_date', 'deezer_id']


class TrackListSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True, allow_null=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_name', 'album', 'album_title',
            'duration', 'genre', 'is_favorite', 'deezer_id'
        ]

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class TrackDetailSerializer(serializers.ModelSerializer):
    artist_name = serializers.CharField(source='artist.name', read_only=True)
    album_title = serializers.CharField(source='album.title', read_only=True, allow_null=True)
    album_cover = serializers.URLField(source='album.cover_url', read_only=True, allow_null=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Track
        fields = [
            'id', 'title', 'artist', 'artist_name', 'album', 'album_title',
            'album_cover', 'duration', 'genre', 'audio_url', 'is_favorite', 'deezer_id'
        ]

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class RadioNextSerializer(serializers.Serializer):
    seed = serializers.UUIDField()


class ExternalTrackSerializer(serializers.Serializer):
    title = serializers.CharField()
    artist_name = serializers.CharField()
    album_title = serializers.CharField(allow_null=True, required=False)
    duration = serializers.IntegerField()
    genre = serializers.CharField(allow_blank=True, required=False)
    audio_url = serializers.URLField(source='preview')
    album_cover = serializers.URLField(source='album_image', allow_null=True, required=False)
    deezer_id = serializers.CharField()
    is_favorite = serializers.BooleanField(default=False)
    artist_id = serializers.CharField(required=False, allow_null=True)
    album_id = serializers.CharField(required=False, allow_null=True)