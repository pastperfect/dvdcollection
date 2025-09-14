from django.core.management.base import BaseCommand
from django.db import models
from tracker.models import DVD
from django.utils import timezone
from datetime import timedelta
import time


class Command(BaseCommand):
    help = 'Refresh torrent data for DVDs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of DVDs to process in each batch (default: 50)'
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=168,  # 1 week
            help='Maximum age of torrent data before refresh (default: 168 hours / 1 week)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between API calls in seconds (default: 1.0)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh all DVDs regardless of age'
        )
        parser.add_argument(
            '--update-flags-only',
            action='store_true',
            help='Only update torrent availability flags without making API calls'
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        max_age_hours = options['max_age_hours']
        delay = options['delay']
        force = options['force']
        update_flags_only = options['update_flags_only']
        
        if update_flags_only:
            self.update_flags_only()
            return
        
        # Find DVDs that need torrent data updates
        dvds_query = DVD.objects.filter(
            models.Q(imdb_id__isnull=False) & ~models.Q(imdb_id='')
        )
        
        if not force:
            cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
            dvds_query = dvds_query.filter(
                models.Q(yts_last_updated__isnull=True) |
                models.Q(yts_last_updated__lt=cutoff_time)
            )
        
        dvds_to_update = dvds_query[:batch_size]
        total_count = dvds_to_update.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No DVDs need torrent data updates.")
            )
            return
        
        self.stdout.write(f"Updating torrent data for {total_count} DVDs...")
        
        if total_count > 100:
            self.stdout.write(
                self.style.WARNING(
                    f"Processing {total_count} DVDs will take approximately "
                    f"{(total_count * delay) / 60:.1f} minutes."
                )
            )
        
        success_count = 0
        error_count = 0
        
        for i, dvd in enumerate(dvds_to_update, 1):
            try:
                self.stdout.write(f"[{i}/{total_count}] Processing: {dvd.name}")
                
                success = dvd.refresh_yts_data()
                if success:
                    success_count += 1
                    torrent_count = len(dvd.yts_data) if dvd.yts_data else 0
                    self.stdout.write(f"  ✓ Success: Found {torrent_count} torrents")
                else:
                    error_count += 1
                    self.stdout.write(f"  ✗ Failed: No IMDB ID or API error")
                
                # Delay between requests to be respectful to the API
                if i < total_count:
                    time.sleep(delay)
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(f"  ✗ Error: {str(e)}")
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Completed: {success_count} successful, {error_count} errors"
            )
        )
        
        # Show final statistics
        with_torrents = DVD.objects.filter(has_cached_torrents=True).count()
        without_torrents = DVD.objects.filter(has_cached_torrents=False).count()
        total_dvds = DVD.objects.count()
        
        self.stdout.write(f"\n📊 Final Statistics:")
        self.stdout.write(f"  Total DVDs: {total_dvds}")
        self.stdout.write(f"  With torrents: {with_torrents}")
        self.stdout.write(f"  Without torrents: {without_torrents}")
        self.stdout.write(f"  Torrent coverage: {(with_torrents/total_dvds*100):.1f}%")
    
    def update_flags_only(self):
        """Update torrent availability flags without making API calls."""
        self.stdout.write("Updating torrent availability flags...")
        
        dvds = DVD.objects.all()
        updated_count = 0
        
        for dvd in dvds:
            old_flag = dvd.has_cached_torrents
            # Set flag based on existing YTS data
            has_torrents = bool(dvd.yts_data and len(dvd.yts_data) > 0)
            
            if old_flag != has_torrents:
                dvd.has_cached_torrents = has_torrents
                dvd.save(update_fields=['has_cached_torrents'])
                updated_count += 1
                status = "✓" if has_torrents else "✗"
                self.stdout.write(f"  {status} Updated {dvd.name}: {old_flag} → {has_torrents}")
        
        self.stdout.write(
            self.style.SUCCESS(f"Updated {updated_count} DVDs with torrent availability flags")
        )
        
        # Show summary
        with_torrents = DVD.objects.filter(has_cached_torrents=True).count()
        without_torrents = DVD.objects.filter(has_cached_torrents=False).count()
        
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"  DVDs with torrents: {with_torrents}")
        self.stdout.write(f"  DVDs without torrents: {without_torrents}")