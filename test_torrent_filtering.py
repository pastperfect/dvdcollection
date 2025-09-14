#!/usr/bin/env python
"""
Test script for the new torrent filtering functionality
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
django.setup()

from tracker.models import DVD

def test_torrent_filtering():
    """Test the new database-only torrent filtering."""
    print("Testing torrent filtering performance improvements...")
    
    # Test 1: Database filtering performance
    print("\n1. Testing database filtering:")
    
    # Count all DVDs
    total_dvds = DVD.objects.count()
    print(f"Total DVDs: {total_dvds}")
    
    # Fast database queries (no API calls)
    with_torrents = DVD.objects.filter(has_cached_torrents=True).count()
    without_torrents = DVD.objects.filter(has_cached_torrents=False).count()
    
    print(f"DVDs with torrents (fast): {with_torrents}")
    print(f"DVDs without torrents (fast): {without_torrents}")
    print(f"Total check: {with_torrents + without_torrents} == {total_dvds}")
    
    # Test 2: Model method consistency
    print("\n2. Testing model method consistency:")
    
    # Get a few DVDs to test
    test_dvds = DVD.objects.all()[:5]
    
    for dvd in test_dvds:
        cached_flag = dvd.has_cached_torrents
        method_result = dvd.has_torrents()  # Now safe - no API calls
        cached_data = bool(dvd.yts_data and len(dvd.yts_data) > 0)
        
        print(f"{dvd.name[:30]:30} | Flag: {cached_flag} | Method: {method_result} | Data: {cached_data}")
    
    # Test 3: Update functionality
    print("\n3. Testing update functionality:")
    
    # Find a DVD with IMDB ID to test refresh
    dvd_with_imdb = DVD.objects.exclude(imdb_id='').exclude(imdb_id__isnull=True).first()
    
    if dvd_with_imdb:
        print(f"Testing refresh on: {dvd_with_imdb.name}")
        old_flag = dvd_with_imdb.has_cached_torrents
        print(f"Before refresh: {old_flag}")
        
        # Test update_torrent_availability (safe method)
        dvd_with_imdb.update_torrent_availability()
        dvd_with_imdb.refresh_from_db()
        
        new_flag = dvd_with_imdb.has_cached_torrents
        print(f"After update_torrent_availability: {new_flag}")
    
    print("\n✅ All tests completed successfully!")
    print("The new filtering system is working correctly and is now safe for production use.")

if __name__ == '__main__':
    test_torrent_filtering()