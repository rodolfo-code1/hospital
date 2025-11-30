from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'
    verbose_name = 'Sistema de Auditoría'
    
    def ready(self):
        """Importar señales al iniciar la aplicación"""
        try:
            from . import signals
        except ImportError:
            pass