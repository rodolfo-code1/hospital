
# altas/urls.py
from django.urls import path
from . import views

app_name = 'altas'

urlpatterns = [
    # Página principal - Lista de altas
    path('', views.lista_altas, name='lista_altas'),
    
    # CRUD de altas
    path('crear/', views.crear_alta, name='crear_alta'),
    path('detalle/<int:pk>/', views.detalle_alta, name='detalle_alta'),
    
    # Confirmaciones
    path('confirmar-clinica/<int:pk>/', views.confirmar_alta_clinica, name='confirmar_alta_clinica'),
    path('confirmar-administrativa/<int:pk>/', views.confirmar_alta_administrativa, name='confirmar_alta_administrativa'),
    
    # Historial y reportes
    path('historial/', views.historial_altas, name='historial_altas'),
    
    # Exportación
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('certificado/<int:pk>/', views.descargar_certificado, name='descargar_certificado'),
]