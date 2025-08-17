from django.urls import path
from . import views

urlpatterns = [
    path("submit/", views.submit_code, name="submit_code"),
    path("status/", views.submission_status, name="submission_status"),
]
