from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.deezer.client import deezer_client


@shared_task
def generate_radio_recommendations(user_id):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import PlaybackHistory
    from .models import Queue, QueueTrack

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)

        two_weeks_ago = timezone.now() - timedelta(days=14)
        history = PlaybackHistory.objects.filter(
            user=user,
            played_at__gte=two_weeks_ago
        ).order_by('-played_at')[:20]

        if not history:
            return False

        queue, created = Queue.objects.get_or_create(user=user)

        track_count = QueueTrack.objects.filter(queue=queue).count()

        if track_count >= 5:
            return False

        recommendations = []
        track_ids_in_queue = set(QueueTrack.objects.filter(queue=queue).values_list('track_id', flat=True))

        for play in history:
            if len(recommendations) >= 5:
                break

            related_tracks = deezer_client.get_related_tracks(play.track_id, limit=3)

            if related_tracks:
                for track in related_tracks:
                    if (track['id'] in track_ids_in_queue or
                            any(r['id'] == track['id'] for r in recommendations)):
                        continue

                    recommendations.append(track)

                    if len(recommendations) >= 5:
                        break

        next_position = track_count
        for track in recommendations:
            QueueTrack.objects.create(
                queue=queue,
                track_id=track['id'],
                artist_id=track['artist']['id'],
                track_title=track['title'],
                artist_name=track['artist']['name'],
                album_title=track.get('album', {}).get('title', ''),
                album_cover=track.get('album', {}).get('cover_medium', ''),
                duration=track.get('duration', 0),
                position=next_position
            )
            next_position += 1

        return True

    except Exception as e:
        print(f"Error generating recommendations for user {user_id}: {str(e)}")
        return False


@shared_task
def clean_old_queue_tracks():
    from .models import Queue, QueueTrack
    from django.db.models import F

    yesterday = timezone.now() - timedelta(days=1)

    queues = Queue.objects.all()

    for queue in queues:
        try:
            if queue.current_track_id:
                current_track = QueueTrack.objects.filter(
                    queue=queue,
                    track_id=queue.current_track_id
                ).first()

                if current_track:
                    QueueTrack.objects.filter(
                        queue=queue,
                        position__lt=current_track.position,
                        added_at__lt=yesterday
                    ).delete()
        except Exception as e:
            print(f"Error cleaning queue {queue.id}: {str(e)}")
            continue

    return True