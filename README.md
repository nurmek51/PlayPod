# PlayPod

PlayPod is a music streaming platform inspired by Spotify, built with Django REST Framework and integrated with the Deezer API.

## Features

- User authentication with JWT tokens
- Music catalog browsing and searching
- Playlist creation and management
- Queue system with Spotify-like functionality
- Favorites management
- Playback history tracking
- Auto-generated recommendations based on listening history
- AWS S3 integration for file storage

## Setup

### Using Docker Compose

1. Clone the repository
2. Configure environment variables in `.env` file or docker-compose.yml
3. Run `docker-compose up -d`
4. Access the API at http://localhost:8000/api/

### Environment Variables

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DATABASE_URL` - PostgreSQL connection string
- `CELERY_BROKER_URL` - Redis URL for Celery
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name
- `AWS_S3_REGION_NAME` - S3 region
- `DEEZER_BASE_URL` - Deezer API base URL

## Queue Functionality

The queue system in PlayPod works similarly to Spotify:

1. When a playlist is played from a specific track, all subsequent tracks are added to the queue
2. When a playlist ends, radio mode automatically generates recommendations based on the user's listening history
3. Users can manually add tracks to the queue, clear the queue, or jump to any position

## Recommendation System

PlayPod offers two types of recommendations:

1. **Radio Mode**: Automatically plays similar tracks when the queue is empty
2. **Recommended Playlists**: Generates personalized playlists like "Your Daily Mood" based on listening history and genre preferences

# API Documentation

This section provides detailed information about all API endpoints available in the PlayPod application.

## Authentication

All endpoints except for registration and login require authentication. Authentication is handled through JWT tokens.

### Register

`POST /api/accounts/register/`

Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string"
}
```

### Login

`POST /api/accounts/token/`

Obtain a JWT token for authentication.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "refresh": "string",
  "access": "string"
}
```

### Refresh Token

`POST /api/accounts/token/refresh/`

Refresh an access token using a refresh token.

**Request Body:**
```json
{
  "refresh": "string"
}
```

**Response:**
```json
{
  "access": "string"
}
```

## User Profile

### Get Profile

`GET /api/accounts/profile/`

Get the current user's profile.

**Response:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "bio": "string",
  "avatar": "url"
}
```

### Update Profile

`PATCH /api/accounts/profile/`

Update the current user's profile.

**Request Body:**
```json
{
  "bio": "string"
}
```

**Response:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "bio": "string",
  "avatar": "url"
}
```

### Upload Avatar

`POST /api/accounts/upload-avatar/`

Upload a profile avatar image.

**Request Body:**
Form data with 'avatar' field containing an image file.

**Response:**
```json
{
  "avatar_url": "string"
}
```

## Playlists

### List Playlists

`GET /api/playlists/playlists/`

Get a list of all public playlists and the user's own playlists.

Parameters:
- `me=true` - Filter to only show the user's playlists

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "string",
    "description": "string",
    "cover_image": "url",
    "is_public": "boolean",
    "track_count": "integer",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

### Get Playlist

`GET /api/playlists/playlists/{id}/`

Get a specific playlist with all its tracks.

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "cover_image": "url",
  "is_public": "boolean",
  "track_count": "integer",
  "created_at": "datetime",
  "updated_at": "datetime",
  "tracks": [
    {
      "id": "uuid",
      "track_id": "string",
      "artist_id": "string",
      "track_title": "string",
      "artist_name": "string",
      "album_title": "string",
      "album_cover": "url",
      "duration": "integer",
      "position": "integer",
      "added_at": "datetime"
    }
  ]
}
```

### Create Playlist

`POST /api/playlists/playlists/`

Create a new playlist.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "is_public": "boolean"
}
```

### Update Playlist

`PATCH /api/playlists/playlists/{id}/`

Update a playlist's details.

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "is_public": "boolean"
}
```

### Delete Playlist

`DELETE /api/playlists/playlists/{id}/`

Delete a playlist.

**Response:**
Status 204 No Content

