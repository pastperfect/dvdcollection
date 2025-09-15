#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from tracker.models import DVD

def test_torrent_badges():
    print("Testing torrent badge functionality...")
    
    # Find a DVD with IMDB ID
    dvd = DVD.objects.filter(imdb_id__isnull=False).exclude(imdb_id='').first()
    
    if not dvd:
        print("No DVDs with IMDB ID found for testing")
        return
    
    print(f"\nTesting with DVD: {dvd.name}")
    print(f"IMDB ID: {dvd.imdb_id}")
    print(f"Has YTS data: {bool(dvd.yts_data)}")
    print(f"YTS data count: {len(dvd.yts_data) if dvd.yts_data else 0}")
    print(f"Has cached torrents flag: {dvd.has_cached_torrents}")
    print(f"has_torrents() method result: {dvd.has_torrents()}")
    
    # Test the badges
    badges = dvd.get_special_features_badges()
    print(f"\nSpecial feature badges ({len(badges)} total):")
    for badge in badges:
        print(f"  - {badge['text']} (class: {badge.get('class', 'no-class')})")
    
    # Check if torrent badge is present
    torrent_badges = [b for b in badges if b['text'] == 'Torrent']
    if torrent_badges:
        print("\n✓ Torrent badge is present!")
    else:
        print("\n✗ Torrent badge is missing!")
    
    print("\nTest completed.")

if __name__ == '__main__':
    test_torrent_badges()