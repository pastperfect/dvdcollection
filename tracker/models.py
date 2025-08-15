from django.db import models
from django.urls import reverse


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
    STATUS_CHOICES = [
        ('kept', 'Kept'),
        ('disposed', 'Disposed'),
    ]
    
    MEDIA_TYPE_CHOICES = [
        ('physical', 'Physical'),
        ('download', 'Download'),
        ('rip', 'Rip'),
    ]

    # Basic info
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='kept')
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='physical')
    
    # DVD specific info
    is_tartan_dvd = models.BooleanField(default=False, help_text='Is this a Tartan DVD release?')
    is_box_set = models.BooleanField(default=False, help_text='Is this part of a box set?')
    box_set_name = models.CharField(max_length=255, blank=True, help_text='Name of the box set (if applicable)')
    is_unopened = models.BooleanField(default=False, help_text='Is this DVD still unopened?')
    is_unwatched = models.BooleanField(default=False, help_text='Have you not watched this movie yet?')
    storage_box = models.CharField(max_length=100, blank=True, help_text='Storage box location (for kept items)')
    
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
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('tracker:dvd_detail', kwargs={'pk': self.pk})
    
    def get_genres_list(self):
        """Return genres as a list."""
        if self.genres:
            return [g.strip() for g in self.genres.split(',')]
        return []
    
    def get_status_display_class(self):
        """Return CSS class for status display."""
        classes = {
            'kept': 'success',
            'disposed': 'danger'
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
        return badges
