# Bulk Upload Feature - Technical Documentation

## Overview

The bulk-upload feature allows users to add multiple movies to their DVD collection simultaneously from a simple text list. This document provides comprehensive technical details for AI assistants and developers working on improving or extending the bulk upload functionality.

## Feature Summary

- **Primary URL**: `/bulk-upload/` (mapped to `views.bulk_upload`)
- **HTTP Methods**: GET (form display), POST (processing)
- **Template**: `tracker/bulk_upload.html`
- **Results Template**: `tracker/bulk_upload_results.html`
- **Form Class**: `BulkUploadForm` in `tracker/forms.py`
- **Main Handler**: `bulk_upload()` view function in `tracker/views.py`

## Architecture Overview

```text
User Input (Text List)
        ↓
BulkUploadForm Validation
        ↓
Movie Title Parsing
        ↓
TMDB API Search (per title)
        ↓
Movie Details Retrieval
        ↓
DVD Model Creation
        ↓
Poster Download
        ↓
Results Display
```

## Core Components

### 1. Form Definition (`BulkUploadForm`)

**Location**: `tracker/forms.py` (lines 205-311)

**Primary Fields**:

- `movie_list`: Large textarea for newline-separated movie titles
- `default_status`: Choice field (kept/disposed) applied to all uploads
- `default_media_type`: Choice field (physical/download/rip) applied to all uploads
- `skip_existing`: Boolean to skip movies already in collection

**DVD-Specific Default Fields**:

- `default_is_tartan_dvd`: Mark all as Tartan DVD releases
- `default_is_box_set`: Mark all as part of box set
- `default_box_set_name`: Default box set name
- `default_is_unopened`: Mark all as unopened
- `default_is_unwatched`: Mark all as unwatched (default: True)
- `default_storage_box`: Default storage location for kept items

**Form Widgets**: Bootstrap-compatible form controls with appropriate styling and help text.

### 2. View Handler (`bulk_upload()`)

**Location**: `tracker/views.py` (lines 381-486)

**Processing Flow**:

#### GET Request
Returns form for user input with sample movie lists in JavaScript.

#### POST Request Processing
1. **Form Validation**: Validate `BulkUploadForm` with user input
2. **Data Extraction**: Extract form fields and movie title list
3. **Title Parsing**: Split textarea content by newlines, strip whitespace
4. **TMDB Integration**: For each title:
   - Search TMDB using `TMDBService.search_movies()`
   - Take first (most relevant) result
   - Check for existing DVD with same TMDB ID
   - Fetch detailed movie data using `TMDBService.get_movie_details()`
   - Format data using `TMDBService.format_movie_data()`
5. **DVD Creation**: Create DVD model instances with:
   - TMDB metadata (name, overview, year, genres, etc.)
   - User-specified defaults (status, media_type, etc.)
   - DVD-specific properties (is_tartan_dvd, box_set_name, etc.)
6. **Poster Handling**: Download and save poster images
7. **Results Compilation**: Track success/failure counts
8. **User Feedback**: Display Django messages and results page

### 3. TMDB Service Integration (`TMDBService`)

**Location**: `tracker/services.py`

**Key Methods Used**:

#### `search_movies(query, page=1)`
- **Purpose**: Search TMDB for movies by title
- **Caching**: 1 hour cache with key `tmdb_search_{query}_{page}`
- **Returns**: Dictionary with 'results' array and metadata
- **Error Handling**: Returns empty results on API failure

#### `get_movie_details(movie_id)`
- **Purpose**: Fetch comprehensive movie data including external IDs
- **Caching**: 24 hour cache with key `tmdb_movie_{movie_id}`
- **Returns**: Complete movie object with all TMDB fields
- **External Data**: Fetches IMDB ID and UK certification

#### `format_movie_data(movie_data)`
- **Purpose**: Convert raw TMDB data to DVD model format
- **Processing**: 
  - Extracts year from release_date
  - Joins genres array into comma-separated string
  - Maps TMDB fields to DVD model fields
- **Returns**: Dictionary ready for DVD.objects.create()

#### `download_poster(dvd, poster_url)`
- **Purpose**: Download and save poster image to DVD instance
- **Storage**: Saves to `media/posters/` directory
- **Error Handling**: Logs failures, continues processing

