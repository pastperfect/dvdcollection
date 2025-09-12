import requests
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
import logging
import os
import hashlib

logger = logging.getLogger(__name__)


class YTSService:
    """Service for interacting with the YTS API to get torrent information."""
    
    def __init__(self):
        self.base_url = "https://yts.mx/api/v2"
        
    def get_movie_torrents(self, imdb_id):
        """Get torrent information for a movie by IMDB ID."""
        if not imdb_id:
            logger.warning("IMDB ID not provided")
            return []
            
        # Cache key for torrent data
        cache_key = f"yts_torrents_{imdb_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/list_movies.json"
        params = {
            'query_term': imdb_id,
            'limit': 1,
            'sort_by': 'rating',
            'order_by': 'desc'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('data', {}).get('movies'):
                movies = data['data']['movies']
                if movies and len(movies) > 0:
                    torrents = movies[0].get('torrents', [])
                    # Cache for 6 hours
                    cache.set(cache_key, torrents, 21600)
                    return torrents
            
            # Cache empty result for 1 hour to avoid repeated failed requests
            cache.set(cache_key, [], 3600)
            return []
            
        except requests.RequestException as e:
            logger.error(f"YTS API error: {e}")
            return []
    
    def filter_torrents_by_quality(self, torrents, qualities=['720p', '1080p']):
        """Filter torrents by desired quality."""
        if not torrents:
            return []
        
        return [
            torrent for torrent in torrents 
            if torrent.get('quality') in qualities
        ]
    
    def get_quality_torrents(self, imdb_id, qualities=['720p', '1080p']):
        """Get filtered torrents for specific qualities."""
        all_torrents = self.get_movie_torrents(imdb_id)
        return self.filter_torrents_by_quality(all_torrents, qualities)


class TMDBService:
    """Service for interacting with The Movie Database API."""
    
    def __init__(self):
        # Get API key from database settings
        try:
            from .models import AppSettings
            app_settings = AppSettings.get_settings()
            self.api_key = app_settings.tmdb_api_key
        except Exception as e:
            logger.warning(f"Could not load TMDB API key from database: {e}")
            # Fallback to settings.py if database is not available
            self.api_key = getattr(settings, 'TMDB_API_KEY', '')
            
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL
        
    def search_movies(self, query, page=1):
        """Search for movies by title."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return {'results': [], 'total_results': 0}
            
        # Create a safe cache key by hashing the query
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        cache_key = f"tmdb_search_{query_hash}_{page}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/search/movie"
        params = {
            'api_key': self.api_key,
            'query': query,
            'page': page,
            'language': 'en-US'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 1 hour
            cache.set(cache_key, data, 3600)
            return data
            
        except requests.RequestException as e:
            logger.error(f"TMDB API error: {e}")
            return {'results': [], 'total_results': 0}
    
    def get_movie_details(self, movie_id):
        """Get detailed information about a specific movie including IMDB ID."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
            
        cache_key = f"tmdb_movie_{movie_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            'api_key': self.api_key,
            'language': 'en-US'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Also fetch external IDs (including IMDB ID)
            external_ids = self.get_movie_external_ids(movie_id)
            if external_ids and external_ids.get('imdb_id'):
                data['imdb_id'] = external_ids['imdb_id']
            
            # Also fetch UK certification
            uk_certification = self.get_uk_certification(movie_id)
            if uk_certification:
                data['uk_certification'] = uk_certification
            
            # Also fetch director information
            director = self.get_movie_director(movie_id)
            if director:
                data['director'] = director
            
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            return data
            
        except requests.RequestException as e:
            logger.error(f"TMDB API error: {e}")
            return None
    
    def get_movie_external_ids(self, movie_id):
        """Get external IDs for a movie (IMDB, etc.)."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
            
        cache_key = f"tmdb_external_ids_{movie_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/movie/{movie_id}/external_ids"
        params = {
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            return data
            
        except requests.RequestException as e:
            logger.error(f"TMDB external IDs API error: {e}")
            return None
    
    def get_movie_certifications(self, movie_id):
        """Get certification/rating information for a movie."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
            
        cache_key = f"tmdb_certifications_{movie_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/movie/{movie_id}/release_dates"
        params = {
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            return data
            
        except requests.RequestException as e:
            logger.error(f"TMDB certifications API error: {e}")
            return None
    
    def get_uk_certification(self, movie_id):
        """Get UK certification for a movie."""
        certifications_data = self.get_movie_certifications(movie_id)
        if not certifications_data:
            return None
            
        # Look for UK certification
        results = certifications_data.get('results', [])
        for country_data in results:
            if country_data.get('iso_3166_1') == 'GB':  # GB is the ISO code for UK
                release_dates = country_data.get('release_dates', [])
                for release in release_dates:
                    certification = release.get('certification')
                    if certification and certification.strip():
                        return certification.strip()
        
        return None
    
    def get_movie_director(self, movie_id):
        """Get the director of a movie from the credits."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None
            
        cache_key = f"tmdb_director_{movie_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
            
        url = f"{self.base_url}/movie/{movie_id}/credits"
        params = {
            'api_key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Look for the director in the crew
            crew = data.get('crew', [])
            directors = []
            for person in crew:
                if person.get('job') == 'Director':
                    directors.append(person.get('name'))
            
            # Join multiple directors with commas
            director_string = ', '.join(directors) if directors else None
            
            # Cache for 24 hours
            cache.set(cache_key, director_string, 86400)
            return director_string
            
        except requests.RequestException as e:
            logger.error(f"TMDB director API error: {e}")
            return None
    
    def get_movie_images(self, movie_id):
        """Get all images for a movie from TMDB."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None

        cache_key = f"tmdb_images_{movie_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        url = f"{self.base_url}/movie/{movie_id}/images"
        params = {
            'api_key': self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours
            cache.set(cache_key, data, 86400)
            return data

        except requests.RequestException as e:
            logger.error(f"TMDB images API error: {e}")
            return None

    def get_movie_posters(self, movie_id):
        """Get a sorted list of posters for a movie."""
        images_data = self.get_movie_images(movie_id)
        if not images_data or 'posters' not in images_data:
            return []

        posters = images_data['posters']
        
        # Sort posters: English first, then no language, then others.
        # Within each group, sort by vote average descending.
        def sort_key(poster):
            lang = poster.get('iso_639_1')
            vote_avg = poster.get('vote_average', 0)
            
            if lang == 'en':
                lang_priority = 0
            elif lang is None:
                lang_priority = 1
            else:
                lang_priority = 2
                
            return (lang_priority, -vote_avg)

        sorted_posters = sorted(posters, key=sort_key)
        
        # Add full URL to each poster
        for poster in sorted_posters:
            poster['full_url'] = self.get_full_poster_url(poster.get('file_path'))
            
        return sorted_posters
    
    def get_full_poster_url(self, poster_path):
        """Get the full URL for a poster image."""
        if not poster_path:
            return None
        return f"{self.image_base_url}{poster_path}"

    def download_poster(self, dvd, poster_url):
        """Download a poster image and save it to the DVD."""
        if not poster_url:
            return

        try:
            response = requests.get(poster_url, stream=True, timeout=10)
            response.raise_for_status()

            # Get the filename from the URL
            filename = os.path.basename(poster_url)
            
            # Save the image to the poster field
            dvd.poster.save(filename, ContentFile(response.content), save=True)

        except requests.RequestException as e:
            logger.error(f"Error downloading poster for DVD {dvd.id}: {e}")
    
    def format_movie_data(self, movie_data):
        """Format TMDB movie data for our DVD model."""
        if not movie_data:
            return {}
            
        genres = ', '.join([genre['name'] for genre in movie_data.get('genres', [])])
        production_companies = ', '.join([pc['name'] for pc in movie_data.get('production_companies', [])])
        
        return {
            'tmdb_id': movie_data.get('id'),
            'imdb_id': movie_data.get('imdb_id', ''),
            'name': movie_data.get('title', ''),
            'overview': movie_data.get('overview', ''),
            'poster_path': movie_data.get('poster_path'),
            'release_year': self._extract_year(movie_data.get('release_date')),
            'genres': genres,
            'runtime': movie_data.get('runtime'),
            'rating': movie_data.get('vote_average'),
            'uk_certification': movie_data.get('uk_certification', ''),
            'tmdb_user_score': movie_data.get('vote_average'),
            'original_language': movie_data.get('original_language', ''),
            'budget': movie_data.get('budget'),
            'revenue': movie_data.get('revenue'),
            'production_companies': production_companies,
            'tagline': movie_data.get('tagline', ''),
            'director': movie_data.get('director', ''),
        }
    
    def format_movie_data_for_refresh(self, movie_data):
        """Format TMDB movie data for refreshing existing DVDs (excludes tmdb_id)."""
        if not movie_data:
            return {}
            
        genres = ', '.join([genre['name'] for genre in movie_data.get('genres', [])])
        
        formatted_data = {}
        
        # Only include fields that have values and are safe to update
        if movie_data.get('imdb_id'):
            formatted_data['imdb_id'] = movie_data.get('imdb_id')
        
        if movie_data.get('title'):
            formatted_data['name'] = movie_data.get('title')
            
        if movie_data.get('overview'):
            formatted_data['overview'] = movie_data.get('overview')
            
        if movie_data.get('poster_path'):
            formatted_data['poster_path'] = movie_data.get('poster_path')
            
        release_year = self._extract_year(movie_data.get('release_date'))
        if release_year:
            formatted_data['release_year'] = release_year
            
        if genres:
            formatted_data['genres'] = genres
            
        if movie_data.get('runtime'):
            formatted_data['runtime'] = movie_data.get('runtime')
            
        if movie_data.get('vote_average'):
            formatted_data['rating'] = movie_data.get('vote_average')
            
        if movie_data.get('uk_certification'):
            formatted_data['uk_certification'] = movie_data.get('uk_certification')
            
        if movie_data.get('vote_average'):
            formatted_data['tmdb_user_score'] = movie_data.get('vote_average')
            
        if movie_data.get('original_language'):
            formatted_data['original_language'] = movie_data.get('original_language')
            
        if movie_data.get('budget') is not None:
            formatted_data['budget'] = movie_data.get('budget')
            
        if movie_data.get('revenue') is not None:
            formatted_data['revenue'] = movie_data.get('revenue')
            
        production_companies = ', '.join([pc['name'] for pc in movie_data.get('production_companies', [])])
        if production_companies:
            formatted_data['production_companies'] = production_companies
            
        if movie_data.get('tagline'):
            formatted_data['tagline'] = movie_data.get('tagline')
            
        if movie_data.get('director'):
            formatted_data['director'] = movie_data.get('director')
        
        return formatted_data
    
    def _extract_year(self, date_string):
        """Extract year from TMDB date string (YYYY-MM-DD)."""
        if not date_string:
            return None
        try:
            return int(date_string.split('-')[0])
        except (ValueError, IndexError):
            return None
