from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Min, Max, Avg, Sum
from .models import DVD
from .forms import DVDForm, DVDSearchForm, DVDFilterForm, BulkUploadForm
from .services import TMDBService, YTSService
import json
import logging
from collections import Counter

logger = logging.getLogger(__name__)


def home(request):
    """Home/landing page with overview of collection."""
    # Get basic stats for the dashboard
    total_dvds = DVD.objects.count()
    kept_dvds = DVD.objects.filter(status='kept').count()
    disposed_dvds = DVD.objects.filter(status='disposed').count()
    
    # Recent additions
    recent_additions = DVD.objects.order_by('-created_at')[:6]
    
    # Quick stats
    tartan_dvds = DVD.objects.filter(is_tartan_dvd=True).count()
    box_sets_count = DVD.objects.filter(is_box_set=True).values('box_set_name').distinct().count()
    unwatched_count = DVD.objects.filter(is_unwatched=True).count()
    
    context = {
        'total_dvds': total_dvds,
        'kept_dvds': kept_dvds,
        'disposed_dvds': disposed_dvds,
        'recent_additions': recent_additions,
        'tartan_dvds': tartan_dvds,
        'box_sets_count': box_sets_count,
        'unwatched_count': unwatched_count,
        'page_title': 'DVD Collection Tracker',
        'page_icon': 'house',
    }
    return render(request, 'tracker/home.html', context)


def box_set_autocomplete(request):
    """API endpoint for box set name autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) >= 2:  # Only search if query is at least 2 characters
        # Get unique box set names that contain the query (case-insensitive)
        box_sets = DVD.objects.filter(
            box_set_name__icontains=query,
            box_set_name__isnull=False
        ).exclude(
            box_set_name__exact=''
        ).values_list('box_set_name', flat=True).distinct().order_by('box_set_name')[:10]
        
        return JsonResponse({'suggestions': list(box_sets)})
    
    return JsonResponse({'suggestions': []})


def storage_box_autocomplete(request):
    """API endpoint for storage box autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) >= 1:  # Only search if query is at least 1 character
        # Get unique storage box names that contain the query (case-insensitive)
        storage_boxes = DVD.objects.filter(
            storage_box__icontains=query,
            storage_box__isnull=False,
            status='kept'  # Only from kept items
        ).exclude(
            storage_box__exact=''
        ).values_list('storage_box', flat=True).distinct().order_by('storage_box')[:10]
        
        return JsonResponse({'suggestions': list(storage_boxes)})
    
    return JsonResponse({'suggestions': []})


def dvd_list(request):
    """Display list of DVDs with filtering."""
    filter_form = DVDFilterForm(request.GET)
    dvds = DVD.objects.all()
    
    # Apply filters
    if filter_form.is_valid():
        search = filter_form.cleaned_data.get('search')
        status = filter_form.cleaned_data.get('status')
        media_type = filter_form.cleaned_data.get('media_type')
        is_tartan_dvd = filter_form.cleaned_data.get('is_tartan_dvd')
        is_box_set = filter_form.cleaned_data.get('is_box_set')
        is_unopened = filter_form.cleaned_data.get('is_unopened')
        is_unwatched = filter_form.cleaned_data.get('is_unwatched')
        
        if search:
            dvds = dvds.filter(
                Q(name__icontains=search) | 
                Q(overview__icontains=search) |
                Q(genres__icontains=search) |
                Q(box_set_name__icontains=search)
            )
        
        if status:
            dvds = dvds.filter(status=status)
            
        if media_type:
            dvds = dvds.filter(media_type=media_type)
            
        if is_tartan_dvd:
            dvds = dvds.filter(is_tartan_dvd=(is_tartan_dvd == 'true'))
            
        if is_box_set:
            dvds = dvds.filter(is_box_set=(is_box_set == 'true'))
            
        if is_unopened:
            dvds = dvds.filter(is_unopened=(is_unopened == 'true'))
            
        if is_unwatched:
            dvds = dvds.filter(is_unwatched=(is_unwatched == 'true'))
    
    # Pagination
    paginator = Paginator(dvds, 12)  # 12 DVDs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': dvds.count(),
    }
    return render(request, 'tracker/dvd_list.html', context)


