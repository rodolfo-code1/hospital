# pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Recepcionista
    path('admision/', views.registrar_madre_recepcion, name='admision_madre'),
    
    # Matrona
    path('lista/', views.lista_pacientes, name='lista_pacientes'),
    path('ficha/<int:pk>/', views.ver_ficha_clinica, name='ver_ficha'),     # Ver (Bloqueado)
    path('editar/<int:pk>/', views.editar_ficha_clinica, name='editar_ficha'), # Editar (Desbloqueado)
    
    # Redirecciones de compatibilidad (opcional)
    path('registrar/', views.registrar_madre, name='registrar_madre'),
    path('buscar/', views.buscar_madre, name='buscar_madre'),
    path('completar/<int:pk>/', views.completar_madre, name='completar_madre'),
]