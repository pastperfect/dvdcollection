# API Reference

Technical documentation for integrations and APIs used in the DVD Collection Tracker.

## 🌐 External API Integrations

### TMDB (The Movie Database) API

The application integrates with TMDB for comprehensive movie metadata.

#### Configuration

```python
# Environment Variables
TMDB_API_KEY=your_api_key_here
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/
```

#### TMDBService Class

Located in `tracker/services.py`

##### Initialization
```python
from tracker.services import TMDBService

tmdb_service = TMDBService()
```

##### Methods

###### `search_movies(query)`
Search for movies by title.

**Parameters:**
- `query` (str): Movie title to search for

**Returns:**
- `dict`: TMDB search results with movies array

**Example:**
```python
results = tmdb_service.search_movies("The Matrix")
# Returns: {'results': [movie_objects...], 'total_results': int}
```

###### `get_movie_details(movie_id)`
Get detailed information for a specific movie.

**Parameters:**
- `movie_id` (int): TMDB movie ID

**Returns:**
- `dict`: Complete movie details or None if not found

**Example:**
```python
movie = tmdb_service.get_movie_details(603)
# Returns movie object with all details
```

###### `get_movie_external_ids(movie_id)`
Get external IDs (IMDB, etc.) for a movie.

**Parameters:**
- `movie_id` (int): TMDB movie ID

**Returns:**
- `dict`: External ID mappings

**Example:**
```python
ids = tmdb_service.get_movie_external_ids(603)
# Returns: {'imdb_id': 'tt0133093', 'facebook_id': '...'}
```

###### `get_movie_posters(movie_id)`
Get available posters for a movie.

**Parameters:**
- `movie_id` (int): TMDB movie ID

**Returns:**
- `list`: Array of poster objects with paths and metadata

**Example:**
```python
posters = tmdb_service.get_movie_posters(603)
# Returns: [{'file_path': '/path.jpg', 'width': 500, ...}]
```

###### `format_movie_data(movie_data)`
Convert TMDB data to DVD model format.

**Parameters:**
- `movie_data` (dict): Raw TMDB movie object

**Returns:**
- `dict`: Formatted data for DVD model

**Example:**
```python
formatted = tmdb_service.format_movie_data(tmdb_movie)
# Returns: {'name': 'The Matrix', 'release_year': 1999, ...}
```

###### `download_poster(dvd, poster_url)`
Download and save poster image for a DVD.

**Parameters:**
- `dvd` (DVD): DVD model instance
- `poster_url` (str): Full URL to poster image

**Returns:**
- `bool`: Success status

#### API Endpoints Used