### Add Track to Playlist

`POST /api/playlists/playlists/{id}/add_track/`

Add a track to a playlist.

**Request Body:**
```json
{
  "track_id": "integer"
}
```

### Add Multiple Tracks to Playlist

`POST /api/playlists/playlists/{id}/add_tracks/`

Add multiple tracks to a playlist.

**Request Body:**
```json
{
  "tracks": ["integer", "integer", "integer"]
}
```

**Response:**
```json
{
  "added_count": "integer",
  "total": "integer"
}
```

### Remove Track from Playlist

`DELETE /api/playlists/playlists/{id}/remove_track/?track_id={track_id}`

Remove a track from a playlist.

### Play Playlist

`POST /api/playlists/playlists/{id}/play/`

Start playing a playlist by adding all its tracks to the user's queue.

**Request Body:**
```json
{
  "position": "integer",  // Optional: position to start playing from
  "shuffle": "boolean"    // Optional: whether to shuffle the playlist
}
```

### Get Recommendations

`GET /api/playlists/recommendations/`

Get personalized track recommendations based on listening history.

### Play Recommendation

`POST /api/playlists/play-recommendation/`

Start playing a recommended track and add similar tracks to the queue for radio playback.

**Request Body:**
```json
{
  "track_id": "string"
}
```

### Generate Playlist

`POST /api/playlists/generate/`

Generate a new playlist based on a specified genre.

**Request Body:**
```json
{
  "genre": "string",
  "genre_id": "integer", // Optional
  "name": "string"       // Optional
}
```

## Queue Management

### Get Queue

`GET /api/playlists/queue/`

Get the user's current queue.

### Update Queue

`PATCH /api/playlists/queue/`

Update the current queue position.

**Request Body:**
```json
{
  "current_track_id": "string",
  "current_position": "integer"
}
```

### Get Queue Tracks

`GET /api/playlists/queue/tracks/`

Get all tracks in the user's queue.

### Enqueue Track

`POST /api/playlists/queue/enqueue/`

Add a track to the end of the queue.

**Request Body:**
```json
{
  "track_id": "integer"
}
```

### Next Track

`POST /api/playlists/queue/next/`

Move to the next track in the queue, or add a related track if at the end of the queue (radio mode).

### Previous Track

`POST /api/playlists/queue/previous/`

Move to the previous track in the queue.

### Clear Queue

`POST /api/playlists/queue/clear/`

Clear all tracks from the queue.

### Get Current Track

`GET /api/playlists/queue/current/`

Get the current playing track.

### Play Track at Position

`POST /api/playlists/queue/position/`

Start playing a track at a specific position in the queue.

**Request Body:**
```json
{
  "position": "integer"
}
```

### Shuffle Queue

`POST /api/playlists/queue/shuffle/`

Shuffle the tracks in the queue after the current track.

### Stream Track

`POST /api/playlists/queue/stream/`

Start streaming a specific track from the queue or add it to the queue if not present.

**Request Body:**
```json
{
  "track_id": "string"
}
```

### Playback History

`GET /api/playlists/queue/history/`

Get the user's playback history.

## Catalogue

### Search

`GET /api/catalogue/search/?q={query}`

Search for tracks, artists, and albums.

**Response:**
```json
{
  "tracks": [/* Track objects */],
  "artists": [/* Artist objects */],
  "albums": [/* Album objects */]
}
```

### Get Track

`GET /api/catalogue/track/{id}/`

Get details for a specific track.

### Stream Track

`GET /api/catalogue/stream/{id}/`

Get streaming URL for a track.

**Response:**
```json
{
  "stream_url": "url"
}
```

## Charts

### Get Top Charts

`GET /api/charts/top/`

Get current top charts.

**Parameters:**
- `limit` - Number of tracks to return (default: 20)

### Get Genre Charts

`GET /api/charts/genre/{genre}/`

Get top tracks for a specific genre.

**Parameters:**
- `limit` - Number of tracks to return (default: 20)

## Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded, no content to return
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error