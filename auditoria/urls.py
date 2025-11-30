# auditoria/urls.py
from django.urls import path
from . import views

app_name = 'auditoria'

urlpatterns = [
    path('', views.lista_auditoria, name='lista_auditoria'),
    path('<int:pk>/', views.detalle_auditoria, name='detalle_auditoria'),
    path('estadisticas/', views.estadisticas_auditoria, name='estadisticas_auditoria'),
]