| Endpoint | Purpose | Documentation |
|----------|---------|---------------|
| `/search/movie` | Search movies by title | [TMDB Search](https://developers.themoviedb.org/3/search/search-movies) |
| `/movie/{id}` | Get movie details | [TMDB Movie Details](https://developers.themoviedb.org/3/movies/get-movie-details) |
| `/movie/{id}/external_ids` | Get external IDs | [TMDB External IDs](https://developers.themoviedb.org/3/movies/get-movie-external-ids) |
| `/movie/{id}/images` | Get movie images | [TMDB Images](https://developers.themoviedb.org/3/movies/get-movie-images) |

#### Rate Limits

TMDB API limits:
- **Requests per second**: 40
- **Requests per day**: 1,000,000
- **Requests per month**: No limit

### YTS API Integration

Used for torrent discovery and download links.

#### Configuration

```python
# Environment Variables
YTS_API_BASE_URL=https://yts.mx/api/v2
```

#### YTSService Class

##### Methods

###### `get_quality_torrents(imdb_id, quality_list)`
Get torrent links for specific qualities.

**Parameters:**
- `imdb_id` (str): IMDB ID (e.g., 'tt0133093')
- `quality_list` (list): Desired qualities ['720p', '1080p']

**Returns:**
- `list`: Array of torrent objects

**Example:**
```python
yts_service = YTSService()
torrents = yts_service.get_quality_torrents('tt0133093', ['720p', '1080p'])
# Returns: [{'quality': '720p', 'url': 'magnet:...', 'size': '1.2GB'}]
```

#### API Endpoints Used

| Endpoint | Purpose | Rate Limit |
|----------|---------|------------|
| `/list_movies.json` | Search movies by IMDB ID | No published limits |

## 🔌 Internal API Endpoints

### AJAX Endpoints

The application provides several AJAX endpoints for dynamic functionality.

#### Search Endpoints

##### `/ajax/search-tmdb/`
Real-time movie search for autocomplete.

**Method:** GET  
**Parameters:**
- `q`: Search query string

**Response:**
```json
{
  "results": [
    {
      "id": 603,
      "title": "The Matrix",
      "release_date": "1999-03-30",
      "poster_url": "https://image.tmdb.org/...",
      "overview": "Plot summary..."
    }
  ]
}
```

##### `/ajax/box-set-autocomplete/`
Autocomplete for box set names.

**Method:** GET  
**Parameters:**
- `q`: Partial box set name

**Response:**
```json
{
  "suggestions": ["James Bond Collection", "Lord of the Rings"]
}
```

##### `/ajax/storage-box-autocomplete/`
Autocomplete for storage box names.

**Method:** GET  
**Parameters:**
- `q`: Partial storage box name

**Response:**
```json
{
  "suggestions": ["Action Movies - Box 1", "Horror - Shelf 2"]
}
```

#### Data Management Endpoints

##### `/ajax/fetch-imdb-id/{pk}/`
Fetch IMDB ID for a DVD from TMDB.

**Method:** POST  
**Parameters:**
- `pk`: DVD primary key

**Response:**
```json
{
  "success": true,
  "imdb_id": "tt0133093",
  "message": "IMDB ID updated to tt0133093"
}
```

##### `/ajax/bulk-update-dvd/`
Update individual DVD fields via AJAX.

**Method:** POST  
**Content-Type:** application/json

**Request Body:**
```json
{
  "dvd_id": 123,
  "field": "status",
  "value": "disposed"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Updated status successfully"
}
```

##### `/ajax/delete-dvd/`
Delete a DVD via AJAX.

**Method:** POST  
**Content-Type:** application/json

**Request Body:**
```json
{
  "dvd_id": 123
}
```

**Response:**
```json
{
  "success": true,
  "message": "\"The Matrix\" has been deleted successfully"
}
```

##### `/ajax/refresh-all-tmdb/`
Start background TMDB data refresh.

**Method:** POST

**Response:**
```json
{
  "success": true,
  "task_id": "uuid-string"
}
```

##### `/ajax/refresh-progress/`
Check progress of TMDB refresh task.

**Method:** GET  
**Parameters:**
- `task_id`: Task UUID from refresh start

**Response:**
```json
{
  "progress": 45.5,
  "status": "Updating The Matrix... (123/270)",
  "completed": false,
  "results": {
    "updated": 122,
    "failed": 1,
    "skipped": 0
  }
}
```

## 🗄️ Database Models API

### DVD Model

Primary model for storing movie information.

#### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | AutoField | Primary key | Auto-generated |
| `name` | CharField | Movie title | Max 255 chars |
| `status` | CharField | Kept/Disposed | Choices: kept, disposed |
| `media_type` | CharField | Format type | Choices: physical, download, rip |
| `tmdb_id` | IntegerField | TMDB movie ID | Nullable |
| `imdb_id` | CharField | IMDB identifier | Max 20 chars, nullable |
| `poster` | ImageField | Poster image | Upload to 'posters/' |
| `overview` | TextField | Plot summary | Nullable |
| `release_year` | IntegerField | Release year | Nullable |
| `genres` | CharField | Comma-separated | Max 255 chars |
| `runtime` | IntegerField | Minutes | Nullable |
| `rating` | DecimalField | TMDB rating | Max 3.1 decimal |
| `is_tartan_dvd` | BooleanField | Tartan release | Default False |
| `is_box_set` | BooleanField | Part of collection | Default False |
| `box_set_name` | CharField | Collection name | Max 255 chars |
| `is_unopened` | BooleanField | Sealed status | Default False |
| `is_unwatched` | BooleanField | Viewing status | Default False |
| `storage_box` | CharField | Physical location | Max 100 chars |
| `created_at` | DateTimeField | Creation time | Auto-generated |
| `updated_at` | DateTimeField | Last modified | Auto-updated |

#### Methods

##### `get_absolute_url()`
Get URL for DVD detail page.

**Returns:** `/dvd/{pk}/`

##### `get_genres_list()`
Get genres as Python list.

**Returns:** `list` of genre strings

##### `get_status_display_class()`
Get Bootstrap CSS class for status.

**Returns:** `str` - 'success' or 'danger'

##### `get_media_type_display_class()`
Get Bootstrap CSS class for media type.

**Returns:** `str` - 'primary', 'info', or 'warning'

##### `get_special_features_badges()`
Get list of special feature badges for display.

**Returns:**
```python
[
  {'text': 'Tartan', 'class': 'bg-purple text-white'},
  {'text': 'Box Set', 'class': 'bg-info'},
  {'text': 'Unopened', 'class': 'bg-success'},
  {'text': 'Unwatched', 'class': 'bg-warning'}
]
```

### AppSettings Model

Application configuration storage.

#### Fields

| Field | Type | Description |
|-------|------|-------------|
| `tmdb_api_key` | CharField | TMDB API key |
| `created_at` | DateTimeField | Creation time |
| `updated_at` | DateTimeField | Last modified |

#### Methods

##### `get_settings()` (classmethod)
Get or create singleton settings instance.

**Returns:** AppSettings instance

## 🔧 Service Layer Architecture

### Base Service Pattern

All external services follow a consistent pattern:

```python
class BaseService:
    def __init__(self):
        self.api_key = self.get_api_key()
        self.base_url = self.get_base_url()
    
    def get_api_key(self):
        # Implementation specific
        pass
    
    def make_request(self, endpoint, params=None):
        # Standard HTTP request handling
        pass
    
    def handle_errors(self, response):
        # Standard error handling
        pass
```

### Error Handling

All services implement consistent error handling:

- **Network Errors**: Graceful degradation with user feedback
- **API Errors**: Specific error messages for different failure types
- **Rate Limiting**: Automatic retry with exponential backoff
- **Data Validation**: Ensure data integrity before storage

### Caching Strategy

- **API Responses**: Cache TMDB responses for 24 hours
- **Images**: Store locally with efficient file naming
- **Search Results**: Cache popular searches for 1 hour
- **Configuration**: Cache settings in memory for performance

## 📊 Data Formats

### CSV Export Format

```csv
Movie Name,Release Year,Status,Media Type,720p Download Link,1080p Download Link
"The Matrix",1999,"Kept","Physical","magnet:...","magnet:..."
```

### JSON API Responses

Standard response format:
```json
{
  "success": boolean,
  "data": object|array,
  "message": string,
  "errors": array
}
```

### Image URL Format

TMDB images follow pattern:
```
https://image.tmdb.org/t/p/{size}{file_path}
```

Size options: w92, w154, w185, w342, w500, w780, original

---

*Complete API reference for DVD Collection Tracker. For implementation details, see the source code and [Development Guide](development.md).*