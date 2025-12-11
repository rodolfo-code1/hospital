"""
URL configuration for trazabilidad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# trazabilidad/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('usuarios/', include('usuarios.urls')),
    path('pacientes/', include('pacientes.urls')),
    path('partos/', include('partos.urls')),
    path('recien-nacidos/', include('recien_nacidos.urls')),
    path('reportes/', include('reportes.urls')),
    path('altas/', include('altas.urls')),
    path('respaldos/', include('respaldos.urls')),

 # LA RAÍZ AHORA APUNTA A 'app'
    path('', include('app.urls')), 
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)