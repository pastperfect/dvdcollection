import os
from django.core.management.base import BaseCommand
from django.conf import settings
from tracker.models import DVD


class Command(BaseCommand):
    help = 'Find and optionally remove unused poster files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting files',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Actually delete the unused files (use with caution)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_files = options['delete']
        
        if not dry_run and not delete_files:
            self.stdout.write(
                self.style.WARNING(
                    'Use --dry-run to see what would be deleted, or --delete to actually remove files'
                )
            )
            return

        # Get the poster directory path
        poster_dir = os.path.join(settings.MEDIA_ROOT, 'posters')
        
        if not os.path.exists(poster_dir):
            self.stdout.write(
                self.style.ERROR(f'Poster directory does not exist: {poster_dir}')
            )
            return

        # Get all poster files from the filesystem
        all_poster_files = set()
        for filename in os.listdir(poster_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                all_poster_files.add(filename)

        self.stdout.write(f'Found {len(all_poster_files)} poster files in filesystem')

        # Get all poster files referenced by DVDs in the database
        used_poster_files = set()
        dvds_with_posters = DVD.objects.exclude(poster='').exclude(poster__isnull=True)
        
        for dvd in dvds_with_posters:
            if dvd.poster and dvd.poster.name:
                # Extract just the filename from the path
                poster_filename = os.path.basename(dvd.poster.name)
                used_poster_files.add(poster_filename)

        self.stdout.write(f'Found {len(used_poster_files)} poster files referenced by DVDs')

        # Find unused files
        unused_files = all_poster_files - used_poster_files
        
        if not unused_files:
            self.stdout.write(
                self.style.SUCCESS('No unused poster files found!')
            )
            return

        self.stdout.write(f'Found {len(unused_files)} unused poster files:')
        
        total_size = 0
        for filename in sorted(unused_files):
            file_path = os.path.join(poster_dir, filename)
            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size
                size_mb = file_size / (1024 * 1024)
                self.stdout.write(f'  - {filename} ({size_mb:.2f} MB)')
            except OSError:
                self.stdout.write(f'  - {filename} (size unknown)')

        total_size_mb = total_size / (1024 * 1024)
        self.stdout.write(f'\nTotal size of unused files: {total_size_mb:.2f} MB')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDRY RUN: {len(unused_files)} files would be deleted, '
                    f'freeing {total_size_mb:.2f} MB of space'
                )
            )
        elif delete_files:
            deleted_count = 0
            for filename in unused_files:
                file_path = os.path.join(poster_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    self.stdout.write(f'Deleted: {filename}')
                except OSError as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to delete {filename}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nDeleted {deleted_count} unused poster files, '
                    f'freed approximately {total_size_mb:.2f} MB of space'
                )
            )