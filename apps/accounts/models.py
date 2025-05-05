from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username


class Favorite(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    track_id = models.CharField(max_length=50)
    artist_id = models.CharField(max_length=50)
    track_title = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_title = models.CharField(max_length=255, blank=True)
    album_cover = models.URLField(blank=True)
    duration = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'track_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.track_title}"


class PlaybackHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playback_history')
    track_id = models.CharField(max_length=50)
    artist_id = models.CharField(max_length=50)
    track_title = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_title = models.CharField(max_length=255, blank=True)
    album_cover = models.URLField(blank=True)
    genre_id = models.CharField(max_length=50, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True)
    position = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Playback histories"

    def __str__(self):
        return f"{self.user.username} - {self.track_title} at {self.timestamp}"