from django.core.management.base import BaseCommand
from tracker.models import DVD
from tracker.services import TMDBService


class Command(BaseCommand):
    help = 'Add sample DVDs to the collection for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing DVDs before adding samples',
        )

    def handle(self, *args, **options):
        if options['clear']:
            DVD.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('Cleared all existing DVDs')
            )

        sample_movies = [
            {
                'name': 'The Matrix',
                'status': 'kept',
                'media_type': 'physical',
                'overview': 'A computer hacker learns about the true nature of reality.',
                'release_year': 1999,
                'genres': 'Action, Sci-Fi',
                'runtime': 136,
                'rating': 8.7,
            },
            {
                'name': 'Inception',
                'status': 'kept',
                'media_type': 'download',
                'overview': 'A thief who steals corporate secrets enters the subconscious.',
                'release_year': 2010,
                'genres': 'Action, Adventure, Sci-Fi',
                'runtime': 148,
                'rating': 8.8,
            },
            {
                'name': 'The Godfather',
                'status': 'disposed',
                'media_type': 'physical',
                'overview': 'The aging patriarch of an organized crime dynasty.',
                'release_year': 1972,
                'genres': 'Crime, Drama',
                'runtime': 175,
                'rating': 9.2,
            },
            {
                'name': 'Pulp Fiction',
                'status': 'kept',
                'media_type': 'rip',
                'overview': 'The lives of two mob hitmen, a boxer, and others intertwine.',
                'release_year': 1994,
                'genres': 'Crime, Drama',
                'runtime': 154,
                'rating': 8.9,
            },
            {
                'name': 'The Dark Knight',
                'status': 'kept',
                'media_type': 'physical',
                'overview': 'Batman faces the Joker in this dark superhero tale.',
                'release_year': 2008,
                'genres': 'Action, Crime, Drama',
                'runtime': 152,
                'rating': 9.0,
            }
        ]

        created_count = 0
        for movie_data in sample_movies:
            dvd, created = DVD.objects.get_or_create(
                name=movie_data['name'],
                defaults=movie_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Added: {dvd.name}')
            else:
                self.stdout.write(f'Already exists: {dvd.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully added {created_count} new DVDs to the collection'
            )
        )
