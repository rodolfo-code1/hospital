# hospital/respaldos/urls.py
from django.urls import path
from . import views

app_name = "respaldos"

urlpatterns = [
    # Ruta única para gatillar la generación del backup.
    # Se accede usualmente desde el panel del Encargado TI.
    path('generar/', views.generar_respaldo, name='generar_respaldo'),
]