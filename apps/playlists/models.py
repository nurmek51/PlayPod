from django.db import models
import uuid
from django.conf import settings

class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='playlist_covers/', null=True, blank=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def track_count(self):
        return self.tracks.count()

class PlaylistTrack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='tracks')
    track_id = models.CharField(max_length=50)
    artist_id = models.CharField(max_length=50)
    track_title = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_title = models.CharField(max_length=255, blank=True)
    album_cover = models.URLField(blank=True)
    genre_id = models.CharField(max_length=50, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True)
    duration = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position']
        unique_together = ('playlist', 'track_id')

class Queue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='queue')
    current_track_id = models.CharField(max_length=50, null=True, blank=True)
    current_position = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

class QueueTrack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue = models.ForeignKey(Queue, on_delete=models.CASCADE, related_name='tracks')
    track_id = models.CharField(max_length=32)
    artist_id = models.CharField(max_length=50)
    track_title = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_title = models.CharField(max_length=255, blank=True)
    album_cover = models.URLField(blank=True)
    genre_id = models.CharField(max_length=50, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True)
    duration = models.PositiveIntegerField(default=0)
    position = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['queue','track_id'],]