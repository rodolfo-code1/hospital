# hospital/app/urls.py
from django.urls import path
from . import views

app_name = 'app'


urlpatterns = [
    path('', views.home, name='home'),
    path('notificacion/leida/<int:pk>/', views.marcar_leida, name='marcar_leida'),
    path('api/notificaciones/', views.api_notificaciones, name='api_notificaciones'),
    path('ocultar/<int:pk>/', views.ocultar_notificacion, name='ocultar_notificacion'),
]
