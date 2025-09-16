from django.test import TestCase
from django.urls import reverse
from django.core.management import call_command
from .models import DVD
from .forms import DVDForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile
from io import StringIO
from datetime import datetime


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


class DVDFormTest(TestCase):
    def test_clean_poster_with_existing_file(self):
        """Test that editing a DVD with an existing poster doesn't raise AttributeError"""
        # Create a DVD with a poster
        dvd = DVD.objects.create(
            name="Test Movie with Poster",
            status="kept",
            media_type="physical"
        )
        
        # Create a simple valid PNG image (1x1 pixel) and assign it
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        test_image = SimpleUploadedFile("test.jpg", png_data, content_type="image/jpeg")
        dvd.poster = test_image
        dvd.save()
        
        # Now test editing this DVD - the poster field will be an ImageFieldFile
        form_data = {
            'name': 'Updated Movie Name',
            'status': 'kept',
            'media_type': 'physical',
            'overview': 'Test overview',
            'copy_number': 1  # Add required field
        }
        
        # Create form with the existing DVD instance (poster will be ImageFieldFile)
        form = DVDForm(data=form_data, instance=dvd)
        
        # This should not raise AttributeError: 'ImageFieldFile' object has no attribute 'content_type'
        try:
            is_valid = form.is_valid()
            # The form might be invalid for other reasons, but it shouldn't crash
            self.assertTrue(True, "Form validation completed without AttributeError")
        except AttributeError as e:
            if "content_type" in str(e):
                self.fail(f"Form validation failed with AttributeError: {e}")
            else:
                raise  # Re-raise if it's a different AttributeError

    def test_clean_poster_with_new_upload(self):
        """Test that uploading a new image still validates content type"""
        # Create a simple valid PNG image (1x1 pixel)
        import base64
        from io import BytesIO
        
        # This is a tiny valid PNG image (1x1 pixel)
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        )
        test_image = SimpleUploadedFile("test.png", png_data, content_type="image/png")
        
        form_data = {
            'name': 'New Movie',
            'status': 'kept',
            'media_type': 'physical',
            'overview': 'Test overview',
            'copy_number': 1  # Add required field
        }
        
        file_data = {
            'poster': test_image
        }
        
        form = DVDForm(data=form_data, files=file_data)
        
        # This should validate successfully
        self.assertTrue(form.is_valid(), f"Form should be valid, errors: {form.errors}")

    def test_clean_poster_with_invalid_content_type(self):
        """Test that uploading an invalid file type raises validation error"""
        # Create a non-image file
        text_content = b"this is not an image"
        test_file = SimpleUploadedFile("test.txt", text_content, content_type="text/plain")
        
        form_data = {
            'name': 'New Movie',
            'status': 'kept',
            'media_type': 'physical',
            'overview': 'Test overview',
            'copy_number': 1  # Add required field
        }
        
        file_data = {
            'poster': test_file
        }
        
        form = DVDForm(data=form_data, files=file_data)
        
        # This should be invalid due to wrong content type
        self.assertFalse(form.is_valid())
        self.assertIn('poster', form.errors)
        # Django's ImageField validation message, not our custom one
        self.assertIn('Upload a valid image', str(form.errors['poster']))


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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False
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
            'timestamp': datetime.now().isoformat()
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False
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
            'timestamp': datetime.now().isoformat()
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False
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
            'timestamp': datetime.now().isoformat()
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False
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
            'timestamp': datetime.now().isoformat()
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False
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
            'timestamp': datetime.now().isoformat()
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


