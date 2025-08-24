# Configuration Guide

Comprehensive guide to configuring the DVD Collection Tracker for your environment and preferences.

## 🔧 Environment Setup

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the project root with the following settings:

```env
# Django Core Settings
SECRET_KEY=your_super_secret_django_key_here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost,your-domain.com

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# TMDB API Configuration
TMDB_API_KEY=your_tmdb_api_key_here
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/

# YTS API Configuration (Optional)
YTS_API_BASE_URL=https://yts.mx/api/v2

# Media and Static Files
MEDIA_ROOT=media
STATIC_ROOT=staticfiles
STATIC_URL=/static/

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/dvdtracker.log

# Email Configuration (Optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security Settings (Production)
SECURE_SSL_REDIRECT=False
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY
```

### Required Settings

#### SECRET_KEY
Django secret key for cryptographic signing.

**Generation:**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Security:** Keep this secret and never commit to version control.

#### TMDB_API_KEY
Your TMDB API key for movie data integration.

**Obtaining:**
1. Register at [TMDB](https://www.themoviedb.org/)
2. Request API key in account settings
3. Copy the v3 API key (not v4)

**Format:** 32-character hexadecimal string

### Optional Settings

#### DEBUG
Controls Django debug mode.

- **Development:** `DEBUG=True`
- **Production:** `DEBUG=False`

**Impact:**
- Error display detail
- Static file serving
- Performance optimizations

#### ALLOWED_HOSTS
Comma-separated list of allowed hostnames.

**Examples:**
```env
# Development
ALLOWED_HOSTS=127.0.0.1,localhost

# Production
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Multiple environments
ALLOWED_HOSTS=127.0.0.1,localhost,yourdomain.com
```

## 🗄️ Database Configuration

### SQLite (Default)

Perfect for single-user installations and development.

```env
DATABASE_URL=sqlite:///db.sqlite3
```

**Characteristics:**
- ✅ No additional setup required
- ✅ File-based, easy to backup
- ✅ Perfect for small to medium collections
- ❌ Not suitable for high concurrency
- ❌ Limited for multiple users

### PostgreSQL (Recommended for Production)

For better performance and multi-user scenarios.

```env
DATABASE_URL=postgresql://username:password@localhost:5432/dvdtracker
```

**Setup Steps:**
1. **Install PostgreSQL**
2. **Create Database:**
   ```sql
   CREATE DATABASE dvdtracker;
   CREATE USER dvduser WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE dvdtracker TO dvduser;
   ```
3. **Install Python Driver:**
   ```powershell
   pip install psycopg2-binary
   ```

### MySQL/MariaDB

Alternative relational database option.

```env
DATABASE_URL=mysql://username:password@localhost:3306/dvdtracker
```

**Setup:**
```powershell
pip install mysqlclient
```

## 🎯 TMDB API Configuration

### API Key Management

The application supports multiple methods for API key configuration:

#### Method 1: Environment Variable (Recommended)
```env
TMDB_API_KEY=your_api_key_here
```

#### Method 2: Admin Interface
1. Navigate to Admin Settings in the application
2. Enter your API key in the form
3. Save settings

#### Method 3: Database Settings Model
```python
from tracker.models import AppSettings
settings = AppSettings.get_settings()
settings.tmdb_api_key = 'your_api_key'
settings.save()
```

### API Configuration Options

```env
# Base URL for TMDB API
TMDB_BASE_URL=https://api.themoviedb.org/3

# Image base URL
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/

# Request timeout (seconds)
TMDB_TIMEOUT=30

# Rate limiting
TMDB_REQUESTS_PER_SECOND=10
```

### Image Quality Settings

Configure poster download quality:

```python
# In settings.py or via environment
TMDB_POSTER_SIZE = 'w500'  # Options: w92, w154, w185, w342, w500, w780, original
TMDB_BACKDROP_SIZE = 'w1280'  # For backdrop images
```

## 📁 Media and Static Files

### Media Files Configuration

Media files store user uploads like movie posters.

```env
# Local storage
MEDIA_ROOT=media
MEDIA_URL=/media/

# Alternative path
MEDIA_ROOT=/path/to/media/storage
```

**Directory Structure:**
```
media/
├── posters/
│   ├── abc123_original.jpg
│   ├── def456_w500.jpg
│   └── ...
└── (other uploads)
```

### Static Files Configuration

Static files include CSS, JavaScript, and images.

```env
# Development
STATIC_URL=/static/
STATIC_ROOT=staticfiles

# Production with CDN
STATIC_URL=https://cdn.yourdomain.com/static/
```

**Collection:**
```powershell
python manage.py collectstatic --noinput
```

### Cloud Storage (Advanced)

For production deployments, consider cloud storage:

#### AWS S3
```python
# settings.py
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.StaticS3Boto3Storage'

AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
AWS_S3_REGION_NAME = 'us-east-1'
```

## 🔐 Security Configuration

### Production Security Settings

```env
# Force HTTPS
SECURE_SSL_REDIRECT=True

# Security headers
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# HTTPS settings
SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Cookie security
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
```

### CORS Configuration (if needed)

For API access from different domains:

```python
# Install django-cors-headers
pip install django-cors-headers

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'corsheaders',
    # ... other apps
]

# Add middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    # ... other middleware
]

# Configure CORS
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## 📧 Email Configuration

### Development (Console Backend)

Emails printed to console for testing:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production (SMTP)

Real email sending configuration:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=DVD Tracker <noreply@yourdomain.com>
```

### Email Providers

#### Gmail
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

#### Outlook/Hotmail
```env
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
```

#### SendGrid
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

## 📊 Logging Configuration

### Basic Logging

```env
LOG_LEVEL=INFO
LOG_FILE=logs/dvdtracker.log
```

### Advanced Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/dvdtracker.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'tracker': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## 🚀 Performance Configuration

### Cache Configuration

#### Redis Cache (Recommended)
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

#### Database Cache
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
```

### Session Configuration

```python
# Database sessions (default)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Cache sessions (faster)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# File sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = '/tmp/django_sessions'
```

### Database Optimization

```python
# Connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'MAX_CONNS': 20,
            'CONN_MAX_AGE': 0,
        },
    }
}

