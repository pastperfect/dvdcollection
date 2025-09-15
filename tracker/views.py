from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Min, Max, Avg, Sum
from django.db import models
from django.utils import timezone
from datetime import date, timedelta
from .models import DVD, AppSettings
from .forms import DVDForm, DVDSearchForm, DVDFilterForm, BulkUploadForm, BulkMarkDownloadedForm
from .services import TMDBService, YTSService
import json
import csv
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
        production_company = filter_form.cleaned_data.get('production_company')
        is_downloaded = filter_form.cleaned_data.get('is_downloaded')
        has_torrents = filter_form.cleaned_data.get('has_torrents')
        
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
            
        if production_company:
            dvds = dvds.filter(production_companies__icontains=production_company)
            
        if is_downloaded:
            dvds = dvds.filter(is_downloaded=(is_downloaded == 'true'))
            
        if has_torrents:
            if has_torrents == 'true':
                # Fast database filter - no API calls needed
                dvds = dvds.filter(has_cached_torrents=True)
            elif has_torrents == 'false':
                # Filter for DVDs without cached torrents
                dvds = dvds.filter(has_cached_torrents=False)
    
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
    
    # Get torrent information - use cached data or refresh if needed
    torrents = []
    if dvd.imdb_id:
        # Check if we need to refresh YTS data
        if not dvd.is_yts_data_fresh():
            dvd.refresh_yts_data()
        
        torrents = dvd.get_cached_torrents()
    
    context = {
        'dvd': dvd,
        'torrents': torrents
    }
    return render(request, 'tracker/dvd_detail.html', context)


def dvd_add(request):
    """Add a new DVD - first step is to search TMDB."""
    search_form = DVDSearchForm()
    # Fetch the last used storage box for a kept DVD
    last_storage_box = (
        DVD.objects.filter(status='kept')
        .exclude(storage_box='')
        .order_by('-created_at')
        .values_list('storage_box', flat=True)
        .first()
    )
    # Get next location number for unboxed DVDs
    next_location_number = DVD.get_next_location_number()
    if request.method == 'POST':
        if 'search' in request.POST:
            search_form = DVDSearchForm(request.POST)
            if search_form.is_valid():
                query = search_form.cleaned_data['query'].strip()
                tmdb_service = TMDBService()
                # If the query is a TMDB ID (all digits, reasonable length), fetch directly
                if query.isdigit() and 1 <= len(query) <= 10:
                    movie_data = tmdb_service.get_movie_details(query)
                    results = []
                    if movie_data:
                        # Wrap in a list to match search results structure
                        if movie_data.get('poster_path'):
                            movie_data['poster_url'] = tmdb_service.get_full_poster_url(movie_data['poster_path'])
                        else:
                            movie_data['poster_url'] = None
                        # Ensure original_language is present
                        movie_data['original_language'] = movie_data.get('original_language', '')
                        # Director is already included in get_movie_details response
                        results = [movie_data]
                    context = {
                        'search_form': search_form,
                        'search_results': results,
                        'query': query,
                        'tmdb_service': tmdb_service,
                        'last_storage_box': last_storage_box,
                        'next_location_number': next_location_number,
                        'tmdb_id_search': True,
                    }
                    return render(request, 'tracker/dvd_search.html', context)
                else:
                    # Normal title search
                    search_results = tmdb_service.search_movies(query)
                    results = search_results.get('results', [])
                    
                    # Enhance results with director information
                    enhanced_results = []
                    for movie in results[:10]:  # Limit to 10 to avoid too many API calls
                        if movie.get('poster_path'):
                            movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                        else:
                            movie['poster_url'] = None
                        # Ensure original_language is present
                        movie['original_language'] = movie.get('original_language', '')
                        
                        # Fetch director information
                        director = tmdb_service.get_movie_director(movie.get('id'))
                        movie['director'] = director if director else ''
                        
                        enhanced_results.append(movie)
                    
                    context = {
                        'search_form': search_form,
                        'search_results': enhanced_results,
                        'query': query,
                        'tmdb_service': tmdb_service,
                        'last_storage_box': last_storage_box,
                        'next_location_number': next_location_number,
                        'tmdb_id_search': False,
                    }
                    return render(request, 'tracker/dvd_search.html', context)
        else:
            # Manual form submission
            dvd_form = DVDForm(request.POST, request.FILES)
            if dvd_form.is_valid():
                dvd = dvd_form.save(commit=False)
                dvd.is_downloaded = False
                dvd.save()
                # Refresh YTS data immediately to populate torrent badge
                if dvd.imdb_id:
                    dvd.refresh_yts_data()
                messages.success(request, f'"{ dvd.name}" has been added to your collection.')
                return redirect('tracker:dvd_add')
    return render(request, 'tracker/dvd_add.html', {
        'search_form': search_form, 
        'last_storage_box': last_storage_box,
        'next_location_number': next_location_number
    })


