# Django Models Documentation

This document provides detailed information about the Django models used in the DVD Collection Tracker application.

## Table of Contents

- [AppSettings Model](#appsettings-model)
- [DVD Model](#dvd-model)
  - [Field Descriptions](#field-descriptions)
  - [Model Methods](#model-methods)
  - [Choice Fields](#choice-fields)
  - [Relationships & Duplicates](#relationships--duplicates)

---

## AppSettings Model

The `AppSettings` model stores application-wide configuration settings, implemented as a singleton pattern.

### Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `tmdb_api_key` | CharField | API key for The Movie Database (TMDB) | max_length=255, blank=True, help_text="TMDB API Key for fetching movie data" |
| `created_at` | DateTimeField | Record creation timestamp | auto_now_add=True |
| `updated_at` | DateTimeField | Record last update timestamp | auto_now=True |

### Key Features

- **Singleton Pattern**: Only one settings instance exists (pk=1)
- **Class Method**: `get_settings()` returns the singleton instance, creating it if needed
- **Verbose Names**: Configured for Django admin display

### Usage Example

```python
settings = AppSettings.get_settings()
api_key = settings.tmdb_api_key
```

---

## DVD Model

The `DVD` model represents individual DVD entries in the collection, supporting physical discs, downloads, and rips with comprehensive metadata from TMDB and YTS torrent integration.

### Field Descriptions

#### Basic Information

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `name` | CharField | Movie title | - | max_length=255, required |
| `status` | CharField | Current status of the DVD | 'kept' | Choices: 'kept', 'disposed', 'unboxed' |
| `media_type` | CharField | Type of media | 'physical' | Choices: 'physical', 'download', 'rip' |
| `is_downloaded` | BooleanField | Download status flag | False | help_text='Has this DVD been downloaded?' |

#### DVD-Specific Properties

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `is_tartan_dvd` | BooleanField | Tartan DVD release indicator | False | help_text='Is this a Tartan DVD release?' |
| `is_box_set` | BooleanField | Box set membership flag | False | help_text='Is this part of a box set?' |
| `box_set_name` | CharField | Box set name | '' | max_length=255, blank=True, help_text='Name of the box set (if applicable)' |
| `is_unopened` | BooleanField | Unopened status | False | help_text='Is this DVD still unopened?' |
| `is_unwatched` | BooleanField | Viewing status | False | help_text='Have you not watched this movie yet?' |
| `storage_box` | CharField | Physical storage location | '' | max_length=100, blank=True, help_text='Storage box location (for kept items)' |
| `location` | CharField | Location identifier | '' | max_length=255, blank=True, help_text='Location (for unboxed items)' |

#### Duplicate Management

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `copy_number` | PositiveSmallIntegerField | Copy identifier for duplicates | 1 | minimum=1, help_text='Copy number (1, 2, 3, etc.) for duplicate movies' |
| `duplicate_notes` | CharField | Notes about this specific copy | '' | max_length=255, blank=True, help_text='Notes about this copy (e.g., "Director\'s Cut", "Region 2", "Special Edition")' |

#### TMDB Integration

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `tmdb_id` | IntegerField | TMDB movie identifier | null | null=True, blank=True |
| `imdb_id` | CharField | IMDB identifier | '' | max_length=20, blank=True, help_text="IMDB ID (e.g., tt1234567)" |
| `poster` | ImageField | Movie poster image | null | upload_to='posters/', null=True, blank=True |
| `overview` | TextField | Movie plot synopsis | '' | blank=True |
| `release_year` | IntegerField | Release year | null | null=True, blank=True |
| `genres` | CharField | Comma-separated genres | '' | max_length=255, blank=True |
| `runtime` | IntegerField | Runtime in minutes | null | null=True, blank=True |
| `rating` | DecimalField | Movie rating | null | max_digits=3, decimal_places=1, null=True, blank=True |
| `uk_certification` | CharField | UK film certification | '' | max_length=10, blank=True, help_text="UK film certification (e.g., U, PG, 12, 15, 18)" |
| `tmdb_user_score` | DecimalField | TMDB user score (0-10) | null | max_digits=4, decimal_places=2, null=True, blank=True, help_text="TMDB user score out of 10" |
| `original_language` | CharField | Original language code | '' | max_length=10, blank=True, help_text="Original language of the movie" |
| `budget` | BigIntegerField | Production budget (USD) | null | null=True, blank=True, help_text="Movie budget in USD" |
| `revenue` | BigIntegerField | Box office revenue (USD) | null | null=True, blank=True, help_text="Movie revenue in USD" |
| `production_companies` | TextField | Comma-separated companies | '' | blank=True, help_text="Production companies, comma-separated" |
| `tagline` | CharField | Movie tagline | '' | max_length=255, blank=True |
| `director` | CharField | Movie director | '' | max_length=255, blank=True, help_text="Director of the movie" |

#### YTS Torrent Integration

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `yts_data` | JSONField | Cached YTS torrent data | null | blank=True, null=True, help_text="Cached YTS torrent data" |
| `yts_last_updated` | DateTimeField | YTS data refresh timestamp | null | blank=True, null=True, help_text="When YTS data was last refreshed" |
| `has_cached_torrents` | BooleanField | Torrent availability flag | False | help_text="Whether this DVD has torrents available (cached result for fast filtering)" |

#### Timestamps

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `created_at` | DateTimeField | Record creation time | auto_now_add | auto_now_add=True |
| `updated_at` | DateTimeField | Last modification time | auto_now | auto_now=True |

### Choice Fields

#### Status Choices

- **kept**: DVD is currently in the collection
- **disposed**: DVD has been removed from collection
- **unboxed**: DVD has been removed from storage box and assigned a location number

#### Media Type Choices

- **physical**: Physical DVD disc
- **download**: Digital download file
- **rip**: Ripped from physical media

### Model Methods

#### Validation Methods

**`clean()`**

- Custom validation for the DVD model
- Validates location field for unboxed DVDs:
  - Checks if location is already taken by another DVD
  - Ensures location is a valid number for unboxed DVDs
- Raises ValidationError for constraint violations

#### Data Access Methods

**`get_genres_list()`**

- Returns genres as a Python list by splitting the comma-separated `genres` field
- Returns empty list if no genres are set

**`get_production_companies_list()`**

- Returns production companies as a Python list
- Splits the comma-separated `production_companies` field
- Returns empty list if no companies are set

#### Financial Analysis

**`profit` (property)**

- Calculates profit as revenue minus budget
- Returns None if either revenue or budget is None
- Useful for financial analysis of movies

#### Display Helper Methods

**`get_status_display_class()`**

- Returns CSS class for status badge styling
- Mapping: 'kept' → 'success', 'disposed' → 'danger', 'unboxed' → 'warning'

**`get_media_type_display_class()`**

- Returns CSS class for media type badge styling
- Mapping: 'physical' → 'primary', 'download' → 'info', 'rip' → 'warning'

**`get_special_features_badges()`**

- Returns list of badge dictionaries for special features
- Each badge contains 'text' and 'class' keys
- Includes badges for: Tartan DVDs, Box Sets, Unopened, Unwatched, Copy numbers, Torrent availability

#### YTS Torrent Methods

**`has_torrents()`**

- Check if this DVD has available torrent links (optimized for filtering)
- Only checks cached data to prevent performance issues during bulk filtering
- Returns boolean based on `yts_data` content

**`get_cached_torrents()`**

- Returns cached YTS torrent data as a list
- Returns empty list if no cached data available

**`is_yts_data_fresh(max_age_hours=24)`**

- Checks if YTS data is fresh (within max_age_hours)
- Returns False if no last_updated timestamp exists
- Useful for determining when to refresh torrent data

**`refresh_yts_data()`**

- Refreshes YTS torrent data from the API
- Updates cached availability flag (`has_cached_torrents`)
- Returns True on success, False if no IMDB ID available

**`update_torrent_availability()`**

- Updates the cached torrent availability flag without making API calls
- Only updates based on existing cached data
- Used for background updates to maintain performance

#### URL Methods

**`get_absolute_url()`**

- Returns the canonical URL for the DVD detail view
- Uses Django's `reverse()` with 'tracker:dvd_detail' and the DVD's primary key

#### Location Management (Class Methods)

**`get_next_location_number()`**

- Class method that returns the next available location number for unboxed DVDs
- Uses raw SQL to properly cast location to integer and get the maximum
- Returns max_location + 1

**`is_location_taken(location_number, exclude_pk=None)`**

- Class method to check if a location number is already taken
- Filters by unboxed status and exact location match
- Can exclude a specific primary key from the check

**`get_next_sequential_locations(count)`**

- Class method that returns a list of sequential location numbers
- Useful for bulk operations requiring multiple location assignments
- Returns list of strings starting from next available location

### Relationships & Duplicates

The DVD model includes sophisticated duplicate management functionality:

#### Duplicate Detection Methods

**`get_duplicate_copies()`**

- Returns QuerySet of all copies of this movie (including current instance)
- Primary matching by `tmdb_id` (most reliable)
- Fallback matching by `name` and `release_year` if no TMDB ID
- Ordered by `copy_number`

**`get_other_copies()`**

- Returns QuerySet of other copies (excluding current instance)
- Uses `get_duplicate_copies()` with current DVD excluded

**`has_duplicates()`**

- Returns boolean indicating if other copies exist
- Efficient check using `exists()` on `get_other_copies()`

#### Copy Management Methods

**`get_next_copy_number()`**

- Calculates the next available copy number for this movie
- Returns 1 if no existing copies found
- Otherwise returns highest existing copy number + 1

**`get_copy_display()`**

- Returns formatted string for displaying copy information
- Hides copy number if it's the only copy (copy_number=1, no duplicates)
- Format: "Copy #N" or "Copy #N (notes)" if duplicate_notes exist
- Returns empty string for single copies

### Model Configuration

#### Meta Options

- **ordering**: `['-created_at']` - Newest records first
- **verbose_name**: Auto-generated from model name
- **verbose_name_plural**: Auto-generated from model name

#### String Representation

- `__str__()` method returns the `name` field
- Provides clear identification in Django admin and debugging

### Usage Examples

#### Creating a DVD Entry

```python
dvd = DVD.objects.create(
    name="The Matrix",
    status="kept",
    media_type="physical",
    tmdb_id=603,
    release_year=1999,
    genres="Action, Science Fiction",
    runtime=136,
    director="The Wachowskis"
)
```

#### Working with Duplicates

```python
# Check for duplicates
if dvd.has_duplicates():
    other_copies = dvd.get_other_copies()
    print(f"Found {other_copies.count()} other copies")

# Add a new copy
new_copy = DVD.objects.create(
    name=dvd.name,
    tmdb_id=dvd.tmdb_id,
    copy_number=dvd.get_next_copy_number(),
    duplicate_notes="Director's Cut",
    media_type="download"
)
```

#### Managing Unboxed DVDs

```python
# Get next available location
next_location = DVD.get_next_location_number()

# Create unboxed DVD
unboxed_dvd = DVD.objects.create(
    name="Inception",
    status="unboxed",
    location=str(next_location)
)

# Bulk location assignment
locations = DVD.get_next_sequential_locations(5)
for i, location in enumerate(locations):
    DVD.objects.create(
        name=f"Movie {i+1}",
        status="unboxed",
        location=location
    )
```

#### Working with YTS Torrents

```python
# Check and refresh torrent data
if not dvd.is_yts_data_fresh():
    dvd.refresh_yts_data()

# Get cached torrents
torrents = dvd.get_cached_torrents()
if torrents:
    print(f"Found {len(torrents)} torrents")

# Check torrent availability (fast filtering)
if dvd.has_torrents():
    print("Torrents available!")
```

#### Displaying Movie Information

```python
# Get formatted data for templates
genres = dvd.get_genres_list()
companies = dvd.get_production_companies_list()
badges = dvd.get_special_features_badges()
copy_info = dvd.get_copy_display()
status_class = dvd.get_status_display_class()

# Calculate profit
if dvd.profit is not None:
    profit_millions = dvd.profit / 1_000_000
    print(f"Profit: ${profit_millions:.1f}M")
```

---

## Database Considerations

### Indexing Recommendations

For optimal performance, consider adding database indexes on frequently queried fields:

- `tmdb_id` (for duplicate detection)
- `name` (for searching and duplicate fallback)
- `status` (for filtering collections)
- `media_type` (for filtering by media type)
- `location` (for unboxed DVD management)
- `has_cached_torrents` (for torrent filtering)
- `created_at` (already used in default ordering)

### Data Integrity

- TMDB ID should be unique per movie but allows nulls for manual entries
- Copy numbers should be managed through the model methods to ensure consistency
- Location numbers for unboxed DVDs are validated to prevent duplicates
- YTS data is cached with timestamps to prevent excessive API calls
- The `AppSettings` singleton pattern prevents configuration duplication

### Storage Requirements

- Poster images are stored in `media/posters/` directory
- Large text fields (`overview`, `production_companies`) support variable-length content
- Numeric fields use appropriate precision for financial data (`budget`, `revenue`)
- JSON field stores torrent data efficiently with native database support
