from django.urls import path
from . import views

app_name = 'recien_nacidos'

urlpatterns = [
    path('registrar/', views.registrar_recien_nacido, name='registrar_rn'),
]