# PlayPod

PlayPod is a music streaming platform inspired by Spotify, built with Django REST Framework and integrated with the Deezer API. It provides a robust backend for streaming music, managing playlists, and offering personalized recommendations based on user preferences and listening history.

## Project Overview

PlayPod is designed to provide a seamless music streaming experience through a well-structured REST API. The platform integrates with Deezer's extensive music catalog to deliver high-quality audio content while maintaining its own user-focused features like personalized playlists, queue management, and a recommendation system.

## Installation and Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized setup)
- PostgreSQL (if running without Docker)
- Redis (for Celery task queue)

### Local Development Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/playpod.git
cd playpod
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
Create a `.env` file in the project root with the following variables:
```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:password@localhost:5432/playpod
DEEZER_BASE_URL=https://api.deezer.com
```

5. Run migrations
```bash
python manage.py migrate
```

6. Create a superuser
```bash
python manage.py createsuperuser
```

7. Start the development server
```bash
python manage.py runserver
```

### Docker Setup

1. Clone the repository
2. Configure environment variables in `.env` file or update docker-compose.yml
3. Run with Docker Compose:
```bash
docker-compose up -d
```
4. Access the API at http://localhost:8000/api/

## Design and Development Process

PlayPod was developed following a pragmatic approach to software architecture, combining best practices from both domain-driven design and clean architecture:

1. **Initial Planning**: We started with a clear vision of creating a Spotify-like experience, defining core features and user stories.

2. **Architecture Design**: The system was designed with a layered architecture:
   - Presentation layer (API endpoints)
   - Service layer (business logic)
   - Data access layer (models and repositories)
   - Integration layer (Deezer API client)

3. **Iterative Development**: Features were implemented incrementally, with a focus on getting a minimal viable product working early.

4. **Continuous Refinement**: The application underwent several refinements based on performance testing and user feedback.

## Unique Approaches and Methodologies

1. **Hybrid Caching Strategy**: PlayPod implements a multi-level caching system that combines in-memory, Redis, and database caching to optimize API response times while minimizing external API calls to Deezer.

2. **Asynchronous Task Processing**: Background tasks like history tracking, recommendation generation, and cache warming are handled by Celery, improving user experience by keeping the main request-response cycle fast.

3. **Dynamic Queue Management**: The queue system is implemented with a sophisticated algorithm that combines explicit user choices with smart auto-recommendations when the queue runs empty, similar to Spotify's radio feature.

4. **Proxy Streaming Architecture**: Rather than storing music files, PlayPod acts as an intelligent proxy between clients and Deezer, managing authentication, playback tracking, and dynamically refreshing expired stream URLs.

## Development Trade-offs and Decisions
0. **General Reason**: I'm confident using django, and I can handle any obstacles.

1. **External API Dependency**: Using Deezer's API means we don't need to manage a music catalog, but it creates a dependency on an external service. We mitigated this risk with extensive caching and fallback mechanisms.

2. **Django REST Framework vs. GraphQL**: We chose DRF for its maturity, community support, and simplicity, though GraphQL could have provided more flexible queries. The trade-off was development speed and reliability over query flexibility.

3. **PostgreSQL vs. NoSQL**: PostgreSQL was selected for its ACID properties and relational capabilities, which were crucial for maintaining data integrity in playlists and user relationships. This came at the cost of some horizontally scaling capabilities that NoSQL might have offered.

4. **Authentication System**: JWT tokens were chosen for their stateless nature and client-side storage benefits, though this required implementing refresh token rotation for security.

## Known Issues and Limitations

1. **Stream URL Expiration**: Deezer preview URLs expire quickly, sometimes causing 403 errors during playback. A refresh mechanism is implemented but occasionally fails if the client doesn't handle the refresh properly.

2. **Artist UUID/ID Handling**: There's occasional confusion between UUID internal identifiers and Deezer's numeric IDs, which can cause lookup errors in the artist endpoint.

3. **Rate Limiting**: Heavy usage can hit Deezer's rate limits. More sophisticated rate limiting and request throttling would improve this situation.

4. **Mobile Streaming Support**: Some mobile browsers have inconsistent behavior with audio streaming. A dedicated mobile app would be a better long-term solution.

