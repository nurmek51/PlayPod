from django.urls import path
from .views import PlaylistViewSet, QueueViewSet

# Playlist URLs
playlist_list = PlaylistViewSet.as_view({'get': 'list', 'post': 'create'})
playlist_detail = PlaylistViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})
playlist_tracks = PlaylistViewSet.as_view({'get': 'tracks'})
playlist_add_track = PlaylistViewSet.as_view({'post': 'add_track'})
playlist_add_tracks = PlaylistViewSet.as_view({'post': 'add_tracks'})
playlist_remove_track = PlaylistViewSet.as_view({'delete': 'remove_track'})
playlist_play = PlaylistViewSet.as_view({'post': 'play'})
playlist_recommendations = PlaylistViewSet.as_view({'get': 'recommendations'})
playlist_play_recommendation = PlaylistViewSet.as_view({'post': 'play_recommendation'})
playlist_generate = PlaylistViewSet.as_view({'post': 'generate'})

# Queue URLs
queue_list = QueueViewSet.as_view({'get': 'list'})
queue_next = QueueViewSet.as_view({'post': 'next'})
queue_previous = QueueViewSet.as_view({'post': 'previous'})
queue_tracks = QueueViewSet.as_view({'get': 'tracks'})
queue_enqueue = QueueViewSet.as_view({'post': 'enqueue'})
queue_clear = QueueViewSet.as_view({'post': 'clear'})
queue_current = QueueViewSet.as_view({'get': 'current'})
queue_position = QueueViewSet.as_view({'post': 'position'})
queue_shuffle = QueueViewSet.as_view({'post': 'shuffle'})
queue_stream = QueueViewSet.as_view({'post': 'stream'})
queue_history = QueueViewSet.as_view({'get': 'history'})

urlpatterns = [
    path('', playlist_list, name='playlist-list'),
    path('<uuid:pk>/', playlist_detail, name='playlist-detail'),
    path('<uuid:pk>/tracks/', playlist_tracks, name='playlist-tracks'),
    path('<uuid:pk>/add_track/', playlist_add_track, name='playlist-add-track'),
    path('<uuid:pk>/add_tracks/', playlist_add_tracks, name='playlist-add-tracks'),
    path('<uuid:pk>/remove_track/', playlist_remove_track, name='playlist-remove-track'),
    path('<uuid:pk>/play/', playlist_play, name='playlist-play'),

    path('recommendations/', playlist_recommendations, name='playlist-recommendations'),
    path('play-recommendation/', playlist_play_recommendation, name='playlist-play-recommendation'),
    path('generate/', playlist_generate, name='playlist-generate'),

    path('queue/', queue_list, name='queue-list'),
    path('queue/next/', queue_next, name='queue-next'),
    path('queue/tracks/', queue_tracks, name='queue-tracks'),
    path('queue/enqueue/', queue_enqueue, name='queue-enqueue'),
    path('queue/previous/', queue_previous, name='queue-previous'),
    path('queue/clear/', queue_clear, name='queue-clear'),
    path('queue/current/', queue_current, name='queue-current'),
    path('queue/position/', queue_position, name='queue-position'),
    path('queue/shuffle/', queue_shuffle, name='queue-shuffle'),
    path('queue/stream/', queue_stream, name='queue-stream'),
    path('queue/history/', queue_history, name='queue-history'),
]
