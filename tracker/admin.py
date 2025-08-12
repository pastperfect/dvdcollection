from django.contrib import admin
from .models import DVD


@admin.register(DVD)
class DVDAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'media_type', 'release_year', 'rating', 'created_at']
    list_filter = ['status', 'media_type', 'release_year', 'created_at']
    search_fields = ['name', 'overview', 'genres']
    readonly_fields = ['tmdb_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'status', 'media_type')
        }),
        ('Movie Details', {
            'fields': ('overview', 'release_year', 'genres', 'runtime', 'rating')
        }),
        ('TMDB Data', {
            'fields': ('tmdb_id', 'poster_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
