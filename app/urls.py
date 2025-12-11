# hospital/app/urls.py
from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.home, name='home'),
    # Agregar esta línea:
    path('notificacion/leida/<int:pk>/', views.marcar_leida, name='marcar_leida'),
]
