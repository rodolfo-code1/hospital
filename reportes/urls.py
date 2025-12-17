# hospital/reportes/urls.py
from django.urls import path
from . import views

# Namespace para referenciar urls como 'reportes:seccion_a'
app_name = 'reportes'

urlpatterns = [
    # ==========================================
    # VISUALIZACIÓN WEB (DASHBOARDS HTML)
    # ==========================================
    # Estas vistas muestran las tablas estadísticas en pantalla con filtros de fecha.
    # Se corresponden con las secciones del REM (Registro Estadístico Mensual).
    path('seccion-a/', views.reporte_seccion_a, name='seccion_a'), # Partos y datos generales
    path('seccion-b/', views.reporte_seccion_b, name='seccion_b'), # Ginecología / Abortos
    path('seccion-c/', views.reporte_seccion_c, name='seccion_c'), # Anticoncepción al alta
    path('seccion-d/', views.reporte_seccion_d, name='seccion_d'), # Neonatología / Recién Nacidos
    
    # ==========================================
    # EXPORTACIÓN DE DATOS (EXCEL .xlsx)
    # ==========================================
    # Endpoints que generan y descargan archivos para trabajo administrativo.
    
    # Descargas individuales por sección
    path('descargar-seccion-a/', views.descargar_excel_seccion_a, name='descargar_seccion_a'),
    path('descargar-seccion-b/', views.descargar_excel_seccion_b, name='descargar_seccion_b'),
    path('descargar-seccion-c/', views.descargar_excel_seccion_c, name='descargar_seccion_c'),
    path('descargar-seccion-d/', views.descargar_excel_seccion_d, name='descargar_seccion_d'),
    
    # "Sábana de Datos": Reporte maestro con el detalle de cada paciente (Madre-Hijo)
    path('descargar-export-madres/', views.descargar_export_madres, name='descargar_export_madres'),
    
    # ==========================================
    # DOCUMENTOS OFICIALES (PDF)
    # ==========================================
    # Generación de documentos estáticos listos para imprimir o archivar.
    
    # Reportes individuales
    path('descargar-pdf-seccion-a/', views.descargar_pdf_seccion_a, name='descargar_pdf_seccion_a'),
    path('descargar-pdf-seccion-b/', views.descargar_pdf_seccion_b, name='descargar_pdf_seccion_b'),
    path('descargar-pdf-seccion-c/', views.descargar_pdf_seccion_c, name='descargar_pdf_seccion_c'),
    path('descargar-pdf-seccion-d/', views.descargar_pdf_seccion_d, name='descargar_pdf_seccion_d'),
    
    # Libro Maestro en PDF (Todas las secciones concatenadas)
    path('descargar-pdf-export-madres/', views.descargar_pdf_export_madres, name='descargar_pdf_export_madres'),
    
    # ==========================================
    # HERRAMIENTAS DE GESTIÓN (JSON / AUDITORÍA)
    # ==========================================
    # API JSON para alimentar los gráficos del dashboard principal (Chart.js)
    path('metricas/', views.metricas_generales, name='metricas'),
    
    # Vista de logs de seguridad (quién entró, quién modificó qué)
    path('auditoria/', views.auditoria_view, name='auditoria'),
]