def dvd_detail(request, pk):
    """Display detailed view of a DVD."""
    dvd = get_object_or_404(DVD, pk=pk)
    
    # Get torrent information if IMDB ID is available
    torrents = []
    if dvd.imdb_id:
        yts_service = YTSService()
        torrents = yts_service.get_quality_torrents(dvd.imdb_id, ['720p', '1080p'])
    
    context = {
        'dvd': dvd,
        'torrents': torrents
    }
    return render(request, 'tracker/dvd_detail.html', context)


def dvd_add(request):
    """Add a new DVD - first step is to search TMDB."""
    search_form = DVDSearchForm()
    
    if request.method == 'POST':
        if 'search' in request.POST:
            search_form = DVDSearchForm(request.POST)
            if search_form.is_valid():
                query = search_form.cleaned_data['query']
                tmdb_service = TMDBService()
                search_results = tmdb_service.search_movies(query)
                
                # Pre-process poster URLs for template
                results = search_results.get('results', [])
                for movie in results:
                    if movie.get('poster_path'):
                        movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                    else:
                        movie['poster_url'] = None
                
                context = {
                    'search_form': search_form,
                    'search_results': results,
                    'query': query,
                    'tmdb_service': tmdb_service,
                }
                return render(request, 'tracker/dvd_search.html', context)
        else:
            # Manual form submission
            dvd_form = DVDForm(request.POST)
            if dvd_form.is_valid():
                dvd = dvd_form.save()
                messages.success(request, f'"{dvd.name}" has been added to your collection.')
                return redirect('tracker:dvd_detail', pk=dvd.pk)
    
    return render(request, 'tracker/dvd_add.html', {'search_form': search_form})


def dvd_add_from_tmdb(request, tmdb_id):
    """Add a DVD from TMDB movie data."""
    tmdb_service = TMDBService()
    movie_data = tmdb_service.get_movie_details(tmdb_id)
    
    if not movie_data:
        messages.error(request, 'Could not fetch movie details from TMDB.')
        return redirect('tracker:dvd_add')
    
    # Check if we already have this movie
    existing_dvd = DVD.objects.filter(tmdb_id=tmdb_id).first()
    if existing_dvd:
        messages.warning(request, f'"{existing_dvd.name}" is already in your collection.')
        return redirect('tracker:dvd_detail', pk=existing_dvd.pk)
    
    # Pre-process poster URL for template
    if movie_data.get('poster_path'):
        movie_data['poster_url'] = tmdb_service.get_full_poster_url(movie_data['poster_path'])
    else:
        movie_data['poster_url'] = None
    
    if request.method == 'POST':
        form = DVDForm(request.POST)
        if form.is_valid():
            dvd = form.save(commit=False)
            # Fill in TMDB data
            tmdb_data = tmdb_service.format_movie_data(movie_data)
            
            poster_path = tmdb_data.pop('poster_path', None)

            for key, value in tmdb_data.items():
                setattr(dvd, key, value)
            
            dvd.save()

            # Download poster
            if poster_path:
                full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                tmdb_service.download_poster(dvd, full_poster_url)
            
            messages.success(request, f'"{dvd.name}" has been added to your collection.')
            return redirect('tracker:dvd_detail', pk=dvd.pk)
    else:
        # Pre-populate form with TMDB data
        initial_data = tmdb_service.format_movie_data(movie_data)
        form = DVDForm(initial=initial_data)
    
    context = {
        'form': form,
        'movie_data': movie_data,
        'tmdb_service': tmdb_service,
    }
    return render(request, 'tracker/dvd_add_from_tmdb.html', context)


def dvd_edit(request, pk):
    """Edit an existing DVD."""
    dvd = get_object_or_404(DVD, pk=pk)
    
    if request.method == 'POST':
        form = DVDForm(request.POST, instance=dvd)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{dvd.name}" has been updated.')
            return redirect('tracker:dvd_detail', pk=dvd.pk)
    else:
        form = DVDForm(instance=dvd)
    
    return render(request, 'tracker/dvd_edit.html', {'form': form, 'dvd': dvd})


