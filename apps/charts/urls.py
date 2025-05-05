from django.urls import path
from .views import TopChartsView, TopAlbumsView, NewReleasesView
 
urlpatterns = [
    path('top-charts/', TopChartsView.as_view(), name='top-charts'),
    path('top-albums/', TopAlbumsView.as_view(), name='top-albums'),
    path('new-releases/', NewReleasesView.as_view(), name='new-releases'),
] 