def dvd_add_from_tmdb(request, tmdb_id):
    """Add a DVD from TMDB movie data."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        tmdb_service = TMDBService()
        movie_data = tmdb_service.get_movie_details(tmdb_id)
        
        if not movie_data:
            logger.error(f"Could not fetch movie details from TMDB for ID {tmdb_id}")
            messages.error(request, 'Could not fetch movie details from TMDB.')
            return redirect('tracker:dvd_add')
        
        # Check if we already have this movie - but allow adding duplicates
        existing_dvd = DVD.objects.filter(tmdb_id=tmdb_id).first()
        # We'll handle this in the form initialization below instead of redirecting
    
    except Exception as e:
        logger.error(f"Error in dvd_add_from_tmdb for TMDB ID {tmdb_id}: {e}")
        messages.error(request, 'An error occurred while fetching movie details.')
        return redirect('tracker:dvd_add')

    # Pre-process poster URL for template
    if movie_data.get('poster_path'):
        movie_data['poster_url'] = tmdb_service.get_full_poster_url(movie_data['poster_path'])
    else:
        movie_data['poster_url'] = None
    
    # Fetch the last used storage box for a kept DVD
    last_storage_box = (
        DVD.objects.filter(status='kept')
        .exclude(storage_box='')
        .order_by('-created_at')
        .values_list('storage_box', flat=True)
        .first()
    )
    
    # Get next location number for unboxed DVDs
    next_location_number = DVD.get_next_location_number()
    
    try:
        if request.method == 'POST':
            form = DVDForm(request.POST, request.FILES)
            if form.is_valid():
                dvd = form.save(commit=False)
                # Fill in TMDB data (excluding tmdb_id since it's already set by the form)
                tmdb_data = tmdb_service.format_movie_data(movie_data)
                poster_path = tmdb_data.pop('poster_path', None)
                tmdb_id = tmdb_data.pop('tmdb_id', None)  # Remove tmdb_id to avoid overriding form value
                for key, value in tmdb_data.items():
                    setattr(dvd, key, value)
                dvd.is_downloaded = False
                dvd.save()
                # Download poster only if no custom poster was uploaded
                if poster_path and not dvd.poster:
                    full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                    tmdb_service.download_poster(dvd, full_poster_url)
                # Refresh YTS data immediately to populate torrent badge
                if dvd.imdb_id:
                    dvd.refresh_yts_data()
                messages.success(request, f'"{dvd.name}" has been added to your collection.')
                return redirect('tracker:dvd_add')
        else:
            # Pre-populate form with TMDB data and last storage box
            initial_data = tmdb_service.format_movie_data(movie_data)
            # Add default values for required fields
            initial_data.setdefault('status', 'kept')
            initial_data.setdefault('media_type', 'physical')
            if last_storage_box:
                initial_data['storage_box'] = last_storage_box
            
            # Check for existing copies and suggest next copy number
            existing_copies = DVD.objects.filter(tmdb_id=tmdb_id)
            if existing_copies.exists():
                next_copy_number = existing_copies.aggregate(
                    max_copy=Max('copy_number')
                )['max_copy'] + 1
                initial_data['copy_number'] = next_copy_number
                # Add a note about existing copies to the form
                existing_copy_info = existing_copies.first()
                messages.info(request, f'You already have {existing_copies.count()} copy(ies) of "{existing_copy_info.name}". This will be copy #{next_copy_number}.')
            
            form = DVDForm(initial=initial_data)
        
        context = {
            'form': form,
            'movie_data': movie_data,
            'tmdb_service': tmdb_service,
            'last_storage_box': last_storage_box,
            'next_location_number': next_location_number,
        }
        return render(request, 'tracker/dvd_add_from_tmdb.html', context)
    
    except Exception as e:
        logger.error(f"Error in dvd_add_from_tmdb form processing for TMDB ID {tmdb_id}: {e}")
        messages.error(request, 'An error occurred while processing the form.')
        return redirect('tracker:dvd_add')


def dvd_edit(request, pk):
    """Edit an existing DVD."""
    dvd = get_object_or_404(DVD, pk=pk)
    
    if request.method == 'POST':
        form = DVDForm(request.POST, request.FILES, instance=dvd)
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
def check_location_availability(request):
    """AJAX endpoint for checking location availability."""
    location = request.GET.get('location', '').strip()
    dvd_id = request.GET.get('dvd_id', '').strip()
    
    if not location:
        return JsonResponse({'available': True, 'message': ''})
    
    if not location.isdigit():
        return JsonResponse({'available': False, 'message': 'Location must be a number.'})
    
    exclude_pk = dvd_id if dvd_id else None
    is_taken = DVD.is_location_taken(location, exclude_pk=exclude_pk)
    
    if is_taken:
        return JsonResponse({'available': False, 'message': f'Location {location} is already taken.'})
    
    return JsonResponse({'available': True, 'message': 'Location is available.'})


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
        
        # Fetch director information
        director = tmdb_service.get_movie_director(movie.get('id'))
        
        results.append({
            'id': movie.get('id'),
            'title': movie.get('title'),
            'release_date': movie.get('release_date'),
            'poster_url': poster_url,
            'overview': movie.get('overview', '')[:200] + '...' if len(movie.get('overview', '')) > 200 else movie.get('overview', ''),
            'director': director if director else '',
            'original_language': movie.get('original_language', ''),
        })
    
    return JsonResponse({'results': results})


def bulk_upload(request):
    """Bulk upload movies from a list - first step: search and store in session."""
    if request.method == 'POST':
        form = BulkUploadForm(request.POST)
        if form.is_valid():
            movie_list = form.cleaned_data['movie_list']
            
            # Split the movie list into individual titles
            movie_titles = [title.strip() for title in movie_list.split('\n') if title.strip()]
            
            # Store form defaults in session
            form_defaults = {
                'default_status': form.cleaned_data['default_status'],
                'default_media_type': form.cleaned_data['default_media_type'],
                'skip_existing': form.cleaned_data['skip_existing'],
                'default_is_tartan_dvd': form.cleaned_data['default_is_tartan_dvd'],
                'default_is_box_set': form.cleaned_data['default_is_box_set'],
                'default_box_set_name': form.cleaned_data['default_box_set_name'],
                'default_is_unopened': form.cleaned_data['default_is_unopened'],
                'default_is_unwatched': form.cleaned_data['default_is_unwatched'],
                'default_storage_box': form.cleaned_data['default_storage_box'],
                'default_location': form.cleaned_data['default_location']
            }
            
            tmdb_service = TMDBService()
            matches = []
            
            for title in movie_titles:
                try:
                    # Search for the movie in TMDB
                    search_results = tmdb_service.search_movies(title)
                    movies = search_results.get('results', [])
                    
                    if not movies:
                        # No match found - store as error case
                        matches.append({
                            'original_title': title,
                            'tmdb_data': None,
                            'confirmed': False,
                            'removed': False,
                            'poster_url': None,
                            'error': 'No TMDB matches found'
                        })
                        continue
                    
                    # Take the first (most relevant) result
                    movie = movies[0]
                    tmdb_id = movie.get('id')
                    
                    # Get detailed movie data
                    movie_data = tmdb_service.get_movie_details(tmdb_id)
                    if not movie_data:
                        matches.append({
                            'original_title': title,
                            'tmdb_data': None,
                            'confirmed': False,
                            'removed': False,
                            'poster_url': None,
                            'error': 'Could not get movie details'
                        })
                        continue
                    
                    # Store match with poster URL
                    poster_url = None
                    if movie.get('poster_path'):
                        poster_url = tmdb_service.get_full_poster_url(movie['poster_path'])
                    
                    matches.append({
                        'original_title': title,
                        'tmdb_data': movie_data,
                        'confirmed': True,  # Default to confirmed
                        'removed': False,
                        'poster_url': poster_url,
                        'error': None
                    })
                    
                except Exception as e:
                    matches.append({
                        'original_title': title,
                        'tmdb_data': None,
                        'confirmed': False,
                        'removed': False,
                        'poster_url': None,
                        'error': f"Error: {str(e)}"
                    })
            
            # Store everything in session
            from datetime import datetime
            request.session['bulk_upload_data'] = {
                'form_defaults': form_defaults,
                'matches': matches,
                'timestamp': datetime.now().isoformat()
            }
            
            # Redirect to preview page
            return redirect('tracker:bulk_upload_preview')
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
                search_type = search_form.cleaned_data.get('search_type', 'title')
                tmdb_service = TMDBService()
                results = []
                query = ''
                if search_type == 'title':
                    query = search_form.cleaned_data['query']
                    search_results = tmdb_service.search_movies(query)
                    results = search_results.get('results', [])
                    for movie in results:
                        if movie.get('poster_path'):
                            movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                        else:
                            movie['poster_url'] = None
                elif search_type == 'tmdb_id':
                    tmdb_id = search_form.cleaned_data['tmdb_id']
                    movie = tmdb_service.get_movie_details(tmdb_id)
                    if movie:
                        if movie.get('poster_path'):
                            movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                        else:
                            movie['poster_url'] = None
                        results = [movie]
                        query = tmdb_id
                    else:
                        results = []
                        query = tmdb_id
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
    
    # Top production companies
    all_companies = []
    for dvd in DVD.objects.filter(production_companies__isnull=False).exclude(production_companies=''):
        if dvd.production_companies:
            companies_list = [company.strip() for company in dvd.production_companies.split(',')]
            all_companies.extend(companies_list)
    
    company_counts = Counter(all_companies)
    top_production_companies = company_counts.most_common(10)
    
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
        'top_production_companies': top_production_companies,
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
        elif field == 'location':
            dvd.location = value
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


def admin_settings(request):
    """Admin page for managing application settings."""
    settings = AppSettings.get_settings()
    
    # Get torrent statistics
    total_dvds = DVD.objects.count()
    dvds_with_imdb = DVD.objects.exclude(imdb_id='').exclude(imdb_id__isnull=True).count()
    dvds_with_torrents = DVD.objects.filter(has_cached_torrents=True).count()
    dvds_without_torrents = DVD.objects.filter(has_cached_torrents=False).count()
    stale_torrent_data = DVD.objects.filter(
        models.Q(yts_last_updated__isnull=True) |
        models.Q(yts_last_updated__lt=timezone.now() - timedelta(weeks=1))
    ).exclude(imdb_id='').exclude(imdb_id__isnull=True).count()
    
    if request.method == 'POST':
        # Handle torrent operations
        if 'refresh_flags' in request.POST:
            updated_count = 0
            for dvd in DVD.objects.all():
                old_flag = dvd.has_cached_torrents
                has_torrents = bool(dvd.yts_data and len(dvd.yts_data) > 0)
                if old_flag != has_torrents:
                    dvd.has_cached_torrents = has_torrents
                    dvd.save(update_fields=['has_cached_torrents'])
                    updated_count += 1
            
            messages.success(request, f'Updated torrent availability flags for {updated_count} DVDs.')
            return redirect('tracker:admin_settings')
        
        elif 'refresh_small_batch' in request.POST:
            # Refresh a small batch (10 DVDs) for immediate feedback
            dvds_to_refresh = DVD.objects.filter(
                models.Q(imdb_id__isnull=False) & ~models.Q(imdb_id=''),
                models.Q(yts_last_updated__isnull=True) |
                models.Q(yts_last_updated__lt=timezone.now() - timedelta(weeks=1))
            )[:10]
            
            success_count = 0
            for dvd in dvds_to_refresh:
                try:
                    if dvd.refresh_yts_data():
                        success_count += 1
                except Exception:
                    pass  # Continue with other DVDs
            
            if success_count > 0:
                messages.success(request, f'Refreshed torrent data for {success_count} DVDs.')
            else:
                messages.info(request, 'No DVDs were refreshed. They may already be up to date.')
            return redirect('tracker:admin_settings')
        
        # Handle TMDB settings
        elif 'tmdb_api_key' in request.POST:
            tmdb_api_key = request.POST.get('tmdb_api_key', '').strip()
            
            # Update the settings
            settings.tmdb_api_key = tmdb_api_key
            settings.save()
            
            messages.success(request, 'Settings updated successfully.')
            return redirect('tracker:admin_settings')
    
    context = {
        'settings': settings,
        'total_dvds': total_dvds,
        'dvds_with_imdb': dvds_with_imdb,
        'dvds_with_torrents': dvds_with_torrents,
        'dvds_without_torrents': dvds_without_torrents,
        'stale_torrent_data': stale_torrent_data,
        'torrent_coverage': (dvds_with_torrents / total_dvds * 100) if total_dvds > 0 else 0,
        'page_title': 'Admin Settings',
        'page_icon': 'gear',
    }
    return render(request, 'tracker/admin_settings.html', context)


def export_non_kept_dvds(request):
    """Export DVDs that are not in 'Kept' status to CSV."""
    # Get all DVDs that are not kept
    non_kept_dvds = DVD.objects.exclude(status='kept')
    
    # Generate filename with current date
    current_date = date.today().strftime('%Y-%m-%d')
    filename = f"Non-Kept_MovieExport_{current_date}.csv"
    
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
    
    writer = csv.writer(response)
    writer.writerow(['Movie Name', 'Release Year', 'Status', 'Media Type', '720p Download Link', '1080p Download Link'])
    
    # Initialize YTS service for getting torrent links
    yts_service = YTSService()
    
    for dvd in non_kept_dvds:
        # Get torrent information if IMDB ID is available
        link_720p = ''
        link_1080p = ''
        
        if dvd.imdb_id:
            torrents = yts_service.get_quality_torrents(dvd.imdb_id, ['720p', '1080p'])
            
            # Find specific quality links
            for torrent in torrents:
                if torrent.get('quality') == '720p':
                    link_720p = torrent.get('url', '')
                elif torrent.get('quality') == '1080p':
                    link_1080p = torrent.get('url', '')
        
        writer.writerow([
            dvd.name,
            dvd.release_year or '',
            dvd.get_status_display(),
            dvd.get_media_type_display(),
            link_720p,
            link_1080p
        ])
    
    return response


def export_complete_collection(request):
    """Export complete collection data to CSV with comprehensive information."""
    # Get all DVDs in the collection
    all_dvds = DVD.objects.all().order_by('-created_at')
    
    # Generate filename with current date
    current_date = date.today().strftime('%Y-%m-%d')
    filename = f"CollectionExport_{current_date}.csv"
    
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
    
    writer = csv.writer(response)
    
    # Write header row with all requested fields
    writer.writerow([
        'Movie Name',
        'Status', 
        'Release Year',
        'Runtime',
        'Tartan Release',
        'Media Type',
        'Box Set',
        'Storage Box',
        'Location',
        'Box Set Name',
        'Date Added',
        'Date Updated',
        'Torrent File Links',
        'Director',
        'IMDB ID',
        'TMDB ID',
        'Copy Number',
        'Duplicate Notes'
    ])
    
    # Initialize YTS service for getting torrent links
    yts_service = YTSService()
    
    for dvd in all_dvds:
        # Get torrent information if IMDB ID is available
        torrent_links = ''
        
        if dvd.imdb_id:
            try:
                torrents = yts_service.get_quality_torrents(dvd.imdb_id, ['720p', '1080p'])
                
                # Build torrent links string
                torrent_parts = []
                for torrent in torrents:
                    quality = torrent.get('quality', 'Unknown')
                    url = torrent.get('url', '')
                    if url:
                        torrent_parts.append(f"{quality}: {url}")
                
                torrent_links = ' | '.join(torrent_parts)
            except Exception as e:
                logger.error(f"Error fetching torrents for {dvd.name}: {e}")
                torrent_links = 'Error fetching torrents'
        
        writer.writerow([
            dvd.name,
            dvd.get_status_display(),
            dvd.release_year or '',
            f"{dvd.runtime} minutes" if dvd.runtime else '',
            'Yes' if dvd.is_tartan_dvd else 'No',
            dvd.get_media_type_display(),
            'Yes' if dvd.is_box_set else 'No',
            dvd.storage_box or '',
            dvd.location or '',
            dvd.box_set_name or '',
            dvd.created_at.strftime('%Y-%m-%d %H:%M:%S') if dvd.created_at else '',
            dvd.updated_at.strftime('%Y-%m-%d %H:%M:%S') if dvd.updated_at else '',
            torrent_links,
            dvd.director or '',
            dvd.imdb_id or '',
            dvd.tmdb_id or '',
            dvd.copy_number or 1,
            dvd.duplicate_notes or ''
        ])
    
    return response


def export_disposed_for_download(request):
    """Export disposed DVDs (excluding downloaded) with torrent links to CSV."""
    
    # Filter DVDs: Status = 'disposed' AND Media Type != 'downloaded'
    disposed_dvds = DVD.objects.filter(
        status='disposed'
    ).exclude(
        media_type='downloaded'
    ).order_by('name')
    
    # Generate filename with current date
    current_date = date.today().strftime('%Y-%m-%d')
    filename = f"DisposedDVDs_{current_date}.csv"
    
    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Movie Name',
        'Status', 
        '720p Torrent Link',
        '1080p Torrent Link'
    ])
    
    # Initialize YTS service for torrent links
    yts_service = YTSService()
    
    # Write data rows
    for dvd in disposed_dvds:
        # Get torrent links
        torrent_720p = ''
        torrent_1080p = ''
        
        if dvd.imdb_id:
            try:
                # Get torrents for this movie
                torrents = yts_service.get_movie_torrents(dvd.imdb_id)
                
                # Extract specific quality links
                for torrent in torrents:
                    quality = torrent.get('quality', '').lower()
                    if quality == '720p' and not torrent_720p:
                        torrent_720p = torrent.get('url', '')
                    elif quality == '1080p' and not torrent_1080p:
                        torrent_1080p = torrent.get('url', '')
            except Exception as e:
                # If torrent fetching fails, continue with empty links
                logger.error(f"Error fetching torrents for {dvd.name}: {e}")
                pass
        
        writer.writerow([
            dvd.name,
            dvd.get_status_display(),
            torrent_720p,
            torrent_1080p
        ])
    
    return response


def bulk_upload_preview(request):
    """Preview and correct TMDB matches before bulk creating DVDs."""
    # Check if we have session data
    bulk_data = request.session.get('bulk_upload_data')
    if not bulk_data:
        messages.error(request, 'No bulk upload data found. Please start over.')
        return redirect('tracker:bulk_upload')
    
    # Check session expiry (24 hours)
    from datetime import datetime, timedelta
    try:
        timestamp = datetime.fromisoformat(bulk_data['timestamp'])
        if datetime.now() - timestamp > timedelta(hours=24):
            messages.error(request, 'Bulk upload session expired. Please start over.')
            del request.session['bulk_upload_data']
            return redirect('tracker:bulk_upload')
    except (ValueError, KeyError):
        messages.error(request, 'Invalid session data. Please start over.')
        del request.session['bulk_upload_data']
        return redirect('tracker:bulk_upload')
    
    if request.method == 'POST':
        # Handle different actions
        if 'search_correction' in request.POST:
            # Handle individual movie search correction
            index = int(request.POST.get('match_index'))
            query = request.POST.get('search_query', '').strip()
            
            if query and 0 <= index < len(bulk_data['matches']):
                tmdb_service = TMDBService()
                search_results = tmdb_service.search_movies(query)
                results = search_results.get('results', [])
                
                # Add poster URLs to results
                for movie in results:
                    if movie.get('poster_path'):
                        movie['poster_url'] = tmdb_service.get_full_poster_url(movie['poster_path'])
                    else:
                        movie['poster_url'] = None
                
                context = {
                    'search_results': results,
                    'query': query,
                    'match_index': index,
                    'original_title': bulk_data['matches'][index]['original_title'],
                    'bulk_data': bulk_data
                }
                return render(request, 'tracker/bulk_upload_search.html', context)
        
        elif 'update_match' in request.POST:
            # Update a specific match with new TMDB data
            index = int(request.POST.get('match_index'))
            tmdb_id = request.POST.get('tmdb_id')
            
            if tmdb_id and 0 <= index < len(bulk_data['matches']):
                tmdb_service = TMDBService()
                movie_data = tmdb_service.get_movie_details(tmdb_id)
                
                if movie_data:
                    # Update the match in session
                    poster_url = None
                    if movie_data.get('poster_path'):
                        poster_url = tmdb_service.get_full_poster_url(movie_data['poster_path'])
                    
                    bulk_data['matches'][index].update({
                        'tmdb_data': movie_data,
                        'confirmed': True,
                        'poster_url': poster_url,
                        'error': None
                    })
                    
                    request.session['bulk_upload_data'] = bulk_data
                    messages.success(request, f'Updated match for "{bulk_data["matches"][index]["original_title"]}"')
                else:
                    messages.error(request, 'Could not fetch movie details from TMDB.')
            
            return redirect('tracker:bulk_upload_preview')
        
        elif 'remove_match' in request.POST:
            # Remove a match from the list
            index = int(request.POST.get('match_index'))
            
            if 0 <= index < len(bulk_data['matches']):
                bulk_data['matches'][index]['removed'] = True
                request.session['bulk_upload_data'] = bulk_data
                messages.info(request, f'Removed "{bulk_data["matches"][index]["original_title"]}" from the list.')
            
            return redirect('tracker:bulk_upload_preview')
        
        elif 'restore_match' in request.POST:
            # Restore a removed match
            index = int(request.POST.get('match_index'))
            
            if 0 <= index < len(bulk_data['matches']):
                bulk_data['matches'][index]['removed'] = False
                request.session['bulk_upload_data'] = bulk_data
                messages.info(request, f'Restored "{bulk_data["matches"][index]["original_title"]}" to the list.')
            
            return redirect('tracker:bulk_upload_preview')
        
        elif 'proceed' in request.POST:
            # Proceed to final processing
            return redirect('tracker:bulk_upload_process')
    
    # Calculate statistics for display
    total_matches = len(bulk_data['matches'])
    confirmed_matches = len([m for m in bulk_data['matches'] if m['confirmed'] and not m['removed']])
    removed_matches = len([m for m in bulk_data['matches'] if m['removed']])
    error_matches = len([m for m in bulk_data['matches'] if m.get('error') and not m['removed']])
    
    # Check for duplicates and add detailed duplicate info
    for match in bulk_data['matches']:
        if match['tmdb_data'] and not match['removed']:
            tmdb_id = match['tmdb_data'].get('id')
            if tmdb_id:
                # Check for existing copies by TMDB ID
                existing_copies = DVD.objects.filter(tmdb_id=tmdb_id).order_by('copy_number')
                if existing_copies.exists():
                    match['duplicate_info'] = {
                        'is_duplicate': True,
                        'existing_copies': list(existing_copies),
                        'next_copy_number': existing_copies.aggregate(
                            max_copy=Max('copy_number')
                        )['max_copy'] + 1,
                        'total_copies': existing_copies.count()
                    }
                else:
                    match['duplicate_info'] = {'is_duplicate': False}
            else:
                # Fallback: check by name and release year
                movie_name = match['tmdb_data'].get('title', '')
                release_date = match['tmdb_data'].get('release_date', '')
                release_year = None
                if release_date:
                    try:
                        release_year = int(release_date.split('-')[0])
                    except (ValueError, IndexError):
                        pass
                
                if movie_name and release_year:
                    existing_copies = DVD.objects.filter(
                        name__iexact=movie_name,
                        release_year=release_year
                    ).order_by('copy_number')
                    if existing_copies.exists():
                        match['duplicate_info'] = {
                            'is_duplicate': True,
                            'existing_copies': list(existing_copies),
                            'next_copy_number': existing_copies.aggregate(
                                max_copy=Max('copy_number')
                            )['max_copy'] + 1,
                            'total_copies': existing_copies.count()
                        }
                    else:
                        match['duplicate_info'] = {'is_duplicate': False}
                else:
                    match['duplicate_info'] = {'is_duplicate': False}
        else:
            match['duplicate_info'] = {'is_duplicate': False}
    
    context = {
        'bulk_data': bulk_data,
        'total_matches': total_matches,
        'confirmed_matches': confirmed_matches,
        'removed_matches': removed_matches,
        'error_matches': error_matches,
        'can_proceed': confirmed_matches > 0,
    }
    
    return render(request, 'tracker/bulk_upload_preview.html', context)


def bulk_upload_process(request):
    """Final processing - create DVDs from confirmed matches."""
    # Check if we have session data
    bulk_data = request.session.get('bulk_upload_data')
    if not bulk_data:
        messages.error(request, 'No bulk upload data found. Please start over.')
        return redirect('tracker:bulk_upload')
    
    # Only allow POST to prevent accidental processing
    if request.method != 'POST':
        return redirect('tracker:bulk_upload_preview')
    
    form_defaults = bulk_data['form_defaults']
    tmdb_service = TMDBService()
    
    # Pre-calculate sequential location numbers for unboxed DVDs
    unboxed_matches = [
        match for match in bulk_data['matches'] 
        if not match['removed'] and match['tmdb_data'] and match['confirmed']
        and form_defaults['default_status'] == 'unboxed'
    ]
    
    if unboxed_matches and form_defaults['default_status'] == 'unboxed':
        sequential_locations = DVD.get_next_sequential_locations(len(unboxed_matches))
        location_iter = iter(sequential_locations)
    else:
        location_iter = iter([])
    
    results = {
        'added': [],
        'skipped': [],
        'errors': []
    }
    
    for match in bulk_data['matches']:
        # Skip removed matches or matches without TMDB data
        if match['removed'] or not match['tmdb_data'] or not match['confirmed']:
            continue
        
        try:
            movie_data = match['tmdb_data']
            tmdb_id = movie_data.get('id')
            
            # Check if movie already exists (if skip_existing is enabled)
            if form_defaults['skip_existing'] and DVD.objects.filter(tmdb_id=tmdb_id).exists():
                existing_dvd = DVD.objects.get(tmdb_id=tmdb_id)
                results['skipped'].append(f"{match['original_title']} (already have: {existing_dvd.name})")
                continue
            
            # Format movie data for DVD creation
            tmdb_formatted_data = tmdb_service.format_movie_data(movie_data)
            poster_path = tmdb_formatted_data.pop('poster_path', None)
            
            # Determine copy number for duplicates
            copy_number = 1
            if tmdb_id:
                # Check for existing copies by TMDB ID
                existing_copies = DVD.objects.filter(tmdb_id=tmdb_id)
                if existing_copies.exists():
                    copy_number = existing_copies.aggregate(
                        max_copy=Max('copy_number')
                    )['max_copy'] + 1
            else:
                # Fallback: check by name and release year
                movie_name = tmdb_formatted_data['name']
                release_year = tmdb_formatted_data['release_year']
                if movie_name and release_year:
                    existing_copies = DVD.objects.filter(
                        name__iexact=movie_name,
                        release_year=release_year
                    )
                    if existing_copies.exists():
                        copy_number = existing_copies.aggregate(
                            max_copy=Max('copy_number')
                        )['max_copy'] + 1
            
            # Assign location for unboxed DVDs
            assigned_location = ''
            if form_defaults['default_status'] == 'unboxed':
                try:
                    assigned_location = next(location_iter)
                except StopIteration:
                    # Fallback to getting next available location
                    assigned_location = str(DVD.get_next_location_number())
            elif form_defaults['default_status'] == 'kept':
                storage_box = form_defaults['default_storage_box']
            else:
                storage_box = ''
            
            # Create DVD entry
            dvd = DVD.objects.create(
                name=tmdb_formatted_data['name'],
                overview=tmdb_formatted_data['overview'],
                release_year=tmdb_formatted_data['release_year'],
                runtime=tmdb_formatted_data['runtime'],
                genres=tmdb_formatted_data['genres'],
                tmdb_id=tmdb_formatted_data['tmdb_id'],
                imdb_id=tmdb_formatted_data['imdb_id'],
                rating=tmdb_formatted_data['rating'],
                copy_number=copy_number,  # Set the proper copy number
                status=form_defaults['default_status'],
                media_type=form_defaults['default_media_type'],
                is_tartan_dvd=form_defaults['default_is_tartan_dvd'],
                is_box_set=form_defaults['default_is_box_set'],
                box_set_name=form_defaults['default_box_set_name'] if form_defaults['default_is_box_set'] else '',
                is_unopened=form_defaults['default_is_unopened'],
                is_unwatched=form_defaults['default_is_unwatched'],
                storage_box=form_defaults['default_storage_box'] if form_defaults['default_status'] == 'kept' else '',
                location=assigned_location
            )
            
            # Download poster if available
            if poster_path:
                full_poster_url = tmdb_service.get_full_poster_url(poster_path)
                tmdb_service.download_poster(dvd, full_poster_url)
            
            # Refresh YTS data immediately to populate torrent badge
            if dvd.imdb_id:
                dvd.refresh_yts_data()
            
            results['added'].append(dvd.name)
            
        except Exception as e:
            results['errors'].append(f"Error processing '{match['original_title']}': {str(e)}")
    
    # Clear session data
    del request.session['bulk_upload_data']
    
    # Show results to user
    if results['added']:
        messages.success(request, f"Successfully added {len(results['added'])} movies to your collection.")
    
    if results['skipped']:
        messages.info(request, f"Skipped {len(results['skipped'])} movies already in your collection.")
    
    if results['errors']:
        messages.error(request, f"Encountered {len(results['errors'])} errors during upload.")
    
    # Render results page
    context = {
        'results': results,
        'total_processed': len([m for m in bulk_data['matches'] if m['confirmed'] and not m['removed']])
    }
    return render(request, 'tracker/bulk_upload_results.html', context)


def bulk_mark_downloaded(request):
    """Bulk mark DVDs as downloaded by searching for movie titles."""
    if request.method == 'POST':
        form = BulkMarkDownloadedForm(request.POST)
        if form.is_valid():
            movie_list = form.cleaned_data['movie_list']
            
            # Split the movie list into individual titles
            movie_titles = [title.strip() for title in movie_list.split('\n') if title.strip()]
            
            results = {
                'found_and_updated': [],
                'already_downloaded': [],
                'not_found': [],
                'multiple_matches': []
            }
            
            for title in movie_titles:
                try:
                    # Search for exact matches first
                    exact_matches = DVD.objects.filter(name__iexact=title)
                    
                    if exact_matches.count() == 1:
                        dvd = exact_matches.first()
                        if dvd.media_type == 'download' and dvd.is_downloaded:
                            results['already_downloaded'].append(dvd.name)
                        else:
                            dvd.media_type = 'download'
                            dvd.is_downloaded = True
                            dvd.save()
                            results['found_and_updated'].append(dvd.name)
                    elif exact_matches.count() > 1:
                        # Multiple exact matches found
                        results['multiple_matches'].append({
                            'title': title,
                            'matches': [{'name': dvd.name, 'id': dvd.id, 'status': dvd.get_status_display()} for dvd in exact_matches]
                        })
                    else:
                        # Try fuzzy search with contains
                        fuzzy_matches = DVD.objects.filter(name__icontains=title)
                        
                        if fuzzy_matches.count() == 1:
                            dvd = fuzzy_matches.first()
                            if dvd.media_type == 'download' and dvd.is_downloaded:
                                results['already_downloaded'].append(dvd.name)
                            else:
                                dvd.media_type = 'download'
                                dvd.is_downloaded = True
                                dvd.save()
                                results['found_and_updated'].append(dvd.name)
                        elif fuzzy_matches.count() > 1:
                            # Multiple fuzzy matches found
                            results['multiple_matches'].append({
                                'title': title,
                                'matches': [{'name': dvd.name, 'id': dvd.id, 'status': dvd.get_status_display()} for dvd in fuzzy_matches]
                            })
                        else:
                            # No matches found
                            results['not_found'].append(title)
                            
                except Exception as e:
                    logger.error(f"Error processing '{title}': {e}")
                    results['not_found'].append(f"{title} (Error: {str(e)})")
            
            # Show results to user
            if results['found_and_updated']:
                messages.success(request, f"Successfully marked {len(results['found_and_updated'])} movies as downloaded.")
            
            if results['already_downloaded']:
                messages.info(request, f"{len(results['already_downloaded'])} movies were already marked as downloaded.")
            
            if results['not_found']:
                messages.warning(request, f"{len(results['not_found'])} movies could not be found in your collection.")
                
            if results['multiple_matches']:
                messages.warning(request, f"{len(results['multiple_matches'])} movie titles had multiple matches. Review the results below.")
            
            # Render results page
            context = {
                'results': results,
                'total_processed': len(movie_titles)
            }
            return render(request, 'tracker/bulk_mark_downloaded_results.html', context)
    else:
        form = BulkMarkDownloadedForm()
    
    return render(request, 'tracker/bulk_mark_downloaded.html', {'form': form})


@require_http_methods(["POST"])
def refresh_yts_data(request, pk):
    """AJAX endpoint to refresh YTS torrent data for a specific DVD."""
    try:
        dvd = get_object_or_404(DVD, pk=pk)
        
        if not dvd.imdb_id:
            return JsonResponse({
                'success': False,
                'error': 'IMDB ID is required to fetch torrent data'
            })
        
        # Refresh the YTS data
        success = dvd.refresh_yts_data()
        
        if success:
            torrents = dvd.get_cached_torrents()
            torrent_count = len(torrents) if torrents else 0
            
            return JsonResponse({
                'success': True,
                'message': f'YTS data refreshed successfully. Found {torrent_count} torrents.',
                'torrent_count': torrent_count,
                'last_updated': dvd.yts_last_updated.strftime('%B %d, %Y at %I:%M %p') if dvd.yts_last_updated else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to refresh YTS data'
            })
            
    except Exception as e:
        logger.error(f"Error refreshing YTS data for DVD {pk}: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while refreshing torrent data'
        })
