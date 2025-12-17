# hospital/partos/urls.py
from django.urls import path
from . import views

app_name = 'partos'

urlpatterns = [
    # --- FLUJO DE MATERNIDAD ---
    # Registro de nacimiento (Matrona)
    path('registrar/', views.registrar_parto, name='registrar_parto'),
    
    # Panel de control de turno (Matrona)
    path('mis-registros/', views.mis_registros_clinicos, name='mis_registros'),
    
    # --- FLUJO DE GINECOLOGÍA / IVE ---
    # Derivación inicial (Matrona -> Médico)
    path('derivar-ive/', views.derivar_aborto, name='derivar_aborto'),
    
    # Lista de espera de casos (Médico)
    path('panel-ive/', views.panel_abortos, name='panel_abortos'),
    
    # Resolución del caso (Médico)
    path('resolver-ive/<int:pk>/', views.resolver_aborto, name='resolver_aborto'),
]