# pacientes/urls.py
from django.urls import path
from . import views

app_name = 'pacientes'

urlpatterns = [
    # --- FLUJO DE RECEPCIÓN ---
    path('admision/', views.registrar_madre_recepcion, name='admision_madre'),
    
    # --- FLUJO CLÍNICO (MATRONA) ---
    path('lista/', views.lista_pacientes, name='lista_pacientes'),
    
    path('ficha/<int:pk>/', views.ver_ficha_clinica, name='ver_ficha'),     # Ver (Solo lectura)
    path('editar/<int:pk>/', views.editar_ficha_clinica, name='editar_ficha'), # Editar (Modificar)
    
    # --- RUTAS DE COMPATIBILIDAD (Redirecciones) ---
    path('registrar/', views.registrar_madre, name='registrar_madre'),
    path('buscar/', views.buscar_madre, name='buscar_madre'),
    path('completar/<int:pk>/', views.completar_madre, name='completar_madre'),
    
    # --- RUTAS ADMINISTRATIVAS (QR y Brazaletes) ---
    path('admin/buscar/', views.admin_buscar_paciente, name='admin_buscar_paciente'),
    path('admin/brazalete/<int:pk>/', views.ver_brazalete, name='ver_brazalete'),
    path('admin/qr-img/<int:pk>/', views.generar_qr_imagen, name='generar_qr_imagen'),
    
    # --- FICHA DIGITAL (QR) ---
    path('ficha-digital/<int:pk>/', views.ficha_qr_madre, name='ficha_qr_madre'),
]