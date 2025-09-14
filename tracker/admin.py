from django.contrib import admin
from django.contrib import messages
from django.db import models
from django.utils.html import format_html
from .models import DVD, AppSettings
import time


@admin.register(DVD)
class DVDAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'media_type', 'release_year', 'rating', 'has_cached_torrents', 'yts_last_updated', 'created_at']
    list_filter = ['status', 'media_type', 'release_year', 'has_cached_torrents', 'created_at']
    search_fields = ['name', 'overview', 'genres', 'imdb_id']
    readonly_fields = ['tmdb_id', 'yts_data', 'yts_last_updated', 'has_cached_torrents', 'created_at', 'updated_at']
    actions = ['refresh_torrent_data', 'refresh_selected_torrent_data', 'update_torrent_availability_flags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'status', 'media_type')
        }),
        ('Movie Details', {
            'fields': ('overview', 'release_year', 'genres', 'runtime', 'rating', 'imdb_id')
        }),
        ('TMDB Data', {
            'fields': ('tmdb_id', 'poster'),
            'classes': ('collapse',)
        }),
        ('YTS Torrent Data', {
            'fields': ('has_cached_torrents', 'yts_last_updated', 'yts_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def refresh_torrent_data(self, request, queryset=None):
        """Refresh torrent data for all DVDs with IMDB IDs."""
        if queryset is None:
            # Refresh all DVDs with IMDB IDs
            dvds_to_refresh = DVD.objects.filter(
                models.Q(imdb_id__isnull=False) & ~models.Q(imdb_id='')
            )
        else:
            # Refresh selected DVDs that have IMDB IDs
            dvds_to_refresh = queryset.filter(
                models.Q(imdb_id__isnull=False) & ~models.Q(imdb_id='')
            )
        
        total_count = dvds_to_refresh.count()
        
        if total_count == 0:
            messages.warning(request, "No DVDs with IMDB IDs found to refresh.")
            return
        
        # Confirm with user for large operations
        if total_count > 50:
            messages.warning(
                request, 
                f"This will refresh {total_count} DVDs and may take several minutes. "
                "Consider running this operation in smaller batches or during off-peak hours."
            )
        
        success_count = 0
        error_count = 0
        
        for i, dvd in enumerate(dvds_to_refresh):
            try:
                success = dvd.refresh_yts_data()
                if success:
                    success_count += 1
                else:
                    error_count += 1
                
                # Add a small delay to be respectful to the YTS API
                if i < total_count - 1:  # Don't delay after the last item
                    time.sleep(1)
                    
            except Exception as e:
                error_count += 1
                messages.error(request, f"Error refreshing {dvd.name}: {str(e)}")
        
        if success_count > 0:
            messages.success(
                request, 
                f"Successfully refreshed torrent data for {success_count} DVDs."
            )
        
        if error_count > 0:
            messages.warning(
                request, 
                f"Failed to refresh {error_count} DVDs. Check the logs for details."
            )
    
    refresh_torrent_data.short_description = "🔄 Refresh torrent data for all DVDs (with IMDB IDs)"
    
    def refresh_selected_torrent_data(self, request, queryset):
        """Refresh torrent data for selected DVDs only."""
        return self.refresh_torrent_data(request, queryset)
    
    refresh_selected_torrent_data.short_description = "🎯 Refresh torrent data for selected DVDs"
    
    def update_torrent_availability_flags(self, request, queryset=None):
        """Update the has_cached_torrents flag based on existing YTS data."""
        if queryset is None:
            dvds_to_update = DVD.objects.all()
        else:
            dvds_to_update = queryset
        
        updated_count = 0
        
        for dvd in dvds_to_update:
            old_flag = dvd.has_cached_torrents
            # Set flag based on existing YTS data without making API calls
            has_torrents = bool(dvd.yts_data and len(dvd.yts_data) > 0)
            
            if old_flag != has_torrents:
                dvd.has_cached_torrents = has_torrents
                dvd.save(update_fields=['has_cached_torrents'])
                updated_count += 1
        
        messages.success(
            request, 
            f"Updated torrent availability flags for {updated_count} DVDs based on existing cached data."
        )
    
    update_torrent_availability_flags.short_description = "⚡ Update torrent availability flags (no API calls)"


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ['tmdb_api_key_masked', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('API Configuration', {
            'fields': ('tmdb_api_key',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def tmdb_api_key_masked(self, obj):
        """Display masked API key for security."""
        if obj.tmdb_api_key:
            return f"{'*' * (len(obj.tmdb_api_key) - 4)}{obj.tmdb_api_key[-4:]}"
        return "Not set"
    
    tmdb_api_key_masked.short_description = "TMDB API Key"
    
    def has_add_permission(self, request):
        """Only allow one AppSettings instance."""
        return not AppSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of AppSettings."""
        return False
