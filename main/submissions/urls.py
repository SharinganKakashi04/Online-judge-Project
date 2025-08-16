from django.urls import path
from . import views

app_name = 'submissions'
urlpatterns = [
    path('', views.submissions_list, name='list'),
    path('<int:problem_id>/run/',views.run_code_ajax,name = 'run_code_ajax'),
    path('submit/<int:problem_id>/', views.submit_code, name='submit_code'),
]
