from django.urls import path
from .views import (
    SearchView, ArtistDetailView, AlbumDetailView,
    TrackDetailView, StreamTrackView
)

urlpatterns = [
    path('search/', SearchView.as_view(), name='search'),
    path('artists/<int:artist_id>/', ArtistDetailView.as_view(), name='artist-detail'),
    path('albums/<int:album_id>/', AlbumDetailView.as_view(), name='album-detail'),
    path('tracks/<int:track_id>/', TrackDetailView.as_view(), name='track-detail'),
    path('stream/<int:track_id>/', StreamTrackView.as_view(), name='stream-track'),
]