def dvd_delete(request, pk):
    """Delete a DVD."""
    dvd = get_object_or_404(DVD, pk=pk)
    
    if request.method == 'POST':
        dvd_name = dvd.name
        dvd.delete()
        messages.success(request, f'"{dvd_name}" has been removed from your collection.')
        return redirect('tracker:dvd_list')
    
    return render(request, 'tracker/dvd_delete.html', {'dvd': dvd})


@require_http_methods(["GET"])
def search_tmdb_ajax(request):
    """AJAX endpoint for searching TMDB."""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'results': []})
    
    tmdb_service = TMDBService()
    search_results = tmdb_service.search_movies(query)
    
    # Format results for JSON response
    results = []
    for movie in search_results.get('results', [])[:10]:  # Limit to 10 results
        poster_url = None
        if movie.get('poster_path'):
            poster_url = tmdb_service.get_full_poster_url(movie['poster_path'])
        
        results.append({
            'id': movie.get('id'),
            'title': movie.get('title'),
            'release_date': movie.get('release_date'),
            'poster_url': poster_url,
            'overview': movie.get('overview', '')[:200] + '...' if len(movie.get('overview', '')) > 200 else movie.get('overview', ''),
        })
    
    return JsonResponse({'results': results})


def bulk_upload(request):
    """Bulk upload movies from a list."""
    if request.method == 'POST':
        form = BulkUploadForm(request.POST)
        if form.is_valid():
            movie_list = form.cleaned_data['movie_list']
            default_status = form.cleaned_data['default_status']
            default_media_type = form.cleaned_data['default_media_type']
            skip_existing = form.cleaned_data['skip_existing']
            
            # Get all the new DVD-specific options
            default_is_tartan_dvd = form.cleaned_data['default_is_tartan_dvd']
            default_is_box_set = form.cleaned_data['default_is_box_set']
            default_box_set_name = form.cleaned_data['default_box_set_name']
            default_is_unopened = form.cleaned_data['default_is_unopened']
            default_is_unwatched = form.cleaned_data['default_is_unwatched']
            default_storage_box = form.cleaned_data['default_storage_box']
            
            # Split the movie list into individual titles
            movie_titles = [title.strip() for title in movie_list.split('\n') if title.strip()]
            
            tmdb_service = TMDBService()
            results = {
                'added': [],
                'skipped': [],
                'not_found': [],
                'errors': []
            }
            
            for title in movie_titles:
                try:
                    # Search for the movie in TMDB
                    search_results = tmdb_service.search_movies(title)
                    movies = search_results.get('results', [])
                    
                    if not movies:
                        results['not_found'].append(title)
                        continue
                    
                    # Take the first (most relevant) result
                    movie = movies[0]
                    tmdb_id = movie.get('id')
                    
                    # Check if movie already exists
                    if skip_existing and DVD.objects.filter(tmdb_id=tmdb_id).exists():
                        existing_dvd = DVD.objects.get(tmdb_id=tmdb_id)
                        results['skipped'].append(f"{title} (already have: {existing_dvd.name})")
                        continue
                    
                    # Get detailed movie data
                    movie_data = tmdb_service.get_movie_details(tmdb_id)
                    if not movie_data:
                        results['errors'].append(f"Could not get details for: {title}")
                        continue
                    
                    # Create DVD entry
                    tmdb_formatted_data = tmdb_service.format_movie_data(movie_data)
                    
                    poster_path = tmdb_formatted_data.pop('poster_path', None)

                    dvd = DVD.objects.create(
                        name=tmdb_formatted_data['name'],
                        overview=tmdb_formatted_data['overview'],
                        release_year=tmdb_formatted_data['release_year'],
                        runtime=tmdb_formatted_data['runtime'],
                        genres=tmdb_formatted_data['genres'],
                        tmdb_id=tmdb_formatted_data['tmdb_id'],
                        imdb_id=tmdb_formatted_data['imdb_id'],
                        rating=tmdb_formatted_data['rating'],
                        status=default_status,
                        media_type=default_media_type,
                        # Use the new default values from form
                        is_tartan_dvd=default_is_tartan_dvd,
                        is_box_set=default_is_box_set,
                        box_set_name=default_box_set_name if default_is_box_set else '',
                        is_unopened=default_is_unopened,
                        is_unwatched=default_is_unwatched,
                        storage_box=default_storage_box if default_status == 'kept' else ''
                    )

                    if poster_path:
                        full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                        tmdb_service.download_poster(dvd, full_poster_url)
                    
                    results['added'].append(dvd.name)
                    
                except Exception as e:
                    results['errors'].append(f"Error processing '{title}': {str(e)}")
            
            # Show results to user
            if results['added']:
                messages.success(request, f"Successfully added {len(results['added'])} movies to your collection.")
            
            if results['skipped']:
                messages.info(request, f"Skipped {len(results['skipped'])} movies already in your collection.")
            
            if results['not_found']:
                messages.warning(request, f"Could not find {len(results['not_found'])} movies on TMDB.")
            
            if results['errors']:
                messages.error(request, f"Encountered {len(results['errors'])} errors during upload.")
            
            # Render results page
            context = {
                'results': results,
                'total_processed': len(movie_titles)
            }
            return render(request, 'tracker/bulk_upload_results.html', context)
    else:
        form = BulkUploadForm()
    
    return render(request, 'tracker/bulk_upload.html', {'form': form})


