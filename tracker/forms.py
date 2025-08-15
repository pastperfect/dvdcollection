from django import forms
from .models import DVD
import requests
from django.conf import settings


class DVDSearchForm(forms.Form):
    """Form for searching movies in TMDB."""
    query = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for a movie...',
            'autocomplete': 'off'
        })
    )


class DVDForm(forms.ModelForm):
    """Form for creating/editing DVD entries."""
    
    class Meta:
        model = DVD
        fields = [
            'name', 'status', 'media_type', 'overview', 'imdb_id',
            'is_tartan_dvd', 'is_box_set', 'box_set_name', 'is_unopened', 'is_unwatched', 'storage_box'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Movie title'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
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
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add some JavaScript to show/hide box set name field
        self.fields['box_set_name'].widget.attrs['style'] = 'display: none;' if not self.instance.is_box_set else ''


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
