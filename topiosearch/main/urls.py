from django.urls import path
from . import views

# URLs des pages web statiques

urlpatterns = [
    path('', views.index, name="index"),
    path('examples/', views.examples, name="examples"),
]

