from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    MeView, MeUpdateView, UserPublicView,
    FavoriteViewSet, PlaybackHistoryViewSet, PlaybackHistoryView,
    AvatarUploadView, RegisterView
)

router = DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'history', PlaybackHistoryViewSet, basename='playback-history')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('me/', MeView.as_view(), name='me'),
    path('me/update/', MeUpdateView.as_view(), name='me_update'),
    path('me/avatar/', AvatarUploadView.as_view(), name='me_avatar'),
    path('users/<uuid:pk>/', UserPublicView.as_view(), name='user_public'),
    path('history/all/', PlaybackHistoryView.as_view(), name='history_all'),
    path('', include(router.urls)),
]