### 4. DVD Model Integration

**Location**: `tracker/models.py`

**Relevant Fields for Bulk Upload**:

#### Core Fields
- `name`: Movie title from TMDB
- `overview`: Plot summary
- `release_year`: Extracted from TMDB release_date
- `genres`: Comma-separated string
- `runtime`: Minutes
- `rating`: TMDB vote_average

#### Collection Management
- `status`: User-specified default (kept/disposed)
- `media_type`: User-specified default (physical/download/rip)
- `storage_box`: Applied only if status='kept'

#### DVD Properties
- `is_tartan_dvd`: Applied from form default
- `is_box_set`: Applied from form default
- `box_set_name`: Applied if is_box_set=True
- `is_unopened`: Applied from form default
- `is_unwatched`: Applied from form default (typically True)

#### TMDB Integration
- `tmdb_id`: Primary identifier for duplicate detection
- `imdb_id`: Fetched from TMDB external_ids
- `poster`: ImageField populated by poster download

### 5. Template System

#### Primary Template (`bulk_upload.html`)
**Features**:
- Bootstrap form with collapsible sections
- Sample movie lists (Action, Sci-Fi, Comedy) with JavaScript population
- Form validation and confirmation dialog
- Progress indication during submission

#### Results Template (`bulk_upload_results.html`)
**Data Display**:
- Success count with list of added movies
- Skipped count with duplicate information
- Not found count with failed search terms
- Error count with specific error messages
- Navigation back to bulk upload or collection view

## Error Handling & Edge Cases

### 1. TMDB API Failures
- **Network Issues**: Graceful degradation with error logging
- **Rate Limiting**: Built-in caching reduces API calls
- **Invalid Results**: Empty results handled as "not found"

### 2. Duplicate Detection
- **Logic**: Check `DVD.objects.filter(tmdb_id=tmdb_id).exists()`
- **User Control**: `skip_existing` flag controls behavior
- **Feedback**: Shows original title and existing movie name

### 3. Data Validation
- **Form Validation**: Django form validation for all fields
- **Movie Title Parsing**: Handles empty lines and whitespace
- **TMDB Data**: Handles missing fields gracefully

### 4. File Operations
- **Poster Downloads**: Continue processing on poster failures
- **Storage**: Uses Django's file storage system
- **Cleanup**: No orphaned files (posters tied to DVD instances)

## Performance Considerations

### 1. Caching Strategy
- **Search Results**: 1 hour cache for TMDB searches
- **Movie Details**: 24 hour cache for detailed movie data
- **External IDs**: Cached with movie details

### 2. Database Operations
- **Bulk Processing**: Individual `DVD.objects.create()` calls
- **Optimization Opportunity**: Could be enhanced with `bulk_create()`
- **Transactions**: No explicit transaction management (runs in autocommit)

### 3. API Rate Limiting
- **TMDB Limits**: 40 requests/second, 1M requests/day
- **Current Usage**: 2-3 API calls per movie (search + details + external_ids)
- **Mitigation**: Aggressive caching reduces repeat calls

## User Experience Flow

### 1. Form Input Stage
1. User navigates to `/bulk-upload/`
2. Optionally uses sample lists to populate textarea
3. Configures default settings for status, media type, DVD properties
4. Submits form with confirmation dialog

### 2. Processing Stage
1. Form validation occurs
2. Loading spinner shows during processing
3. Each movie processed sequentially
4. Poster downloads happen asynchronously

### 3. Results Stage
1. Results categorized by outcome
2. Success/error counts displayed
3. Detailed lists for each category
4. Actions to upload more or view collection

## Extension Points & Improvement Opportunities

### 1. Batch Processing
**Current**: Sequential processing of each movie
**Enhancement**: Implement async processing or background tasks
**Benefits**: Better user experience for large lists

### 2. Enhanced Matching
**Current**: Takes first TMDB search result
**Enhancement**: Fuzzy matching, year-based disambiguation
**Benefits**: More accurate movie identification

### 3. Validation Improvements
**Current**: Basic form validation
**Enhancement**: Pre-submission validation, duplicate preview
**Benefits**: Reduced processing failures

### 4. Import Sources
**Current**: Manual text entry only
**Enhancement**: File upload (CSV, TXT), URL import
**Benefits**: Support for larger datasets

