# hospital/recien_nacidos/urls.py
from django.urls import path
from . import views

app_name = 'recien_nacidos'

urlpatterns = [
    # --- FLUJO CLÍNICO ---
    # Formulario de registro inicial
    path('registrar/', views.registrar_recien_nacido, name='registrar_rn'),
    
    # --- FLUJO ADMINISTRATIVO (IDENTIFICACIÓN) ---
    # Buscador de RNs para generar brazaletes
    path('admin/buscar/', views.admin_buscar_rn, name='admin_buscar_rn'),
    # Vista previa del brazalete
    path('admin/brazalete/<int:pk>/', views.ver_brazalete_rn, name='ver_brazalete_rn'),
    # Generador de imagen QR
    path('admin/qr-img/<int:pk>/', views.generar_qr_rn, name='generar_qr_rn'),
    
    # --- FICHA DIGITAL ---
    # URL de destino al escanear el brazalete
    path('ficha-digital/<int:pk>/', views.ficha_qr, name='ficha_qr'),
]