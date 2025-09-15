#!/usr/bin/env python
"""
Test script to verify bulk upload now includes detailed movie information.
This will test the changes made to fix the issue where bulk uploaded DVDs
were missing fields like tagline, revenue, production companies, etc.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from tracker.models import DVD
from tracker.services import TMDBService

def test_format_movie_data_includes_all_fields():
    """Test that format_movie_data returns all expected fields"""
    print("Testing TMDBService.format_movie_data()...")
    
    # Mock detailed movie data similar to what TMDB API returns
    mock_movie_data = {
        'id': 12345,
        'title': 'Test Movie',
        'overview': 'A comprehensive test movie with all data fields',
        'release_date': '2023-01-01',
        'runtime': 120,
        'genres': [{'name': 'Action'}, {'name': 'Adventure'}],
        'vote_average': 7.5,
        'imdb_id': 'tt1234567',
        'poster_path': '/test_poster.jpg',
        'budget': 50000000,
        'revenue': 150000000,
        'tagline': 'The ultimate test movie',
        'original_language': 'en',
        'production_companies': [
            {'name': 'Test Studios'}, 
            {'name': 'Example Productions'}
        ],
        'uk_certification': '12A',
        'director': 'Test Director'
    }
    
    tmdb_service = TMDBService()
    formatted_data = tmdb_service.format_movie_data(mock_movie_data)
    
    print("Formatted data fields:")
    for key, value in formatted_data.items():
        print(f"  {key}: {value}")
    
    # Check that all important fields are present
    expected_fields = [
        'tmdb_id', 'imdb_id', 'name', 'overview', 'release_year',
        'genres', 'runtime', 'rating', 'uk_certification', 'tmdb_user_score',
        'original_language', 'budget', 'revenue', 'production_companies',
        'tagline', 'director'
    ]
    
    missing_fields = []
    for field in expected_fields:
        if field not in formatted_data:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
        return False
    else:
        print("✅ All expected fields are present in formatted data")
        
    # Verify specific values
    assert formatted_data['tagline'] == 'The ultimate test movie'
    assert formatted_data['budget'] == 50000000
    assert formatted_data['revenue'] == 150000000
    assert formatted_data['production_companies'] == 'Test Studios, Example Productions'
    assert formatted_data['uk_certification'] == '12A'
    assert formatted_data['director'] == 'Test Director'
    
    print("✅ All field values are correct")
    return True

def test_dvd_model_has_all_fields():
    """Test that DVD model has all the fields we expect to populate"""
    print("\nTesting DVD model fields...")
    
    dvd_fields = [field.name for field in DVD._meta.get_fields()]
    expected_fields = [
        'tagline', 'budget', 'revenue', 'production_companies', 
        'uk_certification', 'director', 'tmdb_user_score', 'original_language'
    ]
    
    missing_fields = []
    for field in expected_fields:
        if field not in dvd_fields:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ DVD model missing fields: {missing_fields}")
        return False
    else:
        print("✅ DVD model has all expected fields")
        return True

if __name__ == '__main__':
    print("Testing bulk upload fix...")
    print("=" * 50)
    
    success = True
    success &= test_format_movie_data_includes_all_fields()
    success &= test_dvd_model_has_all_fields()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The bulk upload fix should work correctly.")
        print("\nNow when you bulk upload DVDs, they should include:")
        print("  - Tagline")
        print("  - Budget and Revenue (profit calculation)")
        print("  - Production Companies")
        print("  - UK Certification")
        print("  - Director")
        print("  - TMDB User Score")
        print("  - Original Language")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)