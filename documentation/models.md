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
| `tmdb_api_key` | CharField | API key for The Movie Database (TMDB) | max_length=255, blank=True |
| `created_at` | DateTimeField | Record creation timestamp | auto_now_add=True |
| `updated_at` | DateTimeField | Record last update timestamp | auto_now=True |

### Key Features

- **Singleton Pattern**: Only one settings instance exists (pk=1)
- **Class Method**: `get_settings()` returns the singleton instance, creating it if needed

### Usage Example

```python
settings = AppSettings.get_settings()
api_key = settings.tmdb_api_key
```

---

## DVD Model

The `DVD` model represents individual DVD entries in the collection, supporting physical discs, downloads, and rips with comprehensive metadata from TMDB.

### Field Descriptions

#### Basic Information

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `name` | CharField | Movie title | - | max_length=255, required |
| `status` | CharField | Current status of the DVD | 'kept' | Choices: 'kept', 'disposed' |
| `media_type` | CharField | Type of media | 'physical' | Choices: 'physical', 'download', 'rip' |
| `is_downloaded` | BooleanField | Download status flag | False | - |

#### DVD-Specific Properties

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `is_tartan_dvd` | BooleanField | Tartan DVD release indicator | False | - |
| `is_box_set` | BooleanField | Box set membership flag | False | - |
| `box_set_name` | CharField | Box set name | '' | max_length=255, blank=True |
| `is_unopened` | BooleanField | Unopened status | False | - |
| `is_unwatched` | BooleanField | Viewing status | False | - |
| `storage_box` | CharField | Physical storage location | '' | max_length=100, blank=True |

#### Duplicate Management

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `copy_number` | PositiveSmallIntegerField | Copy identifier for duplicates | 1 | minimum=1 |
| `duplicate_notes` | CharField | Notes about this specific copy | '' | max_length=255, blank=True |

#### TMDB Integration

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `tmdb_id` | IntegerField | TMDB movie identifier | null | null=True, blank=True |
| `imdb_id` | CharField | IMDB identifier | '' | max_length=20, blank=True |
| `poster` | ImageField | Movie poster image | null | upload_to='posters/', null=True |
| `overview` | TextField | Movie plot synopsis | '' | blank=True |
| `release_year` | IntegerField | Release year | null | null=True, blank=True |
| `genres` | CharField | Comma-separated genres | '' | max_length=255, blank=True |
| `runtime` | IntegerField | Runtime in minutes | null | null=True, blank=True |
| `rating` | DecimalField | Movie rating | null | max_digits=3, decimal_places=1 |
| `uk_certification` | CharField | UK film certification | '' | max_length=10, blank=True |
| `tmdb_user_score` | DecimalField | TMDB user score (0-10) | null | max_digits=4, decimal_places=2 |
| `original_language` | CharField | Original language code | '' | max_length=10, blank=True |
| `budget` | BigIntegerField | Production budget (USD) | null | null=True, blank=True |
| `revenue` | BigIntegerField | Box office revenue (USD) | null | null=True, blank=True |
| `production_companies` | TextField | Comma-separated companies | '' | blank=True |
| `tagline` | CharField | Movie tagline | '' | max_length=255, blank=True |

#### Timestamps

| Field | Type | Description | Default | Constraints |
|-------|------|-------------|---------|-------------|
| `created_at` | DateTimeField | Record creation time | auto_now_add | auto_now_add=True |
| `updated_at` | DateTimeField | Last modification time | auto_now | auto_now=True |

### Choice Fields

#### Status Choices

- **kept**: DVD is currently in the collection
- **disposed**: DVD has been removed from collection

#### Media Type Choices

- **physical**: Physical DVD disc
- **download**: Digital download file
- **rip**: Ripped from physical media

### Model Methods

#### Data Access Methods

**`get_genres_list()`**

- Returns genres as a Python list by splitting the comma-separated `genres` field
- Returns empty list if no genres are set

**`get_production_companies_list()`**

- Returns production companies as a Python list
- Splits the comma-separated `production_companies` field
- Returns empty list if no companies are set

#### Display Helper Methods

**`get_status_display_class()`**

- Returns CSS class for status badge styling
- Mapping: 'kept' → 'success', 'disposed' → 'danger'

**`get_media_type_display_class()`**

- Returns CSS class for media type badge styling
- Mapping: 'physical' → 'primary', 'download' → 'info', 'rip' → 'warning'

**`get_special_features_badges()`**

- Returns list of badge dictionaries for special features
- Each badge contains 'text' and 'class' keys
- Includes badges for: Tartan DVDs, Box Sets, Unopened, Unwatched, Copy numbers

#### URL Methods

**`get_absolute_url()`**

- Returns the canonical URL for the DVD detail view
- Uses Django's `reverse()` with 'tracker:dvd_detail' and the DVD's primary key

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
    runtime=136
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

#### Displaying Movie Information

```python
# Get formatted data for templates
genres = dvd.get_genres_list()
badges = dvd.get_special_features_badges()
copy_info = dvd.get_copy_display()
status_class = dvd.get_status_display_class()
```

---

## Database Considerations

### Indexing Recommendations

For optimal performance, consider adding database indexes on frequently queried fields:

- `tmdb_id` (for duplicate detection)
- `name` (for searching and duplicate fallback)
- `status` (for filtering collections)
- `media_type` (for filtering by media type)
- `created_at` (already used in default ordering)

### Data Integrity

- TMDB ID should be unique per movie but allows nulls for manual entries
- Copy numbers should be managed through the model methods to ensure consistency
- The `AppSettings` singleton pattern prevents configuration duplication

### Storage Requirements

- Poster images are stored in `media/posters/` directory
- Large text fields (`overview`, `production_companies`) support variable-length content
- Numeric fields use appropriate precision for financial data (`budget`, `revenue`)
