#!/usr/bin/env python
"""
Simple script to test the YTS API integration
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
django.setup()

from tracker.services import YTSService

def test_yts_api():
    """Test the YTS API with a known movie IMDB ID."""
    yts_service = YTSService()
    
    # Test with The Matrix (1999) - IMDB ID: tt0133093
    test_imdb_id = "tt0133093"
    
    print(f"Testing YTS API with IMDB ID: {test_imdb_id}")
    print("-" * 50)
    
    # Get all torrents
    all_torrents = yts_service.get_movie_torrents(test_imdb_id)
    print(f"Found {len(all_torrents)} torrents total")
    
    if all_torrents:
        print("\nAll available torrents:")
        for i, torrent in enumerate(all_torrents):
            print(f"{i+1}. Quality: {torrent.get('quality')}, Size: {torrent.get('size')}, Seeds: {torrent.get('seeds')}")
    
    # Get filtered torrents (720p and 1080p)
    filtered_torrents = yts_service.get_quality_torrents(test_imdb_id, ['720p', '1080p'])
    print(f"\nFound {len(filtered_torrents)} torrents for 720p/1080p")
    
    if filtered_torrents:
        print("\nFiltered torrents (720p/1080p):")
        for i, torrent in enumerate(filtered_torrents):
            print(f"{i+1}. Quality: {torrent.get('quality')}")
            print(f"   Size: {torrent.get('size')}")
            print(f"   Seeds: {torrent.get('seeds')}")
            print(f"   Peers: {torrent.get('peers')}")
            print(f"   URL: {torrent.get('url')}")
            print()
    else:
        print("No 720p/1080p torrents found for this movie")

if __name__ == "__main__":
    test_yts_api()
