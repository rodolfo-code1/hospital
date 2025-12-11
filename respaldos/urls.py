from django.urls import path
from . import views

app_name = "respaldos"

urlpatterns = [
    path('generar/', views.generar_respaldo, name='generar_respaldo'),
]
