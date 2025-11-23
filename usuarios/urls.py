# usuarios/urls.py
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Rutas públicas
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    # Rutas de Gestión TI
    path('gestion/', views.gestion_usuarios, name='gestion_usuarios'),
    path('gestion/crear/', views.crear_usuario_interno, name='crear_usuario'),
    path('gestion/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),
]