def fix_tmdb_match(request, pk):
    """Fix an incorrect TMDB match for a DVD."""
    dvd = get_object_or_404(DVD, pk=pk)
    search_form = DVDSearchForm()
    
    if request.method == 'POST':
        if 'search' in request.POST:
            search_form = DVDSearchForm(request.POST)
            if search_form.is_valid():
                query = search_form.cleaned_data['query']
                tmdb_service = TMDBService()
                search_results = tmdb_service.search_movies(query)
                
                # Pre-process poster URLs for template
                results = search_results.get('results', [])
                for movie in results:
                    if movie.get('poster_path'):
                        movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                    else:
                        movie['poster_url'] = None
                
                context = {
                    'dvd': dvd,
                    'search_form': search_form,
                    'search_results': results,
                    'query': query,
                    'tmdb_service': tmdb_service,
                }
                return render(request, 'tracker/fix_tmdb_match.html', context)
        elif 'update_tmdb' in request.POST:
            # Update with new TMDB data
            tmdb_id = request.POST.get('tmdb_id')
            if tmdb_id:
                tmdb_service = TMDBService()
                movie_data = tmdb_service.get_movie_details(tmdb_id)
                
                if movie_data:
                    # Update DVD with new TMDB data
                    tmdb_formatted_data = tmdb_service.format_movie_data(movie_data)
                    
                    poster_path = tmdb_formatted_data.pop('poster_path', None)

                    # Keep the original user settings (status, media_type)
                    dvd.name = tmdb_formatted_data['name']
                    dvd.overview = tmdb_formatted_data['overview']
                    dvd.release_year = tmdb_formatted_data['release_year']
                    dvd.runtime = tmdb_formatted_data['runtime']
                    dvd.genres = tmdb_formatted_data['genres']
                    dvd.tmdb_id = tmdb_formatted_data['tmdb_id']
                    dvd.imdb_id = tmdb_formatted_data['imdb_id']
                    dvd.rating = tmdb_formatted_data['rating']
                    dvd.save()

                    if poster_path:
                        full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                        tmdb_service.download_poster(dvd, full_poster_url)
                    
                    messages.success(request, f'Successfully updated "{dvd.name}" with correct TMDB data.')
                    return redirect('tracker:dvd_detail', pk=dvd.pk)
                else:
                    messages.error(request, 'Could not fetch movie details from TMDB.')
            else:
                messages.error(request, 'No movie selected.')
    
    return render(request, 'tracker/fix_tmdb_match.html', {'dvd': dvd, 'search_form': search_form})