## Technical Stack Rationale

### Backend
- **Django & Django REST Framework**: Chosen for rapid development, robust ORM, built-in security features, and excellent REST API capabilities. The mature ecosystem allowed us to focus on business logic rather than infrastructure.

- **PostgreSQL**: Selected for its reliability, ACID compliance, and powerful query capabilities. The JSON field support also allowed for flexible storage of metadata without sacrificing relational integrity.

- **Redis**: Used for caching and as a message broker for Celery. Its in-memory nature provides the speed needed for queue management and session data.

- **Celery**: Implemented for background task processing, enabling features like recommendation generation without blocking the main application thread.

### Deployment
- **AWS EC2, AMAZON S3, NEON, UPSTASH**: I said about it in the demo-video.

- **Docker & Docker Compose**: Containerization provides consistent environments across development and production, simplifying deployment and scaling.

- **Nginx**: Used as a reverse proxy for its high performance, caching capabilities, and ability to handle static files efficiently.

- **Gunicorn**: A production-ready WSGI server that offers better performance and reliability than Django's development server.

### Integration
- **Deezer API**: Chosen for its comprehensive music catalog, reliable API, and free tier that allows for development and testing without immediate licensing concerns.

This technical stack balances development speed, performance, maintainability, and scalability, allowing for rapid iteration while still providing a solid foundation for future growth.

## Features

- User authentication with JWT tokens
- Music catalog browsing and searching
- Playlist creation and management
- Queue system with Spotify-like functionality
- Favorites management
- Playback history tracking
- Auto-generated recommendations based on listening history
- AWS S3 integration for file storage

