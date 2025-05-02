from django.contrib import admin
from .models import Playlist, PlaylistTrack, Queue, QueueTrack


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 0
    readonly_fields = ['id', 'added_at']


class QueueTrackInline(admin.TabularInline):
    model = QueueTrack
    extra = 0
    readonly_fields = ['id', 'added_at']


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'is_public', 'track_count', 'created_at', 'updated_at']
    list_filter = ['is_public', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'user__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [PlaylistTrackInline]


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'current_track_id', 'updated_at']
    search_fields = ['user__username', 'current_track_id']
    readonly_fields = ['id', 'updated_at']
    inlines = [QueueTrackInline]