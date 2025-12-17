# hospital/app/urls.py
from django.urls import path
from . import views

# Namespace 'app' permite usar urls como {% url 'app:home' %}
app_name = 'app'

urlpatterns = [
    # Dashboard principal (Login required)
    path('', views.home, name='home'),
    
    # Rutas para gestión de notificaciones (Botones de acción)
    path('notificacion/leida/<int:pk>/', views.marcar_leida, name='marcar_leida'),
    path('ocultar/<int:pk>/', views.ocultar_notificacion, name='ocultar_notificacion'),
    
    # Endpoint JSON para actualizaciones automáticas (AJAX)
    path('api/notificaciones/', views.api_notificaciones, name='api_notificaciones'),
]