class NormalizeUKCertificationsCommandTestCase(TestCase):
    """Test the normalize_uk_certifications management command."""
    
    def setUp(self):
        """Create test DVDs with various certification formats."""
        self.dvds = []
        
        # Create DVDs with various certification formats
        test_data = [
            ('Movie A', 'PG'),      # Should be normalized to 'pg'
            ('Movie B', '12A'),     # Should be normalized to '12a'
            ('Movie C', 'U'),       # Should be normalized to 'u'
            ('Movie D', 'pg'),      # Already normalized
            ('Movie E', '15'),      # Already normalized (numbers)
            ('Movie F', ''),        # Empty certification
        ]
        
        for name, cert in test_data:
            dvd = DVD.objects.create(
                name=name,
                uk_certification='temp'  # Bypass the save method initially
            )
            # Now directly update the certification to bypass the model's save method
            DVD.objects.filter(pk=dvd.pk).update(uk_certification=cert)
            dvd.refresh_from_db()
            self.dvds.append(dvd)
    
    def test_dry_run_shows_correct_updates(self):
        """Test that dry run shows the correct DVDs that need updating."""
        out = StringIO()
        call_command('normalize_uk_certifications', '--dry-run', stdout=out)
        
        output = out.getvalue()
        
        # Should identify 3 DVDs that need updating (PG, 12A, U)
        self.assertIn('Found 3 DVDs that need certification normalization', output)
        self.assertIn('Movie A', output)
        self.assertIn('Movie B', output)
        self.assertIn('Movie C', output)
        self.assertIn("'PG' → 'pg'", output)
        self.assertIn("'12A' → '12a'", output)
        self.assertIn("'U' → 'u'", output)
    
    def test_actual_normalization(self):
        """Test that the command actually normalizes the certifications."""
        out = StringIO()
        call_command('normalize_uk_certifications', stdout=out)
        
        output = out.getvalue()
        
        # Should update 3 DVDs
        self.assertIn('Successfully updated 3 DVDs!', output)
        
        # Refresh from database and check
        dvd_a = DVD.objects.get(name='Movie A')
        dvd_b = DVD.objects.get(name='Movie B')
        dvd_c = DVD.objects.get(name='Movie C')
        dvd_d = DVD.objects.get(name='Movie D')
        dvd_e = DVD.objects.get(name='Movie E')
        
        self.assertEqual(dvd_a.uk_certification, 'pg')
        self.assertEqual(dvd_b.uk_certification, '12a')
        self.assertEqual(dvd_c.uk_certification, 'u')
        self.assertEqual(dvd_d.uk_certification, 'pg')  # Should remain unchanged
        self.assertEqual(dvd_e.uk_certification, '15')  # Should remain unchanged
    
    def test_verbose_output(self):
        """Test that verbose mode shows detailed output."""
        out = StringIO()
        call_command('normalize_uk_certifications', '--verbose', stdout=out)
        
        output = out.getvalue()
        
        # Should show detailed information
        self.assertIn('Movie A', output)
        self.assertIn('✅ Updated', output)
        self.assertIn('Certification:', output)
    
    def test_already_normalized_collection(self):
        """Test behavior when all certifications are already normalized."""
        # First normalize everything
        call_command('normalize_uk_certifications')
        
        # Then run again
        out = StringIO()
        call_command('normalize_uk_certifications', '--dry-run', stdout=out)
        
        output = out.getvalue()
        self.assertIn('All UK certifications are already normalized!', output)
    
    def test_certification_stats_display(self):
        """Test that certification statistics are displayed correctly."""
        out = StringIO()
        call_command('normalize_uk_certifications', '--dry-run', stdout=out)
        
        output = out.getvalue()
        
        # Should show statistics
        self.assertIn('Current UK Certification Distribution:', output)
        self.assertIn('(no certification):', output)
    
    def test_model_save_method_normalizes(self):
        """Test that the DVD model's save method automatically normalizes certifications."""
        dvd = DVD(name='Test Movie', uk_certification='PG')
        dvd.save()
        
        # Should be automatically normalized
        self.assertEqual(dvd.uk_certification, 'pg')
        
        # Test updating existing
        dvd.uk_certification = '12A'
        dvd.save()
        
        self.assertEqual(dvd.uk_certification, '12a')


