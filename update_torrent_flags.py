#!/usr/bin/env python
"""
Script to populate the has_cached_torrents field for existing DVDs
This should be run after implementing the database-only filtering solution
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dvd_tracker.settings')
django.setup()

from tracker.models import DVD

def update_torrent_flags():
    """Update torrent availability flags for all existing DVDs."""
    dvds = DVD.objects.all()
    updated = 0
    
    print(f"Processing {dvds.count()} DVDs...")
    
    for dvd in dvds:
        old_flag = dvd.has_cached_torrents
        # Set flag based on existing YTS data
        has_torrents = bool(dvd.yts_data and len(dvd.yts_data) > 0)
        
        if old_flag != has_torrents:
            dvd.has_cached_torrents = has_torrents
            dvd.save(update_fields=['has_cached_torrents'])
            updated += 1
            status = "✓" if has_torrents else "✗"
            print(f"{status} Updated {dvd.name}: {old_flag} -> {has_torrents}")
    
    print(f"\nUpdated {updated} DVDs with torrent availability flags")
    
    # Show summary
    with_torrents = DVD.objects.filter(has_cached_torrents=True).count()
    without_torrents = DVD.objects.filter(has_cached_torrents=False).count()
    with_imdb = DVD.objects.exclude(imdb_id='').exclude(imdb_id__isnull=True).count()
    
    print(f"\n📊 Summary:")
    print(f"  Total DVDs: {dvds.count()}")
    print(f"  DVDs with IMDB IDs: {with_imdb}")
    print(f"  DVDs with cached torrents: {with_torrents}")
    print(f"  DVDs without cached torrents: {without_torrents}")
    print(f"  Torrent coverage: {(with_torrents/dvds.count()*100):.1f}%")
    
    if with_imdb > with_torrents:
        missing = with_imdb - with_torrents
        print(f"\n⚠️  {missing} DVDs with IMDB IDs don't have torrent data cached.")
        print("   Consider running: python manage.py refresh_torrent_data")

if __name__ == '__main__':
    update_torrent_flags()