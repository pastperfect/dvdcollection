# Database Schema

Complete documentation of the database structure and data models for the DVD Collection Tracker.

## 📊 Overview

The DVD Collection Tracker uses a straightforward relational database schema optimized for single-user collection management. The schema consists of two primary models with focused responsibilities.

### Database Engine Support

| Database | Status | Notes |
|----------|--------|-------|
| **SQLite** | ✅ Primary | Default for development and small collections |
| **PostgreSQL** | ✅ Recommended | Best for production and larger collections |
| **MySQL/MariaDB** | ✅ Supported | Alternative production option |
| **Oracle** | ⚠️ Untested | Should work with Django ORM |
| **SQL Server** | ⚠️ Untested | Requires additional drivers |

## 🎬 DVD Model

The core model storing all movie and collection information.

### Table Structure

```sql
CREATE TABLE "tracker_dvd" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "is_downloaded" bool NOT NULL,
    "name" varchar(255) NOT NULL,
    "status" varchar(10) NOT NULL,
    "media_type" varchar(10) NOT NULL,
    "is_tartan_dvd" bool NOT NULL,
    "is_box_set" bool NOT NULL,
    "box_set_name" varchar(255) NOT NULL,
    "is_unopened" bool NOT NULL,
    "is_unwatched" bool NOT NULL,
    "storage_box" varchar(100) NOT NULL,
    "tmdb_id" integer NULL,
    "imdb_id" varchar(20) NOT NULL,
    "poster" varchar(100) NULL,
    "overview" text NOT NULL,
    "release_year" integer NULL,
    "genres" varchar(255) NOT NULL,
    "runtime" integer NULL,
    "rating" decimal(3,1) NULL,
    "uk_certification" varchar(10) NOT NULL,
    "tmdb_user_score" decimal(4,2) NULL,
    "original_language" varchar(10) NOT NULL,
    "budget" bigint NULL,
    "revenue" bigint NULL,
    "production_companies" text NOT NULL,
    "tagline" varchar(255) NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);
```

### Field Definitions

#### Primary Key
| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key, auto-incrementing integer |

#### Core Movie Information
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | CharField(255) | NOT NULL | Movie title as stored in collection |
| `overview` | TextField | NULL | Plot summary from TMDB |
| `release_year` | IntegerField | NULL | Year of original release |
| `runtime` | IntegerField | NULL | Duration in minutes |
| `genres` | CharField(255) | NULL | Comma-separated genre list |
| `tagline` | CharField(255) | NULL | Movie tagline/slogan |

#### Collection Management
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | CharField(10) | 'kept' | Current ownership status |
| `media_type` | CharField(10) | 'physical' | Format type |
| `storage_box` | CharField(100) | '' | Physical storage location |
| `is_downloaded` | BooleanField | False | Download completion flag |

#### Special Properties
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `is_tartan_dvd` | BooleanField | False | Tartan Asia Extreme release |
| `is_box_set` | BooleanField | False | Part of a collection |
| `box_set_name` | CharField(255) | '' | Collection/series name |
| `is_unopened` | BooleanField | False | Sealed/mint condition |
| `is_unwatched` | BooleanField | False | Not yet viewed |

#### External References
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `tmdb_id` | IntegerField | NULL | TMDB movie identifier |
| `imdb_id` | CharField(20) | NULL | IMDB identifier (e.g., tt0133093) |
| `poster` | ImageField | NULL | Local poster file path |

#### Ratings and Scores
| Field | Type | Precision | Description |
|-------|------|-----------|-------------|
| `rating` | DecimalField | 3,1 | TMDB average rating (0.0-10.0) |
| `tmdb_user_score` | DecimalField | 4,2 | TMDB user score (0.00-10.00) |
| `uk_certification` | CharField(10) | NULL | UK film rating (U, PG, 12, 15, 18) |

#### Production Information
| Field | Type | Description |
|-------|------|-------------|
| `original_language` | CharField(10) | ISO 639-1 language code |
| `budget` | BigIntegerField | Production budget in USD |
| `revenue` | BigIntegerField | Box office revenue in USD |
| `production_companies` | TextField | Comma-separated company list |

#### Audit Fields
| Field | Type | Auto | Description |
|-------|------|------|-------------|
| `created_at` | DateTimeField | add | Record creation timestamp |
| `updated_at` | DateTimeField | update | Last modification timestamp |

### Choice Fields

#### Status Choices
```python
STATUS_CHOICES = [
    ('kept', 'Kept'),
    ('disposed', 'Disposed'),
]
```

#### Media Type Choices
```python
MEDIA_TYPE_CHOICES = [
    ('physical', 'Physical'),
    ('download', 'Download'),
    ('rip', 'Rip'),
]
```

### Database Indexes

