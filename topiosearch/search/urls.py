from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('remote/', views.api_remote_search_term),
    path('local/', views.api_local_search_term),
]