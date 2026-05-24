from django.urls import path

from .views import sap_import_view, travel_sync_view, utility_import_view

urlpatterns = [
    path("imports/sap", sap_import_view, name="sap-import"),
    path("imports/utility", utility_import_view, name="utility-import"),
    path("imports/travel-sync", travel_sync_view, name="travel-sync"),
]
