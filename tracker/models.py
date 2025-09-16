from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class AppSettings(models.Model):
    """Model to store application settings."""
    tmdb_api_key = models.CharField(
        max_length=255, 
        blank=True, 
        help_text="TMDB API Key for fetching movie data"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Application Settings"
        verbose_name_plural = "Application Settings"
    
    def __str__(self):
        return "Application Settings"
    
    @classmethod
    def get_settings(cls):
        """Get or create the settings instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class DVD(models.Model):
    is_downloaded = models.BooleanField(default=False, help_text='Has this DVD been downloaded?')
    STATUS_CHOICES = [
        ('kept', 'Kept'),
        ('disposed', 'Disposed'),
        ('unboxed', 'Unboxed'),
    ]
    
    MEDIA_TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('download', 'Download'),
        ('rip', 'Rip'),
    ]

    DISK_TYPE_CHOICES = [
    ('DVD', 'DVD'),
    ('BluRay', 'BluRay'),
    ]

    # Basic info
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='kept')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='physical')
    disk_type = models.CharField(max_length=10, choices=DISK_TYPE_CHOICES, default='DVD')
    
    # DVD specific info
    is_tartan_dvd = models.BooleanField(default=False, help_text='Is this a Tartan DVD release?')
    is_box_set = models.BooleanField(default=False, help_text='Is this part of a box set?')
    box_set_name = models.CharField(max_length=255, blank=True, help_text='Name of the box set (if applicable)')
    is_unopened = models.BooleanField(default=False, help_text='Is this DVD still unopened?')
    is_unwatched = models.BooleanField(default=False, help_text='Have you not watched this movie yet?')
    storage_box = models.CharField(max_length=100, blank=True, help_text='Storage box location (for kept items)')
    location = models.CharField(max_length=255, blank=True, help_text='Location (for unboxed items)')
    
    # Duplicate tracking
    copy_number = models.PositiveSmallIntegerField(default=1, help_text='Copy number (1, 2, 3, etc.) for duplicate movies')
    duplicate_notes = models.CharField(max_length=255, blank=True, help_text='Notes about this copy (e.g., "Director\'s Cut", "Region 2", "Special Edition")')
    
    # TMDB data
    tmdb_id = models.IntegerField(null=True, blank=True)
    imdb_id = models.CharField(max_length=20, blank=True, help_text="IMDB ID (e.g., tt1234567)")
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    overview = models.TextField(blank=True)
    release_year = models.IntegerField(null=True, blank=True)
    genres = models.CharField(max_length=255, blank=True)
    runtime = models.IntegerField(null=True, blank=True)  # in minutes
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    uk_certification = models.CharField(max_length=10, blank=True, help_text="UK film certification (e.g., U, PG, 12, 15, 18)")
    tmdb_user_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="TMDB user score out of 10")
    original_language = models.CharField(max_length=10, blank=True, help_text="Original language of the movie")
    budget = models.BigIntegerField(null=True, blank=True, help_text="Movie budget in USD")
    revenue = models.BigIntegerField(null=True, blank=True, help_text="Movie revenue in USD")
    production_companies = models.TextField(blank=True, help_text="Production companies, comma-separated")
    tagline = models.CharField(max_length=255, blank=True)
    director = models.CharField(max_length=255, blank=True, help_text="Director of the movie")
    
    # YTS Torrent data - stored to avoid repeated API calls
    yts_data = models.JSONField(blank=True, null=True, help_text="Cached YTS torrent data")
    yts_last_updated = models.DateTimeField(blank=True, null=True, help_text="When YTS data was last refreshed")
    has_cached_torrents = models.BooleanField(
        default=False, 
        help_text="Whether this DVD has torrents available (cached result for fast filtering)"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to ensure uk_certification is always lowercase."""
        if self.uk_certification:
            self.uk_certification = self.uk_certification.lower()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Custom validation for the DVD model."""
        super().clean()
        
        # Validate location field for unboxed DVDs
        if self.status == 'unboxed':
            if self.location:
                # Check if location is already taken by another DVD
                if self.is_location_taken(self.location, exclude_pk=self.pk):
                    raise ValidationError({
                        'location': f'Location {self.location} is already taken by another unboxed DVD.'
                    })
                
                # Check if location is a valid number
                try:
                    int(self.location)
                except ValueError:
                    raise ValidationError({
                        'location': 'Location must be a number for unboxed DVDs.'
                    })
    
    def get_absolute_url(self):
        return reverse('tracker:dvd_detail', kwargs={'pk': self.pk})
    
    @property
    def profit(self):
        """Calculate profit as revenue minus budget."""
        if self.revenue is not None and self.budget is not None:
            return self.revenue - self.budget
        return None
    
    def get_genres_list(self):
        """Return genres as a list."""
        if self.genres:
            return [g.strip() for g in self.genres.split(',')]
        return []
    
    def get_production_companies_list(self):
        """Return production companies as a list."""
        if self.production_companies:
            return [pc.strip() for pc in self.production_companies.split(',')]
        return []
    
    def get_status_display_class(self):
        """Return CSS class for status display."""
        classes = {
            'kept': 'success',
            'disposed': 'danger',
            'unboxed': 'warning'
        }
        return classes.get(self.status, 'secondary')
    
    def get_media_type_display_class(self):
        """Return CSS class for media type display."""
        classes = {
            'physical': 'primary',
            'download': 'info',
            'rip': 'warning'
        }
        return classes.get(self.media_type, 'secondary')
    
    def has_torrents(self):
        """Check if this DVD has available torrent links (optimized for filtering)."""
        if not self.imdb_id:
            return False
        
        # For filtering operations, only check cached data - never make API calls
        # This prevents performance issues and crashes during bulk filtering
        return bool(self.yts_data and len(self.yts_data) > 0)
    
    def get_cached_torrents(self):
        """Get cached YTS torrent data."""
        if self.yts_data and isinstance(self.yts_data, list):
            return self.yts_data
        return []
    
    def is_yts_data_fresh(self, max_age_hours=24):
        """Check if YTS data is fresh (within max_age_hours)."""
        if not self.yts_last_updated:
            return False
        
        age = timezone.now() - self.yts_last_updated
        return age < timedelta(hours=max_age_hours)
    
    def refresh_yts_data(self):
        """Refresh YTS torrent data from the API and update cached availability flag."""
        if not self.imdb_id:
            self.has_cached_torrents = False
            self.save(update_fields=['has_cached_torrents'])
            return False
        
        from .services import YTSService
        
        yts_service = YTSService()
        torrents = yts_service.get_quality_torrents(self.imdb_id, ['720p', '1080p'])
        
        # Store the data and update the cached availability flag
        self.yts_data = torrents
        self.yts_last_updated = timezone.now()
        self.has_cached_torrents = bool(torrents and len(torrents) > 0)
        self.save(update_fields=['yts_data', 'yts_last_updated', 'has_cached_torrents'])
        
        return True
    
    def update_torrent_availability(self):
        """Update the cached torrent availability flag without making API calls."""
        if not self.imdb_id:
            self.has_cached_torrents = False
        else:
            # Only update based on existing cached data
            # Don't make API calls here - this is for background updates
            if self.is_yts_data_fresh():
                self.has_cached_torrents = bool(self.yts_data and len(self.yts_data) > 0)
            # If data is stale, keep existing value until background job updates it
        
        self.save(update_fields=['has_cached_torrents'])
        
    def get_special_features_badges(self):
        """Return a list of special feature badges."""
        badges = []
        if self.is_tartan_dvd:
            badges.append({'text': 'Tartan', 'class': 'bg-purple text-white'})
        if self.is_box_set:
            badges.append({'text': 'Box Set', 'class': 'bg-info'})
        if self.is_unopened:
            badges.append({'text': 'Unopened', 'class': 'bg-success'})
        if self.is_unwatched:
            badges.append({'text': 'Unwatched', 'class': 'bg-warning'})
        if self.copy_number > 1:
            badges.append({'text': f'Copy #{self.copy_number}', 'class': 'bg-secondary'})
        if self.has_torrents():
            badges.append({'text': 'Torrent', 'class': 'text-white', 'style': 'background-color: #16a34a;'})
        return badges
    
    def get_duplicate_copies(self):
        """Return all copies of this movie (including this one)."""
        if not self.tmdb_id:
            # If no TMDB ID, try to match by name and release year
            return DVD.objects.filter(
                name__iexact=self.name,
                release_year=self.release_year
            ).order_by('copy_number')
        else:
            # Match by TMDB ID (more reliable)
            return DVD.objects.filter(tmdb_id=self.tmdb_id).order_by('copy_number')
    
    def get_other_copies(self):
        """Return other copies of this movie (excluding this one)."""
        return self.get_duplicate_copies().exclude(pk=self.pk)
    
    def has_duplicates(self):
        """Return True if there are other copies of this movie."""
        return self.get_other_copies().exists()
    
    def get_next_copy_number(self):
        """Get the next available copy number for this movie."""
        existing_copies = self.get_duplicate_copies()
        if not existing_copies.exists():
            return 1
        return existing_copies.aggregate(max_copy=models.Max('copy_number'))['max_copy'] + 1
    
    def get_copy_display(self):
        """Return a display string for this copy."""
        if self.copy_number == 1 and not self.has_duplicates():
            return ""  # Don't show copy number if it's the only copy
        
        copy_text = f"Copy #{self.copy_number}"
        if self.duplicate_notes:
            copy_text += f" ({self.duplicate_notes})"
        return copy_text
    
    @classmethod
    def get_next_location_number(cls):
        """Get the next available location number for unboxed DVDs."""
        from django.db import connection
        
        # Use raw SQL to properly cast location to integer and get the max
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT MAX(CAST(location AS INTEGER)) 
                FROM tracker_dvd 
                WHERE status = 'unboxed' 
                AND location IS NOT NULL 
                AND location != '' 
                AND location GLOB '[0-9]*'
            """)
            result = cursor.fetchone()
            max_location = result[0] if result[0] is not None else 0
        
        return max_location + 1
    
    @classmethod
    def is_location_taken(cls, location_number, exclude_pk=None):
        """Check if a location number is already taken by another unboxed DVD."""
        queryset = cls.objects.filter(
            status='unboxed',
            location=str(location_number)
        )
        if exclude_pk:
            queryset = queryset.exclude(pk=exclude_pk)
        return queryset.exists()
    
    @classmethod
    def get_next_sequential_locations(cls, count):
        """Get the next sequential location numbers for bulk operations."""
        start_number = cls.get_next_location_number()
        return [str(start_number + i) for i in range(count)]
