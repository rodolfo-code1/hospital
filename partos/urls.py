from django.urls import path
from . import views

app_name = 'partos'

urlpatterns = [
    path('registrar/', views.registrar_parto, name='registrar_parto'),
    path('mis-registros/', views.mis_registros_clinicos, name='mis_registros'),
]