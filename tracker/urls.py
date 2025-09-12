from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.home, name='home'),
    path('collection/', views.dvd_list, name='dvd_list'),
    path('stats/', views.stats, name='stats'),
    path('dvd/<int:pk>/', views.dvd_detail, name='dvd_detail'),
    path('add/', views.dvd_add, name='dvd_add'),
    path('add/tmdb/<int:tmdb_id>/', views.dvd_add_from_tmdb, name='dvd_add_from_tmdb'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('bulk-upload/preview/', views.bulk_upload_preview, name='bulk_upload_preview'),
    path('bulk-upload/process/', views.bulk_upload_process, name='bulk_upload_process'),
    path('bulk-edit/', views.bulk_edit, name='bulk_edit'),
    path('dvd/<int:pk>/edit/', views.dvd_edit, name='dvd_edit'),
    path('dvd/<int:pk>/delete/', views.dvd_delete, name='dvd_delete'),
    path('dvd/<int:pk>/fix-tmdb/', views.fix_tmdb_match, name='fix_tmdb_match'),
    path('dvd/<int:pk>/change-poster/', views.dvd_change_poster, name='dvd_change_poster'),
    path('dvd/<int:pk>/fetch-imdb/', views.fetch_imdb_id, name='fetch_imdb_id'),
    path('box-sets/<str:box_set_name>/', views.box_set_detail, name='box_set_detail'),
    path('api/search/', views.search_tmdb_ajax, name='search_tmdb_ajax'),
    path('api/box-set-autocomplete/', views.box_set_autocomplete, name='box_set_autocomplete'),
    path('api/storage-box-autocomplete/', views.storage_box_autocomplete, name='storage_box_autocomplete'),
    path('api/check-location/', views.check_location_availability, name='check_location_availability'),
    path('api/bulk-update-dvd/', views.bulk_update_dvd, name='bulk_update_dvd'),
    path('api/delete-dvd/', views.delete_dvd_api, name='delete_dvd_api'),
    path('api/refresh-all-tmdb/', views.refresh_all_tmdb, name='refresh_all_tmdb'),
    path('api/refresh-progress/', views.refresh_progress, name='refresh_progress'),
    path('system-admin/', views.admin_settings, name='admin_settings'),
    path('system-admin/export-non-kept/', views.export_non_kept_dvds, name='export_non_kept_dvds'),
    path('system-admin/export-complete/', views.export_complete_collection, name='export_complete_collection'),
]
