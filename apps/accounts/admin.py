from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, Favorite, PlaybackHistory


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('email', 'first_name', 'last_name', 'avatar', 'bio')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'track_title', 'artist_name', 'created_at')
    search_fields = ('user__username', 'track_title', 'artist_name')
    list_filter = ('created_at',)


@admin.register(PlaybackHistory)
class PlaybackHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'track_title', 'artist_name', 'position', 'timestamp')
    search_fields = ('user__username', 'track_title', 'artist_name')
    list_filter = ('timestamp',)