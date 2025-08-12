#!/usr/bin/env python
"""
Test script to verify TMDB external ID fetching works
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
django.setup()

from tracker.services import TMDBService

def test_imdb_fetching():
    """Test fetching IMDB IDs from TMDB."""
    tmdb_service = TMDBService()
    
    # Test movies with known TMDB IDs
    test_movies = [
        {'name': 'The Matrix', 'tmdb_id': 603},
        {'name': 'Inception', 'tmdb_id': 27205},
        {'name': 'The Dark Knight', 'tmdb_id': 155},
    ]
    
    print("Testing IMDB ID fetching from TMDB...")
    print("=" * 50)
    
    for movie in test_movies:
        print(f"\nTesting: {movie['name']} (TMDB ID: {movie['tmdb_id']})")
        
        # Get external IDs
        external_ids = tmdb_service.get_movie_external_ids(movie['tmdb_id'])
        
        if external_ids:
            imdb_id = external_ids.get('imdb_id')
            if imdb_id:
                print(f"  ✓ Found IMDB ID: {imdb_id}")
                print(f"  ✓ IMDB URL: https://www.imdb.com/title/{imdb_id}/")
            else:
                print(f"  ✗ No IMDB ID found")
        else:
            print(f"  ✗ Failed to fetch external IDs")

if __name__ == "__main__":
    test_imdb_fetching()