class BluRayFormTest(TestCase):
    """Test the Blu-Ray checkbox functionality in forms."""
    
    def test_dvd_form_bluray_checkbox_default_dvd(self):
        """Test that DVDForm creates DVD disk_type when checkbox is unchecked."""
        form_data = {
            'name': 'Test Movie',
            'status': 'kept',
            'media_type': 'physical',
            'overview': 'Test overview',
            'copy_number': 1,
            'is_bluray': False  # Checkbox unchecked
        }
        
        form = DVDForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        dvd = form.save()
        self.assertEqual(dvd.disk_type, 'DVD')
    
    def test_dvd_form_bluray_checkbox_creates_bluray(self):
        """Test that DVDForm creates BluRay disk_type when checkbox is checked."""
        form_data = {
            'name': 'Test BluRay Movie',
            'status': 'kept',
            'media_type': 'physical',
            'overview': 'Test BluRay overview',
            'copy_number': 1,
            'is_bluray': True  # Checkbox checked
        }
        
        form = DVDForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        dvd = form.save()
        self.assertEqual(dvd.disk_type, 'BluRay')
    
    def test_dvd_form_edit_existing_bluray(self):
        """Test that editing an existing BluRay DVD initializes checkbox correctly."""
        # Create a BluRay DVD
        dvd = DVD.objects.create(
            name="Existing BluRay Movie",
            status="kept",
            media_type="physical",
            disk_type="BluRay"
        )
        
        # Create form with the existing DVD instance
        form = DVDForm(instance=dvd)
        
        # Check that the checkbox is initialized as checked
        self.assertTrue(form.fields['is_bluray'].initial)
    
    def test_dvd_form_edit_existing_dvd(self):
        """Test that editing an existing DVD initializes checkbox as unchecked."""
        # Create a regular DVD
        dvd = DVD.objects.create(
            name="Existing DVD Movie",
            status="kept",
            media_type="physical",
            disk_type="DVD"
        )
        
        # Create form with the existing DVD instance
        form = DVDForm(instance=dvd)
        
        # Check that the checkbox is initialized as unchecked
        self.assertFalse(form.fields['is_bluray'].initial)


class BulkUploadBluRayTest(TestCase):
    """Test the bulk upload functionality with Blu-Ray checkbox."""
    
    def test_bulk_upload_with_bluray_checkbox(self):
        """Test that Blu-Ray checkbox works in bulk upload."""
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': True,  # Test BluRay checkbox
            },
            'matches': [
                {
                    'original_title': 'Test BluRay Movie',
                    'tmdb_data': {
                        'id': 12345,
                        'title': 'Test BluRay Movie',
                        'overview': 'A test movie for BluRay',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Action'}],
                        'vote_average': 7.5,
                        'imdb_id': 'tt1234567'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        session.save()

        # Submit to process view
        response = self.client.post(reverse('tracker:bulk_upload_process'))
        
        # Check that redirect occurred (successful processing)
        self.assertEqual(response.status_code, 200)
        
        # Verify DVD was created with BluRay disk_type
        dvd = DVD.objects.get(tmdb_id=12345)
        self.assertEqual(dvd.disk_type, 'BluRay')
        self.assertEqual(dvd.name, 'Test BluRay Movie')
    
    def test_bulk_upload_with_dvd_checkbox_unchecked(self):
        """Test that unchecked Blu-Ray checkbox creates DVD disk_type in bulk upload."""
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
                'default_storage_box': '',
                'default_location': '',
                'default_is_bluray': False,  # Test unchecked BluRay checkbox
            },
            'matches': [
                {
                    'original_title': 'Test DVD Movie',
                    'tmdb_data': {
                        'id': 54321,
                        'title': 'Test DVD Movie',
                        'overview': 'A test movie for DVD',
                        'release_date': '2023-01-01',
                        'runtime': 120,
                        'genres': [{'name': 'Drama'}],
                        'vote_average': 6.5,
                        'imdb_id': 'tt7654321'
                    },
                    'confirmed': True,
                    'removed': False,
                    'poster_url': None,
                    'error': None
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        session.save()

        # Submit to process view
        response = self.client.post(reverse('tracker:bulk_upload_process'))
        
        # Check that redirect occurred (successful processing)
        self.assertEqual(response.status_code, 200)
        
        # Verify DVD was created with DVD disk_type
        dvd = DVD.objects.get(tmdb_id=54321)
        self.assertEqual(dvd.disk_type, 'DVD')
        self.assertEqual(dvd.name, 'Test DVD Movie')
