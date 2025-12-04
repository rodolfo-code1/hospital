# reportes/urls.py
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
    
    # Métricas
    path('metricas/', views.metricas_generales, name='metricas'),
    
    # Auditoría
    path('auditoria/', views.auditoria_view, name='auditoria'),
]