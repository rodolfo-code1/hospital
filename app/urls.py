# app/urls.py
from django.urls import path
from . import views

app_name = 'app'  # <--- NAMESPACE AHORA ES 'app'

urlpatterns = [
    path('', views.home, name='home'),
    
    # URLs para Supervisor
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    path('supervisor/reportes/', views.supervisor_reportes, name='supervisor_reportes'),
    path('supervisor/auditoria/', views.supervisor_auditoria, name='supervisor_auditoria'),
    path('supervisor/metricas/', views.supervisor_metricas, name='supervisor_metricas'),
    
    # URLs para Reportes específicos REM A24
    path('supervisor/reportes/partos/', views.reporte_partos, name='reporte_partos'),
    path('supervisor/reportes/ive/', views.reporte_ive, name='reporte_ive'),
    path('supervisor/reportes/anticonceptivos/', views.reporte_anticonceptivos, name='reporte_anticonceptivos'),
    path('supervisor/reportes/recien-nacidos/', views.reporte_recien_nacidos, name='reporte_recien_nacidos'),
]