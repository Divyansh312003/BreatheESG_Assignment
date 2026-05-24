from django.urls import path

from .views import review_record_view

urlpatterns = [
    path("records/<int:record_id>/review", review_record_view, name="review-record"),
]
