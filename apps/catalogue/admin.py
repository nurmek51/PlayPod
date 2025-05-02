from django.contrib import admin
from .models import Artist, Album, Track

class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'deezer_id')
    search_fields = ('name', 'deezer_id')

class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'deezer_id')
    list_filter = ('artist',)
    search_fields = ('title', 'artist__name', 'deezer_id')

class TrackAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album', 'duration', 'genre', 'popularity', 'deezer_id')
    list_filter = ('artist', 'genre')
    search_fields = ('title', 'artist__name', 'album__title', 'deezer_id')
    ordering = ('title',)

admin.site.register(Artist, ArtistAdmin)
admin.site.register(Album, AlbumAdmin)
admin.site.register(Track, TrackAdmin)