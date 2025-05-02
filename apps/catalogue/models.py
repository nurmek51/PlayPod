import uuid
from django.db import models


class Artist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    image_url = models.URLField(blank=True)
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    deezer_id = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(
        Artist,
        related_name='albums',
        on_delete=models.CASCADE
    )
    cover_url = models.URLField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    deezer_id = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['-release_date']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"


class Track(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(
        Artist,
        related_name='tracks',
        on_delete=models.CASCADE
    )
    album = models.ForeignKey(
        Album,
        related_name='tracks',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    duration = models.PositiveIntegerField(default=0)
    audio_url = models.URLField()
    popularity = models.PositiveIntegerField(default=0)
    genre = models.CharField(max_length=100, blank=True)
    deezer_id = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"