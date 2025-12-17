# hospital/app/apps.py
from django.apps import AppConfig

class AppConfig(AppConfig):
    """
    Configuración de la aplicación 'app' (Core/Dashboard).
    Define el campo automático por defecto para modelos y el nombre de registro.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'