def dvd_change_poster(request, pk):
    """View to manage and change a DVD's poster."""
    dvd = get_object_or_404(DVD, pk=pk)
    tmdb_service = TMDBService()

    if request.method == 'POST':
        poster_path = request.POST.get('poster_path')
        if poster_path:
            # Delete the old poster file if it exists
            if dvd.poster:
                dvd.poster.delete(save=False)

            # Download the new poster
            full_poster_url = tmdb_service.get_full_poster_url(poster_path)
            tmdb_service.download_poster(dvd, full_poster_url)
            
            messages.success(request, 'Poster has been updated successfully.')
            return redirect('tracker:dvd_detail', pk=dvd.pk)
        else:
            messages.error(request, 'No poster was selected.')

    # GET request: Display available posters
    posters = tmdb_service.get_movie_posters(dvd.tmdb_id)
    
    context = {
        'dvd': dvd,
        'posters': posters
    }
    return render(request, 'tracker/dvd_change_poster.html', context)


@require_http_methods(["POST"])
def fetch_imdb_id(request, pk):
    """AJAX endpoint to fetch IMDB ID for a movie."""
    dvd = get_object_or_404(DVD, pk=pk)
    
    if not dvd.tmdb_id:
        return JsonResponse({
            'success': False,
            'error': 'No TMDB ID available for this movie'
        })
    
    tmdb_service = TMDBService()
    external_ids = tmdb_service.get_movie_external_ids(dvd.tmdb_id)
    
    if external_ids and external_ids.get('imdb_id'):
        imdb_id = external_ids['imdb_id']
        dvd.imdb_id = imdb_id
        dvd.save(update_fields=['imdb_id'])
        
        return JsonResponse({
            'success': True,
            'imdb_id': imdb_id,
            'message': f'IMDB ID updated to {imdb_id}'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'No IMDB ID found for this movie on TMDB'
        })


def tartan_dvds(request):
    """Display all Tartan DVDs."""
    dvds = DVD.objects.filter(is_tartan_dvd=True)
    
    # Apply search if provided
    search = request.GET.get('search', '')
    if search:
        dvds = dvds.filter(
            Q(name__icontains=search) | 
            Q(overview__icontains=search) |
            Q(genres__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(dvds, 12)  # 12 DVDs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_count': dvds.count(),
        'search': search,
        'page_title': 'Tartan DVD Collection',
        'page_icon': 'collection-play',
        'empty_message': 'No Tartan DVDs found in your collection.',
        'add_url': 'tracker:dvd_add',
    }
    return render(request, 'tracker/tartan_dvds.html', context)


def box_sets(request):
    """Display all box sets."""
    # Get unique box set names and count of movies in each
    box_sets_data = (
        DVD.objects.filter(is_box_set=True, box_set_name__isnull=False)
        .exclude(box_set_name='')
        .values('box_set_name')
        .annotate(
            movie_count=Count('id'),
            first_poster=Min('poster'),
            latest_added=Max('created_at')
        )
        .order_by('box_set_name')
    )
    
    # Apply search if provided
    search = request.GET.get('search', '')
    if search:
        box_sets_data = box_sets_data.filter(box_set_name__icontains=search)
    
    # For each box set, get up to 4 poster URLs
    for box_set in box_sets_data:
        box_set['posters'] = list(
            DVD.objects.filter(
                is_box_set=True, 
                box_set_name=box_set['box_set_name'],
                poster__isnull=False
            ).exclude(
                poster=''
            ).values_list('poster', flat=True)[:4]
        )
    
    # Pagination
    paginator = Paginator(box_sets_data, 12)  # 12 box sets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_count': box_sets_data.count(),
        'search': search,
        'page_title': 'Box Set Collection',
        'page_icon': 'boxes',
        'empty_message': 'No box sets found in your collection.',
    }
    return render(request, 'tracker/box_sets.html', context)


