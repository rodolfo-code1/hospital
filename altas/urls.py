# hospital/altas/urls.py
from django.urls import path
from . import views

# Namespace para referenciar urls como 'altas:nombre_ruta'
app_name = 'altas'

urlpatterns = [
    # --- PANEL Y GESTIÓN DE RIESGO ---
    # Dashboard principal para médicos (muestra pacientes activos)
    path('panel-medico/', views.panel_medico, name='panel_medico'),
    
    # Vista concentradora de alertas (pacientes críticos)
    path('alertas/', views.alertas_clinicas, name='alertas_clinicas'),
    
    # Acción POST para cambiar el semáforo de salud (Sano / En Observación / Crítico)
    path('cambiar-salud/<str:tipo_paciente>/<int:pk>/', views.cambiar_estado_salud, name='cambiar_salud'),

    # --- FLUJO DE ALTA ---
    # Listado general de trámites (para administrativos)
    path('lista/', views.lista_altas, name='lista_altas'),
    
    # Formulario inicial de creación de alta
    path('crear/', views.crear_alta, name='crear_alta'),
    
    # Ficha de detalle del trámite (semáforos y validaciones)
    path('detalle/<int:pk>/', views.detalle_alta, name='detalle_alta'),
    
    # --- CONFIRMACIONES (FIRMAS) ---
    # Firma del médico (autorización clínica)
    path('confirmar-clinica/<int:pk>/', views.confirmar_alta_clinica, name='confirmar_alta_clinica'),
    
    # Firma administrativa (cierre de cuenta y liberación de cama)
    path('confirmar-administrativa/<int:pk>/', views.confirmar_alta_administrativa, name='confirmar_alta_administrativa'),
    
    # --- REPORTES Y UTILIDADES ---
    # Historial completo de altas cerradas
    path('historial/', views.historial_altas, name='historial_altas'),
    
    # Descarga masiva de datos en Excel
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    
    # Descarga del certificado PDF individual
    path('certificado/<int:pk>/', views.descargar_certificado, name='descargar_certificado'),
    
    # Acción para marcar una alerta clínica como revisada/resuelta
    path('alertas/revisar/<str:tipo>/<int:pk>/', views.marcar_alerta_revisada, name='marcar_alerta_revisada'),
]