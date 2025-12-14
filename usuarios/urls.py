# usuarios/urls.py
from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Rutas públicas
    path('registro/', views.registro_view, name='registro'),
    path('login/', views.login_view, name='login'),
    
    # Activación desde correo
    path('activar/<uidb64>/<token>/', views.activar_usuario, name='activar_usuario'),
    path('crear-password/', views.crear_password_activacion, name='crear_password_activacion'),
    
    # 2FA
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    
    # Restablecer contraseña
    path('reset/', views.solicitar_reset_pw, name='solicitar_reset_pw'),
    path('reset/<uidb64>/<token>/', views.reset_password_confirm, name='reset_pw_confirm'),
    
    #Rutas usuarios
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.perfil_view, name='perfil'),
    
    # Rutas de Gestión TI
    path('gestion/', views.gestion_usuarios, name='gestion_usuarios'),
    path('gestion/obtener-usuarios/', views.obtener_usuarios, name='obtener_usuarios'),
    path('gestion/crear/', views.crear_usuario_interno, name='crear_usuario'),
    path('gestion/editar/<int:pk>/', views.editar_usuario, name='editar_usuario'),   
]