def box_set_detail(request, box_set_name):
    """Display all DVDs in a specific box set."""
    # URL decode the box set name
    from urllib.parse import unquote
    box_set_name = unquote(box_set_name)
    
    dvds = DVD.objects.filter(is_box_set=True, box_set_name=box_set_name)
    
    if not dvds.exists():
        messages.error(request, f'Box set "{box_set_name}" not found.')
        return redirect('tracker:box_sets')
    
    # Apply search if provided
    search = request.GET.get('search', '')
    if search:
        dvds = dvds.filter(
            Q(name__icontains=search) | 
            Q(overview__icontains=search) |
            Q(genres__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(dvds, 12)  # 12 DVDs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'box_set_name': box_set_name,
        'total_count': dvds.count(),
        'search': search,
        'page_title': f'{box_set_name} - Box Set',
        'page_icon': 'box',
        'empty_message': f'No movies found in "{box_set_name}" box set.',
    }
    return render(request, 'tracker/box_set_detail.html', context)


def stats(request):
    """Display collection statistics."""
    # Basic counts
    total_dvds = DVD.objects.count()
    kept_dvds = DVD.objects.filter(status='kept').count()
    disposed_dvds = DVD.objects.filter(status='disposed').count()
    
    # Media type breakdown
    physical_dvds = DVD.objects.filter(media_type='physical').count()
    digital_dvds = DVD.objects.filter(media_type='digital').count()
    
    # Special collections
    tartan_dvds = DVD.objects.filter(is_tartan_dvd=True).count()
    box_sets_count = DVD.objects.filter(is_box_set=True).values('box_set_name').distinct().count()
    box_set_movies = DVD.objects.filter(is_box_set=True).count()
    unopened_dvds = DVD.objects.filter(is_unopened=True).count()
    
    # Rating statistics
    rating_stats = DVD.objects.filter(rating__isnull=False).aggregate(
        avg_rating=Avg('rating'),
        max_rating=Max('rating'),
        min_rating=Min('rating'),
        rated_count=Count('rating')
    )
    
    # Runtime statistics
    runtime_stats = DVD.objects.filter(runtime__isnull=False).aggregate(
        avg_runtime=Avg('runtime'),
        max_runtime=Max('runtime'),
        min_runtime=Min('runtime'),
        total_runtime=Sum('runtime'),
        runtime_count=Count('runtime')
    )
    
    # Year statistics
    year_stats = DVD.objects.filter(release_year__isnull=False).aggregate(
        earliest_year=Min('release_year'),
        latest_year=Max('release_year'),
        year_count=Count('release_year')
    )
    
    # Calculate year span
    if year_stats['earliest_year'] and year_stats['latest_year']:
        year_stats['year_span'] = year_stats['latest_year'] - year_stats['earliest_year']
    else:
        year_stats['year_span'] = 0
    
    # Top genres
    all_genres = []
    for dvd in DVD.objects.filter(genres__isnull=False).exclude(genres=''):
        if dvd.genres:
            genres_list = [genre.strip() for genre in dvd.genres.split(',')]
            all_genres.extend(genres_list)
    
    genre_counts = Counter(all_genres)
    top_genres = genre_counts.most_common(10)
    
    # Top box sets (by movie count)
    top_box_sets = DVD.objects.filter(is_box_set=True).values('box_set_name').annotate(
        movie_count=Count('id')
    ).order_by('-movie_count')[:10]
    
    # Recent additions (last 10)
    recent_additions = DVD.objects.order_by('-id')[:10]
    
    # Decade breakdown
    decade_stats = {}
    for dvd in DVD.objects.filter(release_year__isnull=False):
        decade = (dvd.release_year // 10) * 10
        decade_key = f"{decade}s"
        decade_stats[decade_key] = decade_stats.get(decade_key, 0) + 1
    
    # Sort decades
    sorted_decades = sorted(decade_stats.items(), key=lambda x: x[0])
    max_decade_count = max(decade_stats.values()) if decade_stats else 1
    
    context = {
        'total_dvds': total_dvds,
        'kept_dvds': kept_dvds,
        'disposed_dvds': disposed_dvds,
        'physical_dvds': physical_dvds,
        'digital_dvds': digital_dvds,
        'tartan_dvds': tartan_dvds,
        'box_sets_count': box_sets_count,
        'box_set_movies': box_set_movies,
        'unopened_dvds': unopened_dvds,
        'rating_stats': rating_stats,
        'runtime_stats': runtime_stats,
        'year_stats': year_stats,
        'top_genres': top_genres,
        'top_box_sets': top_box_sets,
        'recent_additions': recent_additions,
        'decade_stats': sorted_decades,
        'max_decade_count': max_decade_count,
        'page_title': 'Collection Statistics',
        'page_icon': 'graph-up',
    }
    return render(request, 'tracker/stats.html', context)


def bulk_edit(request):
    """Bulk edit view for DVDs with table interface."""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    media_type_filter = request.GET.get('media_type', '')
    search_query = request.GET.get('search', '')
    
    # Start with all DVDs
    dvds = DVD.objects.all()
    
    # Apply filters
    if status_filter:
        dvds = dvds.filter(status=status_filter)
    if media_type_filter:
        dvds = dvds.filter(media_type=media_type_filter)
    if search_query:
        dvds = dvds.filter(
            Q(name__icontains=search_query) |
            Q(box_set_name__icontains=search_query) |
            Q(storage_box__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(dvds, 25)  # Show 25 DVDs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': DVD.STATUS_CHOICES,
        'media_type_choices': DVD.MEDIA_TYPE_CHOICES,
        'current_status': status_filter,
        'current_media_type': media_type_filter,
        'current_search': search_query,
        'page_title': 'Bulk Edit DVDs',
        'page_icon': 'pencil-square',
    }
    return render(request, 'tracker/bulk_edit.html', context)


@require_http_methods(["POST"])
def bulk_update_dvd(request):
    """API endpoint for updating individual DVD fields via AJAX."""
    try:
        data = json.loads(request.body)
        dvd_id = data.get('dvd_id')
        field = data.get('field')
        value = data.get('value')
        
        if not dvd_id or not field:
            return JsonResponse({
                'success': False,
                'error': 'DVD ID and field are required'
            })
        
        dvd = get_object_or_404(DVD, pk=dvd_id)
        
        # Validate and update the field
        if field == 'status':
            if value not in ['kept', 'disposed']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid status value'
                })
            dvd.status = value
        elif field == 'media_type':
            if value not in ['physical', 'download', 'rip']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid media type value'
                })
            dvd.media_type = value
        elif field == 'is_box_set':
            dvd.is_box_set = value == 'true'
        elif field == 'box_set_name':
            dvd.box_set_name = value
        elif field == 'storage_box':
            dvd.storage_box = value
        elif field == 'is_tartan_dvd':
            dvd.is_tartan_dvd = value == 'true'
        else:
            return JsonResponse({
                'success': False,
                'error': f'Field "{field}" is not editable'
            })
        
        dvd.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {field} successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Error in bulk_update_dvd: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while updating the DVD'
        })


