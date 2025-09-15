from django.core.management.base import BaseCommand
from django.db import models
from tracker.models import DVD
from tracker.services import TMDBService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh TMDB data for DVDs missing detailed information like taglines, budget, revenue, production companies, director, and UK certification'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each DVD processed'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of DVDs to process (default: process all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh all DVDs with TMDB IDs, even if they have detailed data'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        limit = options['limit']
        force = options['force']
        
        # Initialize TMDB service
        tmdb_service = TMDBService()
        if not tmdb_service.api_key:
            self.stdout.write(
                self.style.ERROR("❌ TMDB API key not configured. Please set it in admin settings.")
            )
            return
        
        # Find DVDs that need refresh
        if force:
            # Force mode: refresh all DVDs with TMDB IDs
            dvds_to_refresh = DVD.objects.filter(tmdb_id__gt=0)
            mode_description = "all DVDs with TMDB IDs (force mode)"
        else:
            # Normal mode: only DVDs missing detailed information
            dvds_to_refresh = DVD.objects.filter(
                tmdb_id__gt=0  # Has TMDB ID
            ).filter(
                # Missing at least one of these detailed fields
                models.Q(tagline='') | models.Q(tagline__isnull=True) |
                models.Q(revenue__isnull=True) |
                models.Q(budget__isnull=True) |
                models.Q(production_companies='') | models.Q(production_companies__isnull=True) |
                models.Q(director='') | models.Q(director__isnull=True) |
                models.Q(uk_certification='') | models.Q(uk_certification__isnull=True)
            )
            mode_description = "DVDs missing detailed information"
        
        # Apply limit if specified
        if limit:
            dvds_to_refresh = dvds_to_refresh[:limit]
            mode_description += f" (limited to {limit})"
        
        total_count = dvds_to_refresh.count()
        total_with_tmdb = DVD.objects.filter(tmdb_id__gt=0).count()
        
        # Display summary
        self.stdout.write(f"Found {total_with_tmdb} DVDs with TMDB IDs in collection")
        self.stdout.write(f"Found {total_count} {mode_description}")
        
        if total_count == 0:
            if force:
                self.stdout.write(
                    self.style.SUCCESS("✅ No DVDs with TMDB IDs found!")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ All DVDs with TMDB IDs already have detailed information!")
                )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN MODE - No changes will be made")
            )
        
        self.stdout.write(f"\n📋 Processing {total_count} DVDs:")
        
        updated_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, dvd in enumerate(dvds_to_refresh, 1):
            try:
                # Always show progress for each DVD being processed
                self.stdout.write(
                    f"[{i}/{total_count}] Processing: {dvd.name} ({dvd.release_year or 'N/A'}) - TMDB ID: {dvd.tmdb_id}"
                )
                
                if not dry_run:
                    # Fetch fresh data from TMDB
                    movie_data = tmdb_service.get_movie_details(dvd.tmdb_id)
                    if movie_data:
                        formatted_data = tmdb_service.format_movie_data_for_refresh(movie_data)
                        
                        # Track which fields were updated
                        fields_updated = []
                        old_values = {}
                        new_values = {}
                        
                        for field, value in formatted_data.items():
                            if hasattr(dvd, field) and field != 'poster_path':
                                old_value = getattr(dvd, field)
                                
                                # Only update if there's a new value and it's different
                                if value and str(old_value) != str(value):
                                    old_values[field] = old_value
                                    new_values[field] = value
                                    setattr(dvd, field, value)
                                    fields_updated.append(field)
                        
                        if fields_updated:
                            dvd.save()
                            updated_count += 1
                            
                            self.stdout.write(f"  ✅ Updated fields: {', '.join(fields_updated)}")
                            if verbose:
                                for field in fields_updated:
                                    self.stdout.write(f"    {field}: '{old_values[field]}' → '{new_values[field]}'")
                        else:
                            skipped_count += 1
                            self.stdout.write(f"  ⏭️  No new data to update")
                    else:
                        failed_count += 1
                        self.stdout.write(f"  ❌ Failed to fetch TMDB data")
                else:
                    # Dry run mode - simulate the operation
                    movie_data = tmdb_service.get_movie_details(dvd.tmdb_id)
                    if movie_data:
                        formatted_data = tmdb_service.format_movie_data_for_refresh(movie_data)
                        
                        # Check what would be updated
                        fields_to_update = []
                        for field, value in formatted_data.items():
                            if hasattr(dvd, field) and field != 'poster_path':
                                old_value = getattr(dvd, field)
                                if value and str(old_value) != str(value):
                                    fields_to_update.append(field)
                        
                        if fields_to_update:
                            self.stdout.write(f"  📝 Would update fields: {', '.join(fields_to_update)}")
                            if verbose:
                                for field in fields_to_update:
                                    old_value = getattr(dvd, field)
                                    new_value = formatted_data[field]
                                    self.stdout.write(f"    {field}: '{old_value}' → '{new_value}'")
                            updated_count += 1
                        else:
                            skipped_count += 1
                            self.stdout.write(f"  ⏭️  No new data to update")
                    else:
                        failed_count += 1
                        self.stdout.write(f"  ❌ Failed to fetch TMDB data")
                        
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Error processing {dvd.name}: {str(e)}")
                )
                logger.error(f"Error refreshing DVD {dvd.id} in management command: {str(e)}")
        
        # Final summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n🔍 DRY RUN COMPLETE:"
                )
            )
            self.stdout.write(f"  Would update: {updated_count} DVDs")
            self.stdout.write(f"  Would skip (no changes): {skipped_count} DVDs")
            self.stdout.write(f"  Failed to fetch: {failed_count} DVDs")
            self.stdout.write("Run without --dry-run to apply these changes.")
        else:
            if failed_count == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ REFRESH COMPLETE:"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️  REFRESH COMPLETE WITH SOME ERRORS:"
                    )
                )
            
            self.stdout.write(f"  Updated: {updated_count} DVDs")
            self.stdout.write(f"  Skipped (no changes): {skipped_count} DVDs")
            self.stdout.write(f"  Failed: {failed_count} DVDs")
        
        # Show detailed field statistics
        self.show_detailed_stats()
    
    def show_detailed_stats(self):
        """Display current statistics for detailed fields."""
        self.stdout.write(f"\n📊 Current Detailed Information Statistics:")
        
        total_with_tmdb = DVD.objects.filter(tmdb_id__gt=0).count()
        
        if total_with_tmdb == 0:
            self.stdout.write("  No DVDs with TMDB IDs found")
            return
        
        # Check each detailed field
        fields_to_check = [
            ('tagline', 'Taglines'),
            ('revenue', 'Revenue'),
            ('budget', 'Budget'),
            ('production_companies', 'Production Companies'),
            ('director', 'Director'),
            ('uk_certification', 'UK Certification')
        ]
        
        for field, label in fields_to_check:
            if field in ['revenue', 'budget']:
                # Numeric fields - check for null
                with_data = DVD.objects.filter(
                    tmdb_id__gt=0,
                    **{f'{field}__isnull': False}
                ).count()
            else:
                # Text fields - check for non-empty
                with_data = DVD.objects.filter(
                    tmdb_id__gt=0
                ).exclude(
                    **{field: ''}
                ).exclude(
                    **{f'{field}__isnull': True}
                ).count()
            
            percentage = (with_data / total_with_tmdb * 100) if total_with_tmdb > 0 else 0
            self.stdout.write(f"  {label}: {with_data}/{total_with_tmdb} ({percentage:.1f}%)")