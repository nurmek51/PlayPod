from django.apps import AppConfig


class PlaylistsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.playlists'

    def ready(self):
        try:
            import apps.playlists.signals
        except ImportError:
            pass