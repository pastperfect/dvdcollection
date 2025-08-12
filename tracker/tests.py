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
        self.assertEqual(self.dvd.get_status_display_class(), "secondary")


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
