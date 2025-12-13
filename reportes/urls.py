# reportes/urls.py
# Rutas para reportes y exportaciones REM
from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    # Dashboard principal (route removed; view redirects to home)
    
    # Reportes REM por sección
    path('seccion-a/', views.reporte_seccion_a, name='seccion_a'),
    path('seccion-b/', views.reporte_seccion_b, name='seccion_b'),
    path('seccion-c/', views.reporte_seccion_c, name='seccion_c'),
    path('seccion-d/', views.reporte_seccion_d, name='seccion_d'),
    
    # Descargas Excel por sección
    path('descargar-seccion-a/', views.descargar_excel_seccion_a, name='descargar_seccion_a'),
    path('descargar-seccion-b/', views.descargar_excel_seccion_b, name='descargar_seccion_b'),
    path('descargar-seccion-c/', views.descargar_excel_seccion_c, name='descargar_seccion_c'),
    path('descargar-seccion-d/', views.descargar_excel_seccion_d, name='descargar_seccion_d'),
    path('descargar-export-madres/', views.descargar_export_madres, name='descargar_export_madres'),
    
    # Descargas PDF por sección
    path('descargar-pdf-seccion-a/', views.descargar_pdf_seccion_a, name='descargar_pdf_seccion_a'),
    path('descargar-pdf-seccion-b/', views.descargar_pdf_seccion_b, name='descargar_pdf_seccion_b'),
    path('descargar-pdf-seccion-c/', views.descargar_pdf_seccion_c, name='descargar_pdf_seccion_c'),
    path('descargar-pdf-seccion-d/', views.descargar_pdf_seccion_d, name='descargar_pdf_seccion_d'),
    path('descargar-pdf-export-madres/', views.descargar_pdf_export_madres, name='descargar_pdf_export_madres'),
    
    # Métricas
    path('metricas/', views.metricas_generales, name='metricas'),
    
    # Auditoría
    path('auditoria/', views.auditoria_view, name='auditoria'),
]