### 5. Progress Feedback
**Current**: Simple loading spinner
**Enhancement**: Real-time progress with status updates
**Benefits**: Better user experience for large uploads

## Manual Script Alternative

### Interactive Bulk Upload (`manual_scripts/bulk_upload_interactive.py`)

**Purpose**: Command-line alternative with user interaction
**Features**:
- Interactive search result selection
- Manual TMDB ID input option
- Individual movie confirmation
- Same backend integration (TMDBService, DVD model)

**Use Cases**:
- Problematic movie titles requiring manual intervention
- Development and testing scenarios
- Power users preferring command-line interface

## Code Examples

### Adding a New Default Field

```python
# 1. Add to BulkUploadForm (forms.py)
default_new_field = forms.BooleanField(
    required=False,
    initial=False,
    widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    help_text='New field description'
)

# 2. Extract in view (views.py)
default_new_field = form.cleaned_data['default_new_field']

# 3. Apply in DVD creation
dvd = DVD.objects.create(
    # ... existing fields ...
    new_field=default_new_field,
)

# 4. Add to template (bulk_upload.html)
<div class="form-check">
    {{ form.default_new_field }}
    <label class="form-check-label" for="{{ form.default_new_field.id_for_label }}">
        New Field
    </label>
    <div class="form-text">{{ form.default_new_field.help_text }}</div>
</div>
```

### Enhancing Movie Search Logic

```python
def enhanced_movie_search(tmdb_service, title):
    """Enhanced search with year extraction and fuzzy matching."""
    # Extract year from title if present
    year_match = re.search(r'\((\d{4})\)|\b(\d{4})\b', title)
    year = year_match.group(1) or year_match.group(2) if year_match else None
    
    # Clean title
    clean_title = re.sub(r'\(?\d{4}\)?', '', title).strip()
    
    # Search TMDB
    search_results = tmdb_service.search_movies(clean_title)
    movies = search_results.get('results', [])
    
    if year and movies:
        # Filter by year if available
        year_matches = [m for m in movies if m.get('release_date', '').startswith(year)]
        if year_matches:
            return year_matches[0]
    
    return movies[0] if movies else None
```

## API Endpoints Related to Bulk Upload

### Search Endpoint (`/api/search/`)
- **Purpose**: AJAX movie search for form assistance
- **Usage**: Could be extended for bulk upload preview
- **Handler**: `search_tmdb_ajax()` view

### Bulk Update Endpoint (`/api/bulk-update-dvd/`)
- **Purpose**: Individual DVD field updates
- **Usage**: Could support post-upload corrections
- **Handler**: `bulk_update_dvd()` view

## Database Schema Impact

### Indexes for Performance
```sql
-- Recommended indexes for bulk upload operations
CREATE INDEX idx_dvd_tmdb_id ON tracker_dvd(tmdb_id);
CREATE INDEX idx_dvd_name_year ON tracker_dvd(name, release_year);
CREATE INDEX idx_dvd_status_media ON tracker_dvd(status, media_type);
```

### Constraint Considerations
- No unique constraint on `tmdb_id` (allows duplicates with different copy_number)
- No unique constraint on `name` (allows multiple copies and versions)

## Testing Considerations

### Unit Tests
- Form validation with various inputs
- TMDB service integration with mocked API responses
- DVD creation with different field combinations

### Integration Tests
- End-to-end bulk upload process
- Error handling scenarios
- Poster download failures

### Performance Tests
- Large movie list processing
- API rate limit scenarios
- Database performance with bulk operations

## Security Considerations

### Input Validation
- Movie titles sanitized through Django form system
- No direct SQL injection risks (using ORM)
- File uploads (posters) handled by Django's secure file handling

### API Key Protection
- TMDB API key stored in database (AppSettings model)
- No API key exposure in client-side code
- Error messages don't leak API details

## Monitoring & Logging

### Current Logging
- TMDB API errors logged at ERROR level
- Poster download failures logged at ERROR level
- General processing exceptions logged with context

### Recommended Monitoring
- Bulk upload success/failure rates
- TMDB API response times and failures
- Large upload processing times
- User engagement with feature

---

This technical documentation provides comprehensive coverage of the bulk-upload feature architecture, implementation details, and extension points for AI assistants and developers working on enhancements or maintenance.