# Query optimization
DEBUG_TOOLBAR = True  # Development only
INTERNAL_IPS = ['127.0.0.1']
```

## 🌐 Internationalization

### Language Settings

```python
# Default language
LANGUAGE_CODE = 'en-us'

# Available languages
LANGUAGES = [
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('de', 'German'),
]

# Enable internationalization
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Time zone
TIME_ZONE = 'UTC'  # or your local timezone
```

### Locale Configuration

```env
# Locale settings
LOCALE_PATHS=[
    os.path.join(BASE_DIR, 'locale'),
]
```

## 🔄 Backup Configuration

### Automated Backups

```python
# Custom management command for backups
# management/commands/backup_data.py

from django.core.management.base import BaseCommand
from django.core.management import call_command
import os
from datetime import datetime

class Command(BaseCommand):
    def handle(self, *args, **options):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_{timestamp}.json'
        
        with open(backup_file, 'w') as f:
            call_command('dumpdata', stdout=f)
```

### Scheduled Backups

#### Windows Task Scheduler
Create a batch file:
```batch
@echo off
cd /d "C:\Projects\dvdcollection"
call venv\Scripts\activate.bat
python manage.py backup_data
```

#### Linux Cron
```bash
# Add to crontab
0 2 * * * cd /path/to/dvdcollection && ./venv/bin/python manage.py backup_data
```

## 🔧 Development vs Production

### Development Configuration

```env
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Production Configuration

```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dvdtracker
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
SECURE_SSL_REDIRECT=True
```

### Configuration Management

Use different settings files:

```python
# settings/base.py - Common settings
# settings/development.py - Dev overrides
# settings/production.py - Prod overrides

# Activate with:
export DJANGO_SETTINGS_MODULE=dvd_tracker.settings.production
```

---

*Complete configuration guide for DVD Collection Tracker. For deployment specifics, see the [Deployment Guide](deployment.md).*