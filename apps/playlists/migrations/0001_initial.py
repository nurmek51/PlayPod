# Generated by Django 5.0.5 on 2025-05-04 17:51

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Playlist',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('cover_image', models.ImageField(blank=True, null=True, upload_to='playlist_covers/')),
                ('is_public', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlists', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('current_track_id', models.CharField(blank=True, max_length=50, null=True)),
                ('current_position', models.PositiveIntegerField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='queue', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PlaylistTrack',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('track_id', models.CharField(max_length=50)),
                ('artist_id', models.CharField(max_length=50)),
                ('track_title', models.CharField(max_length=255)),
                ('artist_name', models.CharField(max_length=255)),
                ('album_title', models.CharField(blank=True, max_length=255)),
                ('album_cover', models.URLField(blank=True)),
                ('duration', models.PositiveIntegerField(default=0)),
                ('position', models.PositiveIntegerField(default=0)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='playlists.playlist')),
            ],
            options={
                'ordering': ['position'],
                'unique_together': {('playlist', 'track_id')},
            },
        ),
        migrations.CreateModel(
            name='QueueTrack',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('track_id', models.CharField(max_length=32)),
                ('artist_id', models.CharField(max_length=50)),
                ('track_title', models.CharField(max_length=255)),
                ('artist_name', models.CharField(max_length=255)),
                ('album_title', models.CharField(blank=True, max_length=255)),
                ('album_cover', models.URLField(blank=True)),
                ('duration', models.PositiveIntegerField(default=0)),
                ('position', models.PositiveIntegerField(default=0)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='playlists.queue')),
            ],
            options={
                'unique_together': {('queue', 'track_id')},
            },
        ),
    ]
