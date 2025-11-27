# partos/urls.py
from django.urls import path
from . import views

app_name = 'partos'

urlpatterns = [
    path('mis-registros/', views.mis_registros_clinicos, name='mis_registros'),
]