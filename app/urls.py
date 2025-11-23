# app/urls.py
from django.urls import path
from . import views

app_name = 'app'  # <--- NAMESPACE AHORA ES 'app'

urlpatterns = [
    path('', views.home, name='home'),
]