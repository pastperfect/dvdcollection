import requests
from django.conf import settings
from django.core.cache import cache
import logging

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
        self.api_key = settings.TMDB_API_KEY
        self.base_url = settings.TMDB_BASE_URL
        self.image_base_url = settings.TMDB_IMAGE_BASE_URL
        
    def search_movies(self, query, page=1):
        """Search for movies by title."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return {'results': [], 'total_results': 0}
            
        cache_key = f"tmdb_search_{query}_{page}"
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
    
    def get_full_poster_url(self, poster_path):
        """Get the full URL for a poster image."""
        if not poster_path:
            return None
        return f"{self.image_base_url}{poster_path}"
    
    def format_movie_data(self, movie_data):
        """Format TMDB movie data for our DVD model."""
        if not movie_data:
            return {}
            
        genres = ', '.join([genre['name'] for genre in movie_data.get('genres', [])])
        
        return {
            'tmdb_id': movie_data.get('id'),
            'imdb_id': movie_data.get('imdb_id', ''),
            'name': movie_data.get('title', ''),
            'overview': movie_data.get('overview', ''),
            'poster_url': self.get_full_poster_url(movie_data.get('poster_path')),
            'release_year': self._extract_year(movie_data.get('release_date')),
            'genres': genres,
            'runtime': movie_data.get('runtime'),
            'rating': movie_data.get('vote_average'),
        }
    
    def _extract_year(self, date_string):
        """Extract year from TMDB date string (YYYY-MM-DD)."""
        if not date_string:
            return None
        try:
            return int(date_string.split('-')[0])
        except (ValueError, IndexError):
            return None
