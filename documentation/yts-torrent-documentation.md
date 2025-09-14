# YTS Service & Torrent Functionality

This document provides comprehensive documentation for the YTS (YIFY Torrents) integration and torrent functionality in the DVD Collection Tracker application.

## Table of Contents

1. [Overview](#overview)
2. [YTS Service Architecture](#yts-service-architecture)
3. [Data Model and Storage](#data-model-and-storage)
4. [Caching Strategy](#caching-strategy)
5. [User Interface](#user-interface)
6. [API Endpoints](#api-endpoints)
7. [Developer Guide](#developer-guide)
8. [Configuration](#configuration)
9. [Troubleshooting](#troubleshooting)
10. [Security Considerations](#security-considerations)

## Overview

The DVD Collection Tracker integrates with the YTS (YIFY Torrents) API to provide users with convenient access to high-quality movie torrents. The integration includes intelligent caching, automatic data refresh, and a user-friendly interface for browsing and downloading torrents.

### Key Features

- **Automatic Torrent Discovery**: Fetches available torrents for movies using IMDB IDs
- **Intelligent Caching**: Stores torrent data locally to improve performance
- **Quality Filtering**: Focuses on high-quality torrents (720p, 1080p)
- **Fresh Data Guarantee**: Automatic refresh of stale torrent data
- **User-Controlled Refresh**: Manual refresh button for on-demand updates
- **Responsive Interface**: Clean, mobile-friendly torrent listing

### Prerequisites

For torrent functionality to work, DVDs must have:
1. A valid IMDB ID
2. Corresponding entries in the YTS database

## YTS Service Architecture

### YTSService Class

The `YTSService` class (`tracker/services.py`) handles all interactions with the YTS API.

```python
class YTSService:
    """Service for interacting with the YTS API to get torrent information."""
    
    def __init__(self):
        self.base_url = "https://yts.mx/api/v2"
```

#### Core Methods

##### `get_movie_torrents(imdb_id)`

Fetches all available torrents for a specific movie using its IMDB ID.

**Parameters:**
- `imdb_id` (str): The IMDB ID of the movie (e.g., "tt1234567")

**Returns:**
- `list`: List of torrent dictionaries containing quality, size, seeds, peers, and download URL

**Features:**
- Built-in caching (6 hours for successful results, 1 hour for empty results)
- Error handling with logging
- Timeout protection (10 seconds)

##### `get_quality_torrents(imdb_id, qualities=['720p', '1080p'])`

Filters torrents by specified quality levels.

**Parameters:**
- `imdb_id` (str): The IMDB ID of the movie
- `qualities` (list): List of desired quality levels (default: ['720p', '1080p'])

**Returns:**
- `list`: Filtered list of high-quality torrents

##### `filter_torrents_by_quality(torrents, qualities)`

Utility method for filtering torrent lists by quality.

### API Integration Details

The service communicates with the YTS API using the following endpoint:
```
GET https://yts.mx/api/v2/list_movies.json?query_term={imdb_id}&limit=1&sort_by=rating&order_by=desc
```

**Request Parameters:**
- `query_term`: IMDB ID for movie lookup
- `limit`: Number of results (always 1 for specific movie)
- `sort_by`: Sorting criteria (rating)
- `order_by`: Sort order (descending)

**Response Format:**
```json
{
  "status": "ok",
  "data": {
    "movies": [
      {
        "torrents": [
          {
            "url": "https://yts.mx/torrent/download/...",
            "hash": "torrent_hash",
            "quality": "1080p",
            "type": "bluray",
            "seeds": 150,
            "peers": 10,
            "size": "2.1 GB",
            "date_uploaded": "2023-01-15 12:00:00"
          }
        ]
      }
    ]
  }
}
```

## Data Model and Storage

### Database Schema

The torrent functionality uses two additional fields in the `DVD` model:

```python
class DVD(models.Model):
    # ... other fields ...
    
    # YTS Integration Fields
    yts_data = models.JSONField(
        blank=True, 
        null=True, 
        help_text="Cached YTS torrent data"
    )
    yts_last_updated = models.DateTimeField(
        blank=True, 
        null=True, 
        help_text="When YTS data was last refreshed"
    )
```

#### Field Details

**`yts_data` (JSONField)**
- Stores the complete torrent information as JSON
- Contains array of torrent objects with quality, size, seeds, peers, and URLs
- Can be null if no torrents are available
- Automatically updated during refresh operations

**`yts_last_updated` (DateTimeField)**
- Timestamp of the last successful YTS data fetch
- Used for cache freshness validation
- Automatically set during refresh operations
- Can be null for DVDs that have never been updated

### Model Methods

#### `get_cached_torrents()`

Returns the cached torrent data without making API calls.

```python
def get_cached_torrents(self):
    """Get cached YTS torrent data."""
    if self.yts_data and isinstance(self.yts_data, list):
        return self.yts_data
    return []
```

#### `is_yts_data_fresh(max_age_hours=24)`

Checks if cached torrent data is still fresh.

```python
def is_yts_data_fresh(self, max_age_hours=24):
    """Check if YTS data is fresh (within max_age_hours)."""
    if not self.yts_last_updated:
        return False
    
    age = timezone.now() - self.yts_last_updated
    return age < timedelta(hours=max_age_hours)
```

#### `refresh_yts_data()`

Fetches fresh torrent data from the YTS API and updates the database.

```python
def refresh_yts_data(self):
    """Refresh YTS torrent data from the API."""
    if not self.imdb_id:
        return False
    
    from .services import YTSService
    
    yts_service = YTSService()
    torrents = yts_service.get_quality_torrents(self.imdb_id, ['720p', '1080p'])
    
    # Store the data regardless of whether it's empty or not
    self.yts_data = torrents
    self.yts_last_updated = timezone.now()
    self.save(update_fields=['yts_data', 'yts_last_updated'])
    
    return True
```

#### `has_torrents()`

Quick check to determine if torrents are available for the movie.

```python
def has_torrents(self):
    """Check if this DVD has any torrents available."""
    if not self.imdb_id:
        return False
    
    # First check cached data
    if self.yts_data and isinstance(self.yts_data, list) and len(self.yts_data) > 0:
        return True
    
    # If no cached data or data is stale, check fresh data
    if not self.is_yts_data_fresh():
        yts_service = YTSService()
        torrents = yts_service.get_quality_torrents(self.imdb_id, ['720p', '1080p'])
        return len(torrents) > 0
    
    return False
```

## Caching Strategy

The torrent functionality implements a multi-layer caching strategy to optimize performance and reduce API calls.

### Cache Layers

1. **Django Cache Framework** (Short-term)
   - Duration: 6 hours for successful results, 1 hour for empty results
   - Scope: Individual API responses
   - Purpose: Reduce redundant API calls during high-traffic periods

2. **Database Storage** (Long-term)
   - Duration: 24 hours default (configurable)
   - Scope: Per-DVD torrent data
   - Purpose: Persistent storage and offline access

### Cache Flow

```
User Request → Check DB Cache → Fresh? → Return Cached Data
                     ↓
                  Stale/Missing
                     ↓
              API Call → Update DB → Return Fresh Data
```

### Cache Validation

```python
def dvd_detail(request, pk):
    dvd = get_object_or_404(DVD, pk=pk)
    
    torrents = []
    if dvd.imdb_id:
        # Check if we need to refresh YTS data
        if not dvd.is_yts_data_fresh():
            dvd.refresh_yts_data()
        
        torrents = dvd.get_cached_torrents()
    
    return render(request, 'tracker/dvd_detail.html', {
        'dvd': dvd,
        'torrents': torrents
    })
```

## User Interface

### DVD Detail Page Integration

The torrent section is seamlessly integrated into the DVD detail page with the following components:

#### Torrent Section Header

```html
<div class="detail-section-header d-flex justify-content-between align-items-center">
    <h5 class="mb-0"><i class="bi bi-download"></i> Torrent Downloads</h5>
    <div class="d-flex align-items-center gap-2">
        {% if dvd.yts_last_updated %}
            <small class="text-muted">Last updated: {{ dvd.yts_last_updated|date:"M d, Y H:i" }}</small>
        {% endif %}
        <button class="btn btn-sm btn-outline-secondary" id="refresh-yts-btn" onclick="refreshYtsData({{ dvd.pk }})">
            <i class="bi bi-arrow-clockwise"></i> Refresh
        </button>
    </div>
</div>
```

#### Torrent Listings

```html
{% if torrents %}
    <div class="torrent-downloads">
        {% for torrent in torrents %}
            <a href="{{ torrent.url }}" 
               class="torrent-download-btn"
               target="_blank" 
               rel="noopener noreferrer"
               title="Size: {{ torrent.size }}, Seeds: {{ torrent.seeds }}, Peers: {{ torrent.peers }}">
                <i class="bi bi-download"></i> 
                {{ torrent.type|capfirst }} {{ torrent.quality }} {{ torrent.video_codec }}
                <small class="torrent-size">({{ torrent.size }})</small>
            </a>
        {% endfor %}
    </div>
{% else %}
    <div class="alert alert-info mb-0" role="alert">
        <i class="bi bi-info-circle"></i>
        No torrents available for this movie on YTS.
    </div>
{% endif %}
```

#### IMDB ID Missing Warning

```html
{% elif dvd.tmdb_id %}
<div class="alert alert-warning mb-2" role="alert">
    <i class="bi bi-exclamation-triangle"></i>
    IMDB ID not available. 
    <button class="btn btn-sm btn-outline-primary ms-2" id="fetch-imdb-btn" onclick="fetchImdbId({{ dvd.pk }})">
        <i class="bi bi-cloud-download"></i> Auto-fetch IMDB ID
    </button>
</div>
{% endif %}
```

### JavaScript Functionality

#### Refresh YTS Data

```javascript
function refreshYtsData(dvdId) {
    const button = document.getElementById('refresh-yts-btn');
    const resultDiv = document.getElementById('yts-refresh-result');
    
    // Disable button and show loading
    button.disabled = true;
    button.innerHTML = '<i class="bi bi-hourglass-split"></i> Refreshing...';
    
    fetch(`/dvd/${dvdId}/refresh-yts/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <i class="bi bi-check-circle"></i> ${data.message}
                    <a href="." class="btn btn-sm btn-primary ms-2">Reload Page</a>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-circle"></i> ${data.error}
                </div>
            `;
        }
        resultDiv.style.display = 'block';
    })
    .finally(() => {
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Refresh';
    });
}
```

## API Endpoints

### Refresh YTS Data Endpoint

**Endpoint:** `POST /dvd/{pk}/refresh-yts/`

**Purpose:** Manually refresh torrent data for a specific DVD

**Parameters:**
- `pk` (int): Primary key of the DVD record

**Request Headers:**
- `X-CSRFToken`: Django CSRF token
- `Content-Type`: application/json

**Response Format:**

**Success Response:**
```json
{
    "success": true,
    "message": "YTS data refreshed successfully. Found 3 torrents.",
    "torrent_count": 3,
    "last_updated": "September 14, 2025 at 06:30 PM"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "IMDB ID is required to fetch torrent data"
}
```

**Implementation:**

```python
@require_http_methods(["POST"])
def refresh_yts_data(request, pk):
    """AJAX endpoint to refresh YTS torrent data for a specific DVD."""
    try:
        dvd = get_object_or_404(DVD, pk=pk)
        
        if not dvd.imdb_id:
            return JsonResponse({
                'success': False,
                'error': 'IMDB ID is required to fetch torrent data'
            })
        
        # Refresh the YTS data
        success = dvd.refresh_yts_data()
        
        if success:
            torrents = dvd.get_cached_torrents()
            torrent_count = len(torrents) if torrents else 0
            
            return JsonResponse({
                'success': True,
                'message': f'YTS data refreshed successfully. Found {torrent_count} torrents.',
                'torrent_count': torrent_count,
                'last_updated': dvd.yts_last_updated.strftime('%B %d, %Y at %I:%M %p') if dvd.yts_last_updated else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to refresh YTS data'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
```

### URL Configuration

```python
# tracker/urls.py
urlpatterns = [
    # ... other patterns ...
    path('dvd/<int:pk>/refresh-yts/', views.refresh_yts_data, name='refresh_yts_data'),
]
```

## Developer Guide

### Adding New Quality Filters

To support additional quality levels:

1. **Update the service method:**
```python
def get_quality_torrents(self, imdb_id, qualities=['480p', '720p', '1080p', '2160p']):
    """Get filtered torrents for specific qualities."""
    all_torrents = self.get_movie_torrents(imdb_id)
    return self.filter_torrents_by_quality(all_torrents, qualities)
```

2. **Update model methods:**
```python
def refresh_yts_data(self):
    yts_service = YTSService()
    torrents = yts_service.get_quality_torrents(
        self.imdb_id, 
        ['480p', '720p', '1080p', '2160p']  # Updated quality list
    )
    # ... rest of method
```

### Custom Cache Duration

To modify cache duration:

```python
def is_yts_data_fresh(self, max_age_hours=48):  # Extended to 48 hours
    """Check if YTS data is fresh (within max_age_hours)."""
    if not self.yts_last_updated:
        return False
    
    age = timezone.now() - self.yts_last_updated
    return age < timedelta(hours=max_age_hours)
```

### Batch Operations

For bulk YTS data refresh:

```python
def refresh_all_yts_data():
    """Management command to refresh YTS data for all DVDs with IMDB IDs."""
    dvds_with_imdb = DVD.objects.filter(imdb_id__isnull=False).exclude(imdb_id='')
    
    for dvd in dvds_with_imdb:
        try:
            if not dvd.is_yts_data_fresh(max_age_hours=168):  # 1 week
                dvd.refresh_yts_data()
                print(f"Refreshed YTS data for: {dvd.name}")
        except Exception as e:
            print(f"Error refreshing {dvd.name}: {e}")
```

### Error Handling Best Practices

```python
def get_movie_torrents(self, imdb_id):
    """Get torrent information for a movie by IMDB ID."""
    if not imdb_id:
        logger.warning("IMDB ID not provided")
        return []
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Validate response structure
        if not data.get('status') == 'ok':
            logger.warning(f"YTS API returned non-OK status for {imdb_id}")
            return []
        
        # ... process data
        
    except requests.Timeout:
        logger.error(f"YTS API timeout for IMDB ID: {imdb_id}")
        return []
    except requests.RequestException as e:
        logger.error(f"YTS API error for {imdb_id}: {e}")
        return []
    except (KeyError, TypeError) as e:
        logger.error(f"YTS response parsing error for {imdb_id}: {e}")
        return []
```

## Configuration

### Environment Variables

No specific environment variables are required for YTS integration. The service uses the public YTS API endpoint.

### Django Settings

Optional settings for customization:

```python
# settings.py

# YTS API Configuration
YTS_API_BASE_URL = "https://yts.mx/api/v2"
YTS_CACHE_TIMEOUT = 21600  # 6 hours
YTS_EMPTY_CACHE_TIMEOUT = 3600  # 1 hour
YTS_DEFAULT_QUALITIES = ['720p', '1080p']
YTS_MAX_DATA_AGE_HOURS = 24

# Request Configuration
YTS_API_TIMEOUT = 10  # seconds
YTS_MAX_RETRIES = 3
```

### Cache Configuration

Ensure Django caching is properly configured:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 21600,  # 6 hours
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

## Troubleshooting

### Common Issues

#### 1. No Torrents Found

**Symptoms:** Empty torrent list despite movie being available on YTS

**Causes:**
- Incorrect or missing IMDB ID
- Movie not available in YTS database
- API connectivity issues

**Solutions:**
1. Verify IMDB ID accuracy
2. Check YTS website manually for movie availability
3. Use the refresh button to force data update
4. Check application logs for API errors

#### 2. Stale Torrent Data

**Symptoms:** Old torrent information showing despite recent releases

**Causes:**
- Cache not refreshing automatically
- Error in refresh mechanism

**Solutions:**
1. Use manual refresh button
2. Check `yts_last_updated` timestamp
3. Verify cache configuration
4. Review error logs

#### 3. Refresh Button Not Working

**Symptoms:** JavaScript errors or no response from refresh button

**Causes:**
- CSRF token missing
- JavaScript errors
- Network connectivity issues

**Solutions:**
1. Check browser console for JavaScript errors
2. Verify CSRF token is present in the page
3. Test network connectivity
4. Check Django server logs

### Debugging

#### Enable Debug Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'yts_debug.log',
        },
    },
    'loggers': {
        'tracker.services': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

#### Test YTS Service Directly

```python
# Django shell
from tracker.services import YTSService

yts = YTSService()
torrents = yts.get_movie_torrents('tt0111161')  # The Shawshank Redemption
print(f"Found {len(torrents)} torrents")
for torrent in torrents:
    print(f"Quality: {torrent.get('quality')}, Size: {torrent.get('size')}")
```

#### Check Database State

```python
# Django shell
from tracker.models import DVD

# Find DVDs with YTS data
dvds_with_yts = DVD.objects.filter(yts_data__isnull=False)
print(f"DVDs with YTS data: {dvds_with_yts.count()}")

# Check specific DVD
dvd = DVD.objects.get(pk=1)
print(f"YTS data fresh: {dvd.is_yts_data_fresh()}")
print(f"Last updated: {dvd.yts_last_updated}")
print(f"Cached torrents: {len(dvd.get_cached_torrents())}")
```

## Security Considerations

### Data Validation

- All torrent data is sanitized before storage
- URLs are validated before display
- User input is properly escaped in templates

### External API Security

- API requests use HTTPS exclusively
- Timeout protection prevents hanging requests
- Error handling prevents information disclosure

### User Privacy

- No user data is sent to YTS API
- Only IMDB IDs are transmitted
- All communication is logged for debugging

### Content Disclaimer

The application provides links to torrents but does not:
- Host any copyrighted content
- Facilitate direct downloads
- Store torrent files locally
- Encourage piracy

Users are responsible for ensuring their use complies with local laws and copyright regulations.

---

*This documentation covers the complete YTS integration and torrent functionality in the DVD Collection Tracker application. For additional technical details, refer to the source code in `tracker/services.py` and `tracker/models.py`.*