```sql
-- Default Django indexes
CREATE INDEX "tracker_dvd_name_idx" ON "tracker_dvd" ("name");
CREATE INDEX "tracker_dvd_tmdb_id_idx" ON "tracker_dvd" ("tmdb_id");
CREATE INDEX "tracker_dvd_status_idx" ON "tracker_dvd" ("status");
CREATE INDEX "tracker_dvd_media_type_idx" ON "tracker_dvd" ("media_type");
CREATE INDEX "tracker_dvd_created_at_idx" ON "tracker_dvd" ("created_at");

-- Custom indexes for performance
CREATE INDEX "tracker_dvd_is_box_set_idx" ON "tracker_dvd" ("is_box_set");
CREATE INDEX "tracker_dvd_box_set_name_idx" ON "tracker_dvd" ("box_set_name");
CREATE INDEX "tracker_dvd_is_tartan_dvd_idx" ON "tracker_dvd" ("is_tartan_dvd");
CREATE INDEX "tracker_dvd_release_year_idx" ON "tracker_dvd" ("release_year");
```

### Constraints

#### Check Constraints
```sql
-- Status validation
ALTER TABLE tracker_dvd ADD CONSTRAINT status_check 
CHECK (status IN ('kept', 'disposed'));

-- Media type validation
ALTER TABLE tracker_dvd ADD CONSTRAINT media_type_check 
CHECK (media_type IN ('physical', 'download', 'rip'));

-- Rating range validation
ALTER TABLE tracker_dvd ADD CONSTRAINT rating_range_check 
CHECK (rating >= 0.0 AND rating <= 10.0);

-- Runtime validation
ALTER TABLE tracker_dvd ADD CONSTRAINT runtime_positive_check 
CHECK (runtime > 0);

-- Release year validation
ALTER TABLE tracker_dvd ADD CONSTRAINT year_range_check 
CHECK (release_year >= 1888 AND release_year <= 2050);
```

#### Unique Constraints
```sql
-- Prevent duplicate TMDB entries
CREATE UNIQUE INDEX "tracker_dvd_tmdb_id_unique" 
ON "tracker_dvd" ("tmdb_id") 
WHERE "tmdb_id" IS NOT NULL;
```

## ⚙️ AppSettings Model

Configuration storage for application-wide settings.

### Table Structure

```sql
CREATE TABLE "tracker_appsettings" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "tmdb_api_key" varchar(255) NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | AutoField | Primary key (always 1 for singleton) |
| `tmdb_api_key` | CharField(255) | TMDB API access key |
| `created_at` | DateTimeField | Settings creation time |
| `updated_at` | DateTimeField | Last configuration update |

### Singleton Pattern

The AppSettings model implements a singleton pattern:

```python
@classmethod
def get_settings(cls):
    """Get or create the settings instance."""
    settings, created = cls.objects.get_or_create(pk=1)
    return settings
```

Only one record exists with `id=1`.

## 🔗 Relationships and Foreign Keys

### Current Schema
The current schema is intentionally denormalized for simplicity:
- No foreign key relationships
- Genres stored as comma-separated values
- Production companies as text field
- Box sets identified by name matching

### Potential Normalized Schema

For larger applications, consider normalization:

```sql
-- Genre normalization
CREATE TABLE "tracker_genre" (
    "id" integer PRIMARY KEY,
    "name" varchar(100) UNIQUE NOT NULL
);

CREATE TABLE "tracker_dvd_genres" (
    "id" integer PRIMARY KEY,
    "dvd_id" integer REFERENCES "tracker_dvd" ("id"),
    "genre_id" integer REFERENCES "tracker_genre" ("id"),
    UNIQUE("dvd_id", "genre_id")
);

-- Production company normalization
CREATE TABLE "tracker_productioncompany" (
    "id" integer PRIMARY KEY,
    "name" varchar(255) UNIQUE NOT NULL
);

CREATE TABLE "tracker_dvd_production_companies" (
    "id" integer PRIMARY KEY,
    "dvd_id" integer REFERENCES "tracker_dvd" ("id"),
    "company_id" integer REFERENCES "tracker_productioncompany" ("id"),
    UNIQUE("dvd_id", "company_id")
);

-- Box set normalization
CREATE TABLE "tracker_boxset" (
    "id" integer PRIMARY KEY,
    "name" varchar(255) UNIQUE NOT NULL,
    "description" text
);

ALTER TABLE "tracker_dvd" ADD COLUMN "box_set_id" integer 
REFERENCES "tracker_boxset" ("id");
```

## 📈 Data Analytics Queries

### Collection Statistics

#### Basic Counts
```sql
-- Total collection size
SELECT COUNT(*) as total_dvds FROM tracker_dvd;

-- Status breakdown
SELECT status, COUNT(*) as count 
FROM tracker_dvd 
GROUP BY status;

