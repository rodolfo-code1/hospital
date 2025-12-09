from django.urls import path
from . import views

app_name = 'recien_nacidos'

urlpatterns = [
    path('registrar/', views.registrar_recien_nacido, name='registrar_rn'),
    # RUTAS QR
    path('admin/buscar/', views.admin_buscar_rn, name='admin_buscar_rn'),
    path('admin/brazalete/<int:pk>/', views.ver_brazalete_rn, name='ver_brazalete_rn'),
    path('admin/qr-img/<int:pk>/', views.generar_qr_rn, name='generar_qr_rn'),
    path('ficha-digital/<int:pk>/', views.ficha_qr, name='ficha_qr'),
]
