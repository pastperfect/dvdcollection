from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.dvd_list, name='dvd_list'),
    path('stats/', views.stats, name='stats'),
    path('dvd/<int:pk>/', views.dvd_detail, name='dvd_detail'),
    path('add/', views.dvd_add, name='dvd_add'),
    path('add/tmdb/<int:tmdb_id>/', views.dvd_add_from_tmdb, name='dvd_add_from_tmdb'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('dvd/<int:pk>/edit/', views.dvd_edit, name='dvd_edit'),
    path('dvd/<int:pk>/delete/', views.dvd_delete, name='dvd_delete'),
    path('dvd/<int:pk>/fix-tmdb/', views.fix_tmdb_match, name='fix_tmdb_match'),
    path('dvd/<int:pk>/fetch-imdb/', views.fetch_imdb_id, name='fetch_imdb_id'),
    path('tartan/', views.tartan_dvds, name='tartan_dvds'),
    path('box-sets/', views.box_sets, name='box_sets'),
    path('box-sets/<str:box_set_name>/', views.box_set_detail, name='box_set_detail'),
    path('api/search/', views.search_tmdb_ajax, name='search_tmdb_ajax'),
    path('api/box-set-autocomplete/', views.box_set_autocomplete, name='box_set_autocomplete'),
    path('api/storage-box-autocomplete/', views.storage_box_autocomplete, name='storage_box_autocomplete'),
]
