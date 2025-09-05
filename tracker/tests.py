from django.test import TestCase
from django.urls import reverse
from .models import DVD


class DVDModelTest(TestCase):
    def setUp(self):
        self.dvd = DVD.objects.create(
            name="Test Movie",
            status="kept",
            media_type="physical",
            overview="A test movie",
            release_year=2023,
            genres="Action, Comedy",
            runtime=120,
            rating=7.5
        )

    def test_string_representation(self):
        self.assertEqual(str(self.dvd), "Test Movie")

    def test_get_genres_list(self):
        self.assertEqual(self.dvd.get_genres_list(), ["Action", "Comedy"])

    def test_get_status_display_class(self):
        self.assertEqual(self.dvd.get_status_display_class(), "success")
        
        self.dvd.status = "disposed"
        self.assertEqual(self.dvd.get_status_display_class(), "danger")


class DVDViewTest(TestCase):
    def setUp(self):
        self.dvd = DVD.objects.create(
            name="Test Movie",
            status="kept",
            media_type="physical"
        )

    def test_dvd_list_view(self):
        response = self.client.get(reverse('tracker:dvd_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Movie")

    def test_dvd_detail_view(self):
        response = self.client.get(reverse('tracker:dvd_detail', kwargs={'pk': self.dvd.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Movie")


class BulkUploadPreviewTest(TestCase):
    def test_bulk_upload_view_get(self):
        """Test that bulk upload form displays correctly"""
        response = self.client.get(reverse('tracker:bulk_upload'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bulk Upload Movies')
        self.assertContains(response, 'movie_list')

    def test_bulk_upload_preview_without_session(self):
        """Test that preview redirects to bulk upload if no session data"""
        response = self.client.get(reverse('tracker:bulk_upload_preview'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tracker:bulk_upload'))

    def test_bulk_upload_process_without_session(self):
        """Test that process redirects to bulk upload if no session data"""
        response = self.client.get(reverse('tracker:bulk_upload_process'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tracker:bulk_upload'))

    def test_bulk_upload_with_session_data(self):
        """Test bulk upload preview with valid session data"""
        # Simulate session data
        session = self.client.session
        session['bulk_upload_data'] = {
            'form_defaults': {
                'default_status': 'kept',
                'default_media_type': 'physical',
                'skip_existing': True,
                'default_is_tartan_dvd': False,
                'default_is_box_set': False,
                'default_box_set_name': '',
                'default_is_unopened': False,
                'default_is_unwatched': True,
                'default_storage_box': ''
            },
            'matches': [
                {
                    'original_title': 'Test Movie',
                    'tmdb_data': {
                        'id': 12345,
                        'title': 'Test Movie',
                        'overview': 'A test movie',
                        'release_date': '2023-01-01'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': '2025-09-05T12:00:00'
        }
        session.save()

        response = self.client.get(reverse('tracker:bulk_upload_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bulk Upload Preview')
        self.assertContains(response, 'Test Movie')

    def test_bulk_upload_process_creates_dvds(self):
        """Test that bulk upload process actually creates DVDs"""
        # Set up session data
        session = self.client.session
        session['bulk_upload_data'] = {
            'form_defaults': {
                'default_status': 'kept',
                'default_media_type': 'physical',
                'skip_existing': True,
                'default_is_tartan_dvd': False,
                'default_is_box_set': False,
                'default_box_set_name': '',
                'default_is_unopened': False,
                'default_is_unwatched': True,
                'default_storage_box': ''
            },
            'matches': [
                {
                    'original_title': 'Test Movie Process',
                    'tmdb_data': {
                        'id': 12346,
                        'title': 'Test Movie Process',
                        'overview': 'A test movie for processing',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Action'}, {'name': 'Drama'}],
                        'vote_average': 7.5,
                        'imdb_id': 'tt1234567'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': '2025-09-05T12:00:00'
        }
        session.save()

        # Verify no DVDs exist initially
        initial_count = DVD.objects.count()

        # Submit to process view
        response = self.client.post(reverse('tracker:bulk_upload_process'))
        
        # Should redirect to results page (or render results template)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bulk Upload Results')
        
        # Verify DVD was created
        self.assertEqual(DVD.objects.count(), initial_count + 1)
        
        # Verify DVD details
        dvd = DVD.objects.get(tmdb_id=12346)
        self.assertEqual(dvd.name, 'Test Movie Process')
        self.assertEqual(dvd.status, 'kept')
        self.assertEqual(dvd.media_type, 'physical')
        
        # Verify session was cleared
        self.assertNotIn('bulk_upload_data', self.client.session)

    def test_bulk_upload_duplicate_detection(self):
        """Test that duplicate detection works in preview"""
        # Create an existing DVD
        existing_dvd = DVD.objects.create(
            name="Test Duplicate Movie",
            tmdb_id=99999,
            status="kept",
            media_type="physical",
            copy_number=1
        )

        # Set up session data with a movie that matches the existing one
        session = self.client.session
        session['bulk_upload_data'] = {
            'form_defaults': {
                'default_status': 'kept',
                'default_media_type': 'physical',
                'skip_existing': False,  # Allow duplicates
                'default_is_tartan_dvd': False,
                'default_is_box_set': False,
                'default_box_set_name': '',
                'default_is_unopened': False,
                'default_is_unwatched': True,
                'default_storage_box': ''
            },
            'matches': [
                {
                    'original_title': 'Test Duplicate Movie',
                    'tmdb_data': {
                        'id': 99999,
                        'title': 'Test Duplicate Movie',
                        'overview': 'A duplicate test movie',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Action'}],
                        'vote_average': 7.5,
                        'imdb_id': 'tt9999999'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': '2025-09-05T12:00:00'
        }
        session.save()

        # Get the preview page
        response = self.client.get(reverse('tracker:bulk_upload_preview'))
        self.assertEqual(response.status_code, 200)
        
        # Check that duplicate information is displayed
        self.assertContains(response, 'Duplicate')
        self.assertContains(response, 'You have 1 copy(ies)')
        self.assertContains(response, 'This will be copy #2')

    def test_bulk_upload_creates_duplicate_with_correct_copy_number(self):
        """Test that duplicates are created with correct copy numbers"""
        # Create an existing DVD
        existing_dvd = DVD.objects.create(
            name="Test Duplicate Create",
            tmdb_id=88888,
            status="kept",
            media_type="physical",
            copy_number=1
        )

        # Set up session data
        session = self.client.session
        session['bulk_upload_data'] = {
            'form_defaults': {
                'default_status': 'kept',
                'default_media_type': 'download',
                'skip_existing': False,  # Allow duplicates
                'default_is_tartan_dvd': False,
                'default_is_box_set': False,
                'default_box_set_name': '',
                'default_is_unopened': False,
                'default_is_unwatched': True,
                'default_storage_box': ''
            },
            'matches': [
                {
                    'original_title': 'Test Duplicate Create',
                    'tmdb_data': {
                        'id': 88888,
                        'title': 'Test Duplicate Create',
                        'overview': 'A duplicate creation test',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Drama'}],
                        'vote_average': 8.0,
                        'imdb_id': 'tt8888888'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': '2025-09-05T12:00:00'
        }
        session.save()

        # Process the upload
        response = self.client.post(reverse('tracker:bulk_upload_process'))
        self.assertEqual(response.status_code, 200)

        # Verify both DVDs exist
        dvds = DVD.objects.filter(tmdb_id=88888).order_by('copy_number')
        self.assertEqual(dvds.count(), 2)
        
        # Verify copy numbers
        self.assertEqual(dvds[0].copy_number, 1)
        self.assertEqual(dvds[0].media_type, 'physical')  # Original
        self.assertEqual(dvds[1].copy_number, 2)
        self.assertEqual(dvds[1].media_type, 'download')  # New duplicate

    def test_bulk_upload_skips_existing_when_enabled(self):
        """Test that existing movies are skipped when skip_existing is True"""
        # Create an existing DVD
        existing_dvd = DVD.objects.create(
            name="Test Skip Movie",
            tmdb_id=77777,
            status="kept",
            media_type="physical",
            copy_number=1
        )

        # Set up session data with skip_existing=True
        session = self.client.session
        session['bulk_upload_data'] = {
            'form_defaults': {
                'default_status': 'kept',
                'default_media_type': 'physical',
                'skip_existing': True,  # Skip duplicates
                'default_is_tartan_dvd': False,
                'default_is_box_set': False,
                'default_box_set_name': '',
                'default_is_unopened': False,
                'default_is_unwatched': True,
                'default_storage_box': ''
            },
            'matches': [
                {
                    'original_title': 'Test Skip Movie',
                    'tmdb_data': {
                        'id': 77777,
                        'title': 'Test Skip Movie',
                        'overview': 'A movie to skip',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Comedy'}],
                        'vote_average': 6.0,
                        'imdb_id': 'tt7777777'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': '2025-09-05T12:00:00'
        }
        session.save()

        # Process the upload
        response = self.client.post(reverse('tracker:bulk_upload_process'))
        self.assertEqual(response.status_code, 200)

        # Verify only one DVD exists (the original)
        dvds = DVD.objects.filter(tmdb_id=77777)
        self.assertEqual(dvds.count(), 1)
        self.assertEqual(dvds[0].copy_number, 1)

        # Verify skip message is shown
        self.assertContains(response, 'Skipped')
        self.assertContains(response, 'already have')