## Environment Variables

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
  "email": "string",
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

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "is_public": "boolean",
  "created_at": "datetime"
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

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "is_public": "boolean",
  "updated_at": "datetime"
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
  "track_id": "string"
}
```

**Response:**
```json
{
  "message": "Track added successfully",
  "track_info": {
    "id": "uuid",
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  }
}
```

### Add Multiple Tracks to Playlist

`POST /api/playlists/playlists/{id}/add_tracks/`

Add multiple tracks to a playlist.

**Request Body:**
```json
{
  "tracks": ["string", "string", "string"]
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

**Response:**
```json
{
  "message": "Track removed successfully"
}
```

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

**Response:**
```json
{
  "message": "Playlist added to queue",
  "queue_length": "integer",
  "current_track": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  }
}
```

### Upload Playlist Cover

`POST /api/playlists/playlists/{id}/upload-cover/`

Upload a cover image for a playlist.

**Request Body:**
Form data with 'cover_image' field containing an image file.

**Response:**
```json
{
  "cover_url": "string"
}
```

### Get Recommendations

`GET /api/playlists/recommendations/`

Get personalized track recommendations based on listening history.

**Parameters:**
- `limit` - Number of recommendations to return (default: 10)

**Response:**
```json
{
  "recommendations": [
    {
      "track_id": "string",
      "track_title": "string",
      "artist_id": "string",
      "artist_name": "string",
      "album_title": "string",
      "album_cover": "url",
      "duration": "integer"
    }
  ]
}
```

### Play Recommendation

`POST /api/playlists/play-recommendation/`

Start playing a recommended track and add similar tracks to the queue for radio playback.

**Request Body:**
```json
{
  "track_id": "string"
}
```

**Response:**
```json
{
  "message": "Radio mode started with recommended track",
  "current_track": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  },
  "queue_length": "integer"
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

**Response:**
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "track_count": "integer",
  "genre": "string"
}
```

### Get Favorites

`GET /api/playlists/favorites/`

Get the user's favorite tracks.

**Response:**
```json
[
  {
    "id": "uuid",
    "track_id": "string",
    "track_title": "string",
    "artist_id": "string",
    "artist_name": "string",
    "album_title": "string",
    "album_cover": "url",
    "added_at": "datetime"
  }
]
```

### Add to Favorites

`POST /api/playlists/favorites/add/`

Add a track to favorites.

**Request Body:**
```json
{
  "track_id": "string"
}
```

**Response:**
```json
{
  "message": "Track added to favorites",
  "track_info": {
    "track_id": "string",
    "track_title": "string"
  }
}
```

### Remove from Favorites

`DELETE /api/playlists/favorites/remove/?track_id={track_id}`

Remove a track from favorites.

**Response:**
```json
{
  "message": "Track removed from favorites"
}
```

## Queue Management

### Get Queue

`GET /api/playlists/queue/`

Get the user's current queue information.

**Response:**
```json
{
  "id": "uuid",
  "current_track_id": "string",
  "current_position": "integer",
  "track_count": "integer",
  "updated_at": "datetime"
}
```

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

**Response:**
```json
{
  "id": "uuid",
  "current_track_id": "string",
  "current_position": "integer",
  "updated_at": "datetime"
}
```

### Get Queue Tracks

`GET /api/playlists/queue/tracks/`

Get all tracks in the user's queue.

**Response:**
```json
[
  {
    "id": "uuid",
    "track_id": "string",
    "track_title": "string",
    "artist_id": "string",
    "artist_name": "string",
    "album_title": "string",
    "album_cover": "url",
    "duration": "integer",
    "position": "integer"
  }
]
```

### Enqueue Track

`POST /api/playlists/queue/enqueue/`

Add a track to the end of the queue.

**Request Body:**
```json
{
  "track_id": "string"
}
```

**Response:**
```json
{
  "message": "Track added to queue",
  "position": "integer",
  "track_info": {
    "track_id": "string",
    "track_title": "string"
  }
}
```

### Next Track

`POST /api/playlists/queue/next/`

Move to the next track in the queue, or add a related track if at the end of the queue (radio mode).

**Response:**
```json
{
  "current_track": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  },
  "position": "integer",
  "is_radio_mode": "boolean"
}
```

### Previous Track

`POST /api/playlists/queue/previous/`

Move to the previous track in the queue.

**Response:**
```json
{
  "current_track": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  },
  "position": "integer"
}
```

### Clear Queue

`POST /api/playlists/queue/clear/`

Clear all tracks from the queue.

**Response:**
```json
{
  "message": "Queue cleared"
}
```

### Get Current Track

`GET /api/playlists/queue/current/`

Get the current playing track.

**Response:**
```json
{
  "track_id": "string",
  "track_title": "string",
  "artist_id": "string",
  "artist_name": "string",
  "album_title": "string",
  "album_cover": "url",
  "duration": "integer",
  "position": "integer"
}
```

### Play Track at Position

`POST /api/playlists/queue/position/`

Start playing a track at a specific position in the queue.

**Request Body:**
```json
{
  "position": "integer"
}
```

**Response:**
```json
{
  "current_track": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string"
  },
  "position": "integer"
}
```

### Shuffle Queue

`POST /api/playlists/queue/shuffle/`

Shuffle the tracks in the queue after the current track.

**Response:**
```json
{
  "message": "Queue shuffled",
  "track_count": "integer"
}
```

### Stream Track

`POST /api/playlists/queue/stream/`

Start streaming a specific track from the queue or add it to the queue if not present.

**Request Body:**
```json
{
  "track_id": "string"
}
```

**Response:**
```json
{
  "stream_url": "url",
  "track_info": {
    "track_id": "string",
    "track_title": "string",
    "artist_name": "string",
    "duration": "integer"
  },
  "in_queue": "boolean",
  "position": "integer"
}
```

### Playback History

`GET /api/playlists/queue/history/`

Get the user's playback history.

**Parameters:**
- `limit` - Number of history items to return (default: 50)
- `offset` - Number of items to skip (default: 0)

**Response:**
```json
{
  "history": [
    {
      "id": "uuid",
      "track_id": "string",
      "track_title": "string",
      "artist_id": "string",
      "artist_name": "string",
      "album_title": "string",
      "album_cover": "url",
      "played_at": "datetime"
    }
  ],
  "count": "integer"
}
```

## Catalogue

### Search

`GET /api/catalogue/search/?q={query}`

Search for tracks, artists, and albums.

**Parameters:**
- `q` - Search query
- `limit` - Number of results per category (default: 10)

**Response:**
```json
{
  "tracks": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "album": {
        "id": "string",
        "title": "string",
        "cover_medium": "url"
      },
      "duration": "integer"
    }
  ],
  "artists": [
    {
      "id": "string",
      "name": "string",
      "picture_medium": "url"
    }
  ],
  "albums": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "cover_medium": "url"
    }
  ]
}
```

### Get Artist

`GET /api/catalogue/artists/{id}/`

Get detailed information about an artist, including albums and top tracks.

**Response:**
```json
{
  "artist": {
    "id": "string",
    "name": "string",
    "picture_xl": "url",
    "nb_album": "integer",
    "nb_fan": "integer"
  },
  "albums": [
    {
      "id": "string",
      "title": "string",
      "cover_medium": "url",
      "release_date": "date"
    }
  ],
  "top_tracks": [
    {
      "id": "string",
      "title": "string",
      "duration": "integer",
      "preview": "url",
      "album": {
        "id": "string",
        "title": "string",
        "cover_medium": "url"
      }
    }
  ]
}
```

### Get Album

`GET /api/catalogue/albums/{id}/`

Get detailed information about an album, including tracks.

**Response:**
```json
{
  "album": {
    "id": "string",
    "title": "string",
    "cover_xl": "url",
    "release_date": "date",
    "artist": {
      "id": "string",
      "name": "string"
    }
  },
  "tracks": [
    {
      "id": "string",
      "title": "string",
      "duration": "integer",
      "track_position": "integer",
      "preview": "url"
    }
  ]
}
```

### Get Track

`GET /api/catalogue/tracks/{id}/`

Get detailed information about a track with related tracks.

**Response:**
```json
{
  "track": {
    "id": "string",
    "title": "string",
    "duration": "integer",
    "preview": "url",
    "artist": {
      "id": "string",
      "name": "string"
    },
    "album": {
      "id": "string",
      "title": "string",
      "cover_medium": "url"
    }
  },
  "related_tracks": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "album": {
        "id": "string",
        "title": "string",
        "cover_medium": "url"
      }
    }
  ]
}
```

### Stream Track

`GET /api/catalogue/stream/{id}/`

Get streaming URL for a track or stream the audio directly.

**Response:**
If direct streaming is disabled:
```json
{
  "preview_url": "url"
}
```

If an error occurs:
```json
{
  "error": "string",
  "preview_url": "url",
  "fallback": "boolean",
  "message": "string"
}
```

## Genres

### Get Genres

`GET /api/catalogue/genres/`

Get all available music genres.

**Response:**
```json
[
  {
    "id": "integer",
    "name": "string",
    "picture_medium": "url"
  }
]
```

### Get Genre Tracks

`GET /api/charts/genre/{genre_id}/`

Get top tracks for a specific genre.

**Parameters:**
- `limit` - Number of tracks to return (default: 20)

**Response:**
```json
{
  "genre": {
    "id": "integer",
    "name": "string"
  },
  "tracks": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "album": {
        "id": "string",
        "title": "string",
        "cover_medium": "url"
      },
      "duration": "integer"
    }
  ]
}
```

## Charts

### Get Top Charts

`GET /api/charts/top/`

Get current top charts.

**Parameters:**
- `limit` - Number of tracks to return (default: 20)

**Response:**
```json
{
  "tracks": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "album": {
        "id": "string",
        "title": "string",
        "cover_medium": "url"
      },
      "duration": "integer",
      "position": "integer"
    }
  ]
}
```

### Get New Releases

`GET /api/charts/new-releases/`

Get newly released albums.

**Parameters:**
- `limit` - Number of albums to return (default: 20)

**Response:**
```json
{
  "albums": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "cover_medium": "url",
      "release_date": "date"
    }
  ]
}
```

### Get Top Albums

`GET /api/charts/top-albums/`

Get current top albums.

**Parameters:**
- `limit` - Number of albums to return (default: 20)

**Response:**
```json
{
  "albums": [
    {
      "id": "string",
      "title": "string",
      "artist": {
        "id": "string",
        "name": "string"
      },
      "cover_medium": "url",
      "position": "integer"
    }
  ]
}
```

## Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `204 No Content`: Request succeeded, no content to return
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Authenticated but not authorized
- `404 Not Found`: Resource not found
- `415 Unsupported Media Type`: Request content type is not supported
- `500 Internal Server Error`: Server error