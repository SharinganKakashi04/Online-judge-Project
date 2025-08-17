# judge/urls.py
from django.urls import path
from . import views
urlpatterns = [
    path("problems/<slug:slug>/submit/", views.submit_code, name="submit_code"),
    path("submissions/<int:sid>/", views.get_submission, name="get_submission"),
]
