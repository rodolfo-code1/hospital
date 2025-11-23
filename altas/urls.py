# altas/urls.py
from django.urls import path
from . import views

app_name = 'altas'

urlpatterns = [
    
    # La lista de gestión se mueve a su propia ruta
    path('lista/', views.lista_altas, name='lista_altas'),
    
    # Registros (Madre, Parto, RN)
    path('registrar/madre/', views.registrar_madre, name='registrar_madre'),
    path('registrar/parto/', views.registrar_parto, name='registrar_parto'),
    path('registrar/recien-nacido/', views.registrar_recien_nacido, name='registrar_recien_nacido'),
    
    # Proceso de Alta (CRUD)
    path('crear/', views.crear_alta, name='crear_alta'),
    path('detalle/<int:pk>/', views.detalle_alta, name='detalle_alta'),
    
    # Confirmaciones de Alta
    path('confirmar-clinica/<int:pk>/', views.confirmar_alta_clinica, name='confirmar_alta_clinica'),
    path('confirmar-administrativa/<int:pk>/', views.confirmar_alta_administrativa, name='confirmar_alta_administrativa'),
    
    # Historial y reportes
    path('historial/', views.historial_altas, name='historial_altas'),
    
    # Exportación y Certificados
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('certificado/<int:pk>/', views.descargar_certificado, name='descargar_certificado'),
]