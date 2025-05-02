from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PlaylistViewSet, PlaylistRadioView, PlaylistReorderView,
    PlaylistBulkActionView, FavoritesPlaylistView,
    QueueView, QueueActionView
)

router = DefaultRouter()
router.register(r'playlists', PlaylistViewSet, basename='playlist')

urlpatterns = [
    path('', include(router.urls)),
    path('playlists/<uuid:pk>/radio/', PlaylistRadioView.as_view()),
    path('playlists/<uuid:pk>/reorder/', PlaylistReorderView.as_view()),
    path('playlists/<uuid:pk>/<str:action>/', PlaylistBulkActionView.as_view()),
    path('favorites/', FavoritesPlaylistView.as_view()),
    path('queue/', QueueView.as_view()),
    path('queue/<str:action>/', QueueActionView.as_view()),
]