@require_http_methods(["POST"])
def delete_dvd_api(request):
    """API endpoint for deleting DVDs via AJAX."""
    try:
        data = json.loads(request.body)
        dvd_id = data.get('dvd_id')
        
        if not dvd_id:
            return JsonResponse({
                'success': False,
                'error': 'DVD ID is required'
            })
        
        dvd = get_object_or_404(DVD, pk=dvd_id)
        dvd_name = dvd.name
        dvd.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'"{dvd_name}" has been deleted successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error(f"Error in delete_dvd_api: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while deleting the DVD'
        })


@require_http_methods(["POST"])
def refresh_all_tmdb(request):
    """Start a background task to refresh TMDB data for all DVDs."""
    import uuid
    from django.core.cache import cache
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    # Initialize progress tracking
    cache.set(f'tmdb_refresh_{task_id}', {
        'progress': 0,
        'status': 'Starting refresh...',
        'completed': False,
        'results': {'updated': 0, 'failed': 0, 'skipped': 0}
    }, 3600)  # Cache for 1 hour
    
    # Start the refresh process in the background
    from django.utils import timezone
    import threading
    
    def refresh_task():
        try:
            tmdb_service = TMDBService()
            # Only get DVDs with valid TMDB IDs (greater than 0)
            # This skips manually added DVDs that don't have TMDB data
            dvds_with_tmdb = DVD.objects.filter(tmdb_id__gt=0)
            total_dvds = dvds_with_tmdb.count()
            
            if total_dvds == 0:
                cache.set(f'tmdb_refresh_{task_id}', {
                    'progress': 100,
                    'status': 'No DVDs with TMDB IDs found to refresh',
                    'completed': True,
                    'results': {'updated': 0, 'failed': 0, 'skipped': 0}
                }, 3600)
                return
            
            updated_count = 0
            failed_count = 0
            
            for i, dvd in enumerate(dvds_with_tmdb, 1):
                try:
                    # Update progress
                    progress = (i / total_dvds) * 100
                    cache.set(f'tmdb_refresh_{task_id}', {
                        'progress': progress,
                        'status': f'Updating {dvd.name}... ({i}/{total_dvds})',
                        'completed': False,
                        'results': {'updated': updated_count, 'failed': failed_count, 'skipped': 0}
                    }, 3600)
                    
                    # Fetch fresh data from TMDB
                    logger.info(f"Fetching TMDB data for DVD {dvd.id} with TMDB ID: {dvd.tmdb_id}")
                    movie_data = tmdb_service.get_movie_details(dvd.tmdb_id)
                    if movie_data:
                        logger.info(f"Got TMDB data for DVD {dvd.id}, formatting...")
                        formatted_data = tmdb_service.format_movie_data_for_refresh(movie_data)
                        logger.info(f"Formatted data for DVD {dvd.id}: {list(formatted_data.keys())}")
                        
                        # Update DVD with fresh data
                        poster_path = formatted_data.pop('poster_path', None)
                        for field, value in formatted_data.items():
                            if hasattr(dvd, field):
                                logger.info(f"Setting DVD {dvd.id}.{field} = {repr(value)}")
                                setattr(dvd, field, value)
                        
                        logger.info(f"Saving DVD {dvd.id}...")
                        dvd.updated_at = timezone.now()
                        dvd.save()

                        # Download poster
                        if poster_path:
                            full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                            tmdb_service.download_poster(dvd, full_poster_url)

                        logger.info(f"Successfully saved DVD {dvd.id}")
                        updated_count += 1
                    else:
                        logger.warning(f"No data returned from TMDB for DVD {dvd.id} (TMDB ID: {dvd.tmdb_id})")
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"Error refreshing DVD {dvd.id} ('{dvd.name}', TMDB ID: {getattr(dvd, 'tmdb_id', 'None')}): {str(e)}")
                    failed_count += 1
            
            # Mark as completed
            cache.set(f'tmdb_refresh_{task_id}', {
                'progress': 100,
                'status': f'Refresh completed! Updated {updated_count}, Failed {failed_count}',
                'completed': True,
                'results': {'updated': updated_count, 'failed': failed_count, 'skipped': 0}
            }, 3600)
            
        except Exception as e:
            logger.error(f"Error in TMDB refresh task: {str(e)}")
            cache.set(f'tmdb_refresh_{task_id}', {
                'progress': 0,
                'status': f'Error: {str(e)}',
                'completed': True,
                'results': {'updated': 0, 'failed': 0, 'skipped': 0}
            }, 3600)
    
    # Start the background thread
    thread = threading.Thread(target=refresh_task)
    thread.daemon = True
    thread.start()
    
    return JsonResponse({
        'success': True,
        'task_id': task_id
    })


def refresh_progress(request):
    """Check the progress of a TMDB refresh task."""
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({
            'success': False,
            'error': 'Task ID required'
        })
    
    from django.core.cache import cache
    progress_data = cache.get(f'tmdb_refresh_{task_id}')
    
    if progress_data is None:
        return JsonResponse({
            'success': False,
            'error': 'Task not found'
        })
    
    return JsonResponse(progress_data)
