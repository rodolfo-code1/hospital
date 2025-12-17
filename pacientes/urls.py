# hospital/pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # --- FLUJO DE RECEPCIÓN / ADMISIÓN ---
    # Formulario de ingreso con semáforo de riesgo
    path('admision/', views.registrar_madre_recepcion, name='admision_madre'),
    # Historial completo de ingresos (para Recepcionistas)
    path('historial/', views.historial_recepcion, name='historial_recepcion'),
    
    # --- FLUJO CLÍNICO (MATRONA) ---
    # Lista de trabajo filtrada (pacientes pendientes)
    path('lista/', views.lista_pacientes, name='lista_pacientes'),
    # Ver detalles de la ficha (solo lectura)
    path('ficha/<int:pk>/', views.ver_ficha_clinica, name='ver_ficha'),
    # Editar datos clínicos o actualizar riesgo
    path('editar/<int:pk>/', views.editar_ficha_clinica, name='editar_ficha'),
    
    # --- RUTAS DE COMPATIBILIDAD (Redirecciones) ---
    path('registrar/', views.registrar_madre, name='registrar_madre'),
    path('buscar/', views.buscar_madre, name='buscar_madre'),
    path('completar/<int:pk>/', views.completar_madre, name='completar_madre'),
    
    # --- RUTAS ADMINISTRATIVAS (BRAZALETES Y QR) ---
    # Buscador específico para generar identificadores
    path('admin/buscar/', views.admin_buscar_paciente, name='admin_buscar_paciente'),
    # Vista previa del brazalete de impresión
    path('admin/brazalete/<int:pk>/', views.ver_brazalete, name='ver_brazalete'),
    # Generador de imagen PNG del código QR
    path('admin/qr-img/<int:pk>/', views.generar_qr_imagen, name='generar_qr_imagen'),
    
    # --- FICHA DIGITAL MÓVIL (Destino del QR) ---
    path('ficha-digital/<int:pk>/', views.ficha_qr_madre, name='ficha_qr_madre'),
    
    # --- AUDITORÍA PERSONAL ---
    # Historial de pacientes atendidos por el usuario logueado
    path('mi-historial/', views.historial_trabajo_matrona, name='mi_historial'),
]