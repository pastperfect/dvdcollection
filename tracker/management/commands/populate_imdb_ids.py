from django.core.management.base import BaseCommand
from django.db import transaction
from tracker.models import DVD
from tracker.services import TMDBService
import time


class Command(BaseCommand):
    help = 'Populate IMDB IDs for movies that have TMDB IDs but missing IMDB IDs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Limit the number of movies to process (default: 50)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        # Find movies with TMDB ID but no IMDB ID
        movies_to_update = DVD.objects.filter(
            tmdb_id__isnull=False,
            imdb_id__exact=''
        )[:limit]
        
        if not movies_to_update:
            self.stdout.write(
                self.style.SUCCESS('No movies found that need IMDB ID updates.')
            )
            return
        
        self.stdout.write(
            f'Found {movies_to_update.count()} movies to update (limit: {limit})'
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        tmdb_service = TMDBService()
        updated_count = 0
        failed_count = 0
        
        for movie in movies_to_update:
            try:
                self.stdout.write(f'Processing: {movie.name} (TMDB ID: {movie.tmdb_id})')
                
                # Get external IDs from TMDB
                external_ids = tmdb_service.get_movie_external_ids(movie.tmdb_id)
                
                if external_ids and external_ids.get('imdb_id'):
                    imdb_id = external_ids['imdb_id']
                    
                    if dry_run:
                        self.stdout.write(
                            f'  Would update IMDB ID to: {imdb_id}'
                        )
                    else:
                        movie.imdb_id = imdb_id
                        movie.save(update_fields=['imdb_id'])
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated IMDB ID to: {imdb_id}')
                        )
                    updated_count += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ✗ No IMDB ID found for {movie.name}')
                    )
                    failed_count += 1
                
                # Be nice to the API - small delay between requests
                time.sleep(0.25)  # 250ms delay
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Error processing {movie.name}: {str(e)}')
                )
                failed_count += 1
                continue
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN COMPLETE - Would update {updated_count} movies')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'COMPLETED - Updated {updated_count} movies')
            )
        
        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(f'Failed to update {failed_count} movies')
            )
        
        self.stdout.write(
            'Run with --dry-run to preview changes before applying them.'
        )
