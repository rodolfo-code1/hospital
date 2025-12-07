# pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # Registrar (Solo Recepción)
    path('admision/', views.registrar_madre_recepcion, name='admision_madre'),
    
    # Historial (NUEVO)
    path('historial/', views.historial_recepcion, name='historial_recepcion'),

    # Gestión Clínica (Matrona)
    path('lista/', views.lista_pacientes, name='lista_pacientes'),
    path('registrar/', views.registrar_madre, name='registrar_madre'),
    path('buscar/', views.buscar_madre, name='buscar_madre'),
    path('completar/<int:pk>/', views.completar_madre, name='completar_madre'),
    # RUTAS ADMINISTRATIVAS (QR)
    path('admin/buscar/', views.admin_buscar_paciente, name='admin_buscar_paciente'),
    path('admin/brazalete/<int:pk>/', views.ver_brazalete, name='ver_brazalete'),
    path('admin/qr-img/<int:pk>/', views.generar_qr_imagen, name='generar_qr_imagen'),
    path('ficha-digital/<int:pk>/', views.ficha_qr_madre, name='ficha_qr_madre'),
]