from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    MeView, MeUpdateView, UserPublicView,
    FavoriteViewSet, PlaybackHistoryViewSet
)

router = DefaultRouter()
router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('history', PlaybackHistoryViewSet, basename='history')

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('me/', MeView.as_view(), name='me'),
    path('me/update/', MeUpdateView.as_view(), name='me-update'),
    path('users/<uuid:pk>/', UserPublicView.as_view(), name='user-detail'),

    path('', include(router.urls)),
]