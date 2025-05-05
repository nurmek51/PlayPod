from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.deezer.client import deezer_client

class TopChartsView(APIView):
    """
    API endpoint for getting top chart tracks.
    ---
    parameters:
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
          maximum: 100
        description: Maximum number of tracks to return
    responses:
      200:
        description: Top chart tracks
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
            if limit > 100:
                limit = 100
        except ValueError:
            limit = 50

        tracks = deezer_client.get_top_charts(limit=limit)
        return Response(tracks)


class TopAlbumsView(APIView):
    """
    API endpoint for getting top albums.
    ---
    parameters:
      - name: limit
        in: query
        schema:
          type: integer
          default: 25
          maximum: 50
        description: Maximum number of albums to return
    responses:
      200:
        description: Top albums
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = request.query_params.get('limit', 25)
        try:
            limit = int(limit)
            if limit > 50:
                limit = 50
        except ValueError:
            limit = 25

        albums = deezer_client.get_top_albums(limit=limit)
        return Response(albums)


class NewReleasesView(APIView):
    """
    API endpoint for getting new music releases.
    ---
    parameters:
      - name: limit
        in: query
        schema:
          type: integer
          default: 50
          maximum: 100
        description: Maximum number of releases to return
    responses:
      200:
        description: New music releases
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
            if limit > 100:
                limit = 100
        except ValueError:
            limit = 50

        releases = deezer_client.get_new_releases(limit=limit)
        return Response(releases) 