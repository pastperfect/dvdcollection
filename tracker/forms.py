from django import forms
from .models import DVD
import requests
from django.conf import settings



class DVDSearchForm(forms.Form):
    """Form for searching movies in TMDB by title or TMDB ID."""
    SEARCH_TYPE_CHOICES = [
        ('title', 'Title'),
        ('tmdb_id', 'TMDB ID'),
    ]
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_search_type'}),
        initial='title',
        required=False
    )
    query = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for a movie...',
            'autocomplete': 'off',
            'id': 'id_query',
        })
    )
    tmdb_id = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter TMDB ID (e.g. 603)',
            'autocomplete': 'off',
            'id': 'id_tmdb_id',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        search_type = cleaned_data.get('search_type', 'title')
        query = cleaned_data.get('query', '').strip()
        tmdb_id = cleaned_data.get('tmdb_id', '').strip()
        if search_type == 'title':
            if not query:
                self.add_error('query', 'Please enter a movie title to search.')
        elif search_type == 'tmdb_id':
            if not tmdb_id:
                self.add_error('tmdb_id', 'Please enter a TMDB ID to search.')
            elif not tmdb_id.isdigit():
                self.add_error('tmdb_id', 'TMDB ID must be a number.')
        return cleaned_data


class DVDForm(forms.ModelForm):
    """Form for creating/editing DVD entries."""
    
    class Meta:
        model = DVD
        fields = [
            'tmdb_id', 'name', 'status', 'media_type', 'overview', 'imdb_id', 'poster',
            'is_tartan_dvd', 'is_box_set', 'box_set_name', 'is_unopened', 'is_unwatched', 'storage_box', 'location',
            'copy_number', 'duplicate_notes'
        ]
        widgets = {
            'tmdb_id': forms.HiddenInput(),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Movie title'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_status'
            }),
            'media_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'overview': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Movie overview/description'
            }),
            'imdb_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IMDB ID (e.g., tt1234567)',
                'pattern': 'tt[0-9]+',
                'title': 'IMDB ID should start with "tt" followed by numbers'
            }),
            'poster': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_poster'
            }),
            'is_tartan_dvd': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_box_set': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'id_is_box_set'
            }),
            'box_set_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter box set name...',
                'id': 'id_box_set_name'
            }),
            'is_unopened': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_unwatched': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'storage_box': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter storage box location...',
                'id': 'id_storage_box'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location...',
                'id': 'id_location'
            }),
            'copy_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '99',
                'placeholder': '1'
            }),
            'duplicate_notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., "Director\'s Cut", "Region 2", "Special Edition"',
                'maxlength': '255'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add some JavaScript to show/hide box set name field
        self.fields['box_set_name'].widget.attrs['style'] = 'display: none;' if not self.instance.is_box_set else ''
        # Show/hide location field based on status
        if self.instance and self.instance.status == 'unboxed':
            self.fields['location'].widget.attrs['style'] = ''
        else:
            self.fields['location'].widget.attrs['style'] = 'display: none;'
    
    def clean_poster(self):
        """Validate uploaded poster image."""
        poster = self.cleaned_data.get('poster')
        
        if poster:
            # Check file size (max 5MB)
            if poster.size > 5 * 1024 * 1024:
                raise forms.ValidationError('Image file too large. Maximum size is 5MB.')
            
            # Check file type
            if not poster.content_type.startswith('image/'):
                raise forms.ValidationError('File must be an image.')
            
            # Check specific image formats
            allowed_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if poster.content_type not in allowed_formats:
                raise forms.ValidationError('Unsupported image format. Please use JPEG, PNG, GIF, or WebP.')
        
        return poster
    
    def clean_location(self):
        """Validate location field for uniqueness when status is unboxed."""
        location = self.cleaned_data.get('location', '').strip()
        status = self.cleaned_data.get('status')
        
        # Only validate location if status is unboxed and location is provided
        if status == 'unboxed' and location:
            # Check if location is numeric
            if not location.isdigit():
                raise forms.ValidationError('Location must be a number.')
            
            # Check for duplicates
            exclude_pk = self.instance.pk if self.instance else None
            if DVD.is_location_taken(location, exclude_pk=exclude_pk):
                raise forms.ValidationError(f'Location {location} is already taken by another unboxed DVD.')
        
        return location
    
    def clean(self):
        """Additional form validation."""
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        location = cleaned_data.get('location', '').strip()
        
        # Require location for unboxed status
        if status == 'unboxed' and not location:
            self.add_error('location', 'Location is required when status is Unboxed.')
        
        # Clear location if status is not unboxed
        if status != 'unboxed':
            cleaned_data['location'] = ''
            
        return cleaned_data


class DVDFilterForm(forms.Form):
    """Form for filtering DVDs."""
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title...',
            'autocomplete': 'off'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + DVD.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    media_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Media Types')] + DVD.MEDIA_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_tartan_dvd = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Tartan DVDs'), ('false', 'Non-Tartan')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_box_set = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Box Sets'), ('false', 'Individual Movies')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_unopened = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Unopened'), ('false', 'Opened')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_unwatched = forms.ChoiceField(
        required=False,
        choices=[('', 'All'), ('true', 'Unwatched'), ('false', 'Watched')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    production_company = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by production company...',
            'autocomplete': 'off'
        })
    )


class BulkUploadForm(forms.Form):
    """Form for bulk uploading movies."""
    movie_list = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 15,
            'placeholder': 'Enter movie titles, one per line:\n\nThe Matrix\nInception\nInterstellar\nThe Dark Knight\nPulp Fiction',
            'style': 'font-family: monospace;'
        }),
        help_text='Enter one movie title per line. We\'ll search TMDB for each movie.'
    )
    
    default_status = forms.ChoiceField(
        choices=DVD.STATUS_CHOICES,
        initial='kept',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Default status for all uploaded movies'
    )
    
    default_media_type = forms.ChoiceField(
        choices=DVD.MEDIA_TYPE_CHOICES,
        initial='physical',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='Default media type for all uploaded movies'
    )
    
    skip_existing = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Skip movies that are already in your collection'
    )
    
    # DVD-specific fields
    default_is_tartan_dvd = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Mark all uploaded movies as Tartan DVD releases'
    )
    
    default_is_box_set = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Mark all uploaded movies as part of a box set'
    )
    
    default_box_set_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter box set name...'
        }),
        help_text='Default box set name (only used if "Part of Box Set" is checked)'
    )
    
    default_is_unopened = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Mark all uploaded movies as still unopened'
    )
    
    default_is_unwatched = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        help_text='Mark all uploaded movies as unwatched'
    )
    
    default_storage_box = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter storage box location...'
        }),
        help_text='Default storage box location for kept movies'
    )
    
    default_location = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter location...'
        }),
        help_text='Default location for unboxed movies'
    )
