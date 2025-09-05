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