-- Media type distribution
SELECT media_type, COUNT(*) as count 
FROM tracker_dvd 
GROUP BY media_type;
```

#### Advanced Analytics
```sql
-- Top genres
SELECT 
    TRIM(value) as genre,
    COUNT(*) as count
FROM tracker_dvd,
     json_each('["' || REPLACE(genres, ',', '","') || '"]')
WHERE genres != ''
GROUP BY TRIM(value)
ORDER BY count DESC
LIMIT 10;

-- Movies by decade
SELECT 
    (release_year / 10) * 10 as decade,
    COUNT(*) as count
FROM tracker_dvd 
WHERE release_year IS NOT NULL
GROUP BY decade
ORDER BY decade;

-- Average rating by media type
SELECT 
    media_type,
    AVG(rating) as avg_rating,
    COUNT(*) as count
FROM tracker_dvd 
WHERE rating IS NOT NULL
GROUP BY media_type;
```

#### Box Set Analysis
```sql
-- Largest box sets
SELECT 
    box_set_name,
    COUNT(*) as movie_count
FROM tracker_dvd 
WHERE is_box_set = 1 AND box_set_name != ''
GROUP BY box_set_name
ORDER BY movie_count DESC;

-- Box set completion rates (if you have target counts)
SELECT 
    box_set_name,
    COUNT(*) as current_count,
    -- Add target_count from external source
    ROUND(COUNT(*) * 100.0 / target_count, 1) as completion_percent
FROM tracker_dvd 
WHERE is_box_set = 1
GROUP BY box_set_name;
```

### Performance Queries

#### Search Optimization
```sql
-- Full-text search simulation
SELECT * FROM tracker_dvd 
WHERE name LIKE '%matrix%' 
   OR overview LIKE '%matrix%'
   OR genres LIKE '%matrix%'
ORDER BY 
    CASE WHEN name LIKE '%matrix%' THEN 1 ELSE 2 END,
    name;
```

#### Storage Analysis
```sql
-- Storage box utilization
SELECT 
    storage_box,
    COUNT(*) as dvd_count,
    GROUP_CONCAT(name, ', ') as movies
FROM tracker_dvd 
WHERE status = 'kept' AND storage_box != ''
GROUP BY storage_box
ORDER BY dvd_count DESC;
```

## 🛠️ Database Maintenance

### Regular Maintenance Tasks

#### Vacuum (SQLite)
```sql
-- Reclaim space and optimize
VACUUM;

-- Update statistics
ANALYZE;
```

#### Cleanup Orphaned Data
```sql
-- Find DVDs with missing poster files
SELECT id, name, poster 
FROM tracker_dvd 
WHERE poster != '' 
  AND poster IS NOT NULL;

-- Clean up empty string values
UPDATE tracker_dvd 
SET box_set_name = NULL 
WHERE box_set_name = '';

UPDATE tracker_dvd 
SET storage_box = NULL 
WHERE storage_box = '';
```

### Backup Strategies

#### Full Database Backup (SQLite)
```bash
# Simple file copy
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3

# SQL dump
sqlite3 db.sqlite3 .dump > backup_$(date +%Y%m%d).sql
```

#### Django Management Commands
```bash
# Export data
python manage.py dumpdata > backup.json

# Import data
python manage.py loaddata backup.json

# Export specific app
python manage.py dumpdata tracker > tracker_backup.json
```

## 🔄 Migrations

### Migration History

Key database changes and their migration files:

#### Initial Migration (0001)
- Created DVD model with core fields
- Created AppSettings model
- Basic indexes

#### Migration 0002 (Example Enhancement)
```python
# Adding new fields
operations = [
    migrations.AddField(
        model_name='dvd',
        name='uk_certification',
        field=models.CharField(max_length=10, blank=True),
    ),
    migrations.AddField(
        model_name='dvd',
        name='tmdb_user_score',
        field=models.DecimalField(decimal_places=2, max_digits=4, null=True, blank=True),
    ),
]
```

### Custom Migrations

#### Data Migration Example
```python
# migrations/0003_update_genres_format.py
from django.db import migrations

def update_genre_format(apps, schema_editor):
    DVD = apps.get_model('tracker', 'DVD')
    for dvd in DVD.objects.all():
        if dvd.genres:
            # Clean up genre formatting
            genres = [g.strip() for g in dvd.genres.split(',')]
            dvd.genres = ', '.join(genres)
            dvd.save()

class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0002_add_certification_fields'),
    ]
    
    operations = [
        migrations.RunPython(update_genre_format),
    ]
```

### Migration Best Practices

1. **Always backup** before running migrations
2. **Test migrations** on development data first
3. **Review SQL** generated by migrations
4. **Plan for rollbacks** when possible
5. **Monitor performance** of large data migrations

---

*Complete database schema documentation for DVD Collection Tracker. For implementation details, see the [Development Guide](development.md).*