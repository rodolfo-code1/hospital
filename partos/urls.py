from django.urls import path
from . import views

app_name = 'partos'

urlpatterns = [
    path('registrar/', views.registrar_parto, name='registrar_parto'),
    path('mis-registros/', views.mis_registros_clinicos, name='mis_registros'),
    path('derivar-ive/', views.derivar_aborto, name='derivar_aborto'),
    path('panel-ive/', views.panel_abortos, name='panel_abortos'),
    path('resolver-ive/<int:pk>/', views.resolver_aborto, name='resolver_aborto'),
]