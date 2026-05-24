from django.urls import path

from .views import dashboard_view, health_view, imports_view, records_view, reference_data_view, sample_file_view, version_view

urlpatterns = [
    path("health", health_view, name="health"),
    path("version", version_view, name="version"),
    path("reference-data", reference_data_view, name="reference-data"),
    path("dashboard", dashboard_view, name="dashboard"),
    path("records", records_view, name="records"),
    path("imports", imports_view, name="imports"),
    path("sample-files/<str:source_type>", sample_file_view, name="sample-file"),
]
