from django.urls import path
from . import views

app_name = 'altas'

urlpatterns = [
    path('lista/', views.lista_altas, name='lista_altas'),
    path('crear/', views.crear_alta, name='crear_alta'),
    path('detalle/<int:pk>/', views.detalle_alta, name='detalle_alta'),
    path('confirmar-clinica/<int:pk>/', views.confirmar_alta_clinica, name='confirmar_alta_clinica'),
    path('confirmar-administrativa/<int:pk>/', views.confirmar_alta_administrativa, name='confirmar_alta_administrativa'),
    path('historial/', views.historial_altas, name='historial_altas'),
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('certificado/<int:pk>/', views.descargar_certificado, name='descargar_certificado'),
]