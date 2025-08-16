from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),  
    path('', views.landing_page, name='landing'),
    path('people/', include('people.urls')),
    path('problems/', include('problems.urls')),
    path('submissions/', include('submissions.urls')),
]
    