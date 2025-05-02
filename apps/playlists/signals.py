from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Playlist, PlaylistTrack


@receiver(post_delete, sender=Playlist)
def cleanup_playlist_tracks(sender, instance, **kwargs):
    PlaylistTrack.objects.filter(playlist_id=instance.id).delete()