from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from collections import Counter
import random
from apps.deezer.client import deezer_client


@shared_task
def generate_radio_recommendations(user_id):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import PlaybackHistory
    from .models import Queue, QueueTrack, Playlist, PlaylistTrack

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)

        two_weeks_ago = timezone.now() - timedelta(days=14)
        history = PlaybackHistory.objects.filter(
            user=user,
            timestamp__gte=two_weeks_ago
        ).order_by('-timestamp')[:20]

        if not history:
            return False

        queue, created = Queue.objects.get_or_create(user=user)

        track_count = QueueTrack.objects.filter(queue=queue).count()

        if track_count >= 5:
            return False

        genres = []
        for play in history:
            artist_genres = deezer_client.get_artist_genres(play.artist_id)
            genres.extend(artist_genres)

        genre_counter = Counter(genres)
        top_genres = [genre for genre, _ in genre_counter.most_common(3)]
        
        if not top_genres:
            top_genres = ["pop", "rock", "hip hop"]

        recommendations = []
        track_ids_in_queue = set(QueueTrack.objects.filter(queue=queue).values_list('track_id', flat=True))
        track_ids_in_history = set(history.values_list('track_id', flat=True))
        
        for genre in top_genres:
            if len(recommendations) >= 10:
                break
                
            genre_tracks = deezer_client.get_genre_tracks(genre, limit=20)
            
            for track in genre_tracks:
                track_id = str(track.get('id'))
                if (track_id not in track_ids_in_queue and 
                    track_id not in track_ids_in_history and
                    not any(r.get('id') == track.get('id') for r in recommendations)):
                    recommendations.append(track)
                    
                    if len(recommendations) >= 10:
                        break

        if history and len(recommendations) < 10:
            most_recent = history.first()
            related_tracks = deezer_client.get_related_tracks(most_recent.track_id, limit=10)
            
            for track in related_tracks:
                track_id = str(track.get('id'))
                if (track_id not in track_ids_in_queue and 
                    track_id not in track_ids_in_history and
                    not any(r.get('id') == track.get('id') for r in recommendations)):
                    recommendations.append(track)
                    
                    if len(recommendations) >= 10:
                        break

        next_position = track_count
        for track in recommendations:
            artist = track.get('artist', {})
            album = track.get('album', {})
            
            QueueTrack.objects.create(
                queue=queue,
                track_id=str(track.get('id')),
                artist_id=str(artist.get('id', '')),
                track_title=track.get('title', ''),
                artist_name=artist.get('name', ''),
                album_title=album.get('title', ''),
                album_cover=album.get('cover_medium', '') or album.get('cover', ''),
                duration=track.get('duration', 0),
                position=next_position
            )
            next_position += 1
            
        if track_count == 0 and next_position > 0:
            first_track = QueueTrack.objects.filter(queue=queue).order_by('position').first()
            if first_track:
                queue.current_track_id = first_track.track_id
                queue.current_position = 0
                queue.save()

        return True

    except Exception as e:
        print(f"Error generating recommendations for user {user_id}: {str(e)}")
        return False


@shared_task
def generate_recommended_playlists(user_id):
    from django.contrib.auth import get_user_model
    from apps.accounts.models import PlaybackHistory
    from .models import Playlist, PlaylistTrack

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)

        history = PlaybackHistory.objects.filter(user=user).order_by('-timestamp')[:50]
        
        if not history:
            return False
            
        genres = []
        for play in history:
            artist_genres = deezer_client.get_artist_genres(play.artist_id)
            genres.extend(artist_genres)
            
        genre_counter = Counter(genres)
        top_genres = [genre for genre, _ in genre_counter.most_common(3)]
        
        if not top_genres:
            top_genres = ["pop", "rock", "hip hop"]
            
        playlist_names = [
            "Your Daily Mood",
            "Me in POV of Strangers",
            "Perfect Mix",
            "Genre Fusion", 
            "New Discoveries",
            "Hidden Gems",
            "Soundtrack of Your Life",
            "Unexpected Favorites",
            "The Vibe Station",
            "Mood Elevator"
        ]
        
        playlist_name = random.choice(playlist_names)
        playlist = Playlist.objects.create(
            user=user,
            name=playlist_name,
            description=f"Personalized playlist based on your listening habits",
            is_public=True
        )
        
        added_track_ids = set()
        position = 0
        
        for genre in top_genres:
            genre_tracks = deezer_client.get_genre_tracks(genre, limit=15)
            
            for track in genre_tracks:
                if position >= 30:
                    break
                    
                track_id = str(track.get('id'))
                if track_id in added_track_ids:
                    continue
                    
                artist = track.get('artist', {})
                album = track.get('album', {})
                
                PlaylistTrack.objects.create(
                    playlist=playlist,
                    track_id=track_id,
                    artist_id=str(artist.get('id', '')),
                    track_title=track.get('title', ''),
                    artist_name=artist.get('name', ''),
                    album_title=album.get('title', ''),
                    album_cover=album.get('cover_medium', '') or album.get('cover', ''),
                    duration=track.get('duration', 0),
                    position=position
                )
                
                added_track_ids.add(track_id)
                position += 1
                
        return True
        
    except Exception as e:
        print(f"Error generating recommended playlists for user {user_id}: {str(e)}")
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