import json
from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from .models import RegistroAuditoria

class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware para registrar automáticamente las acciones en el sistema
    """
    
    def process_request(self, request):
        """Captura requests para auditoría"""
        if request.user.is_authenticated:
            # Registrar visualización de páginas importantes
            if self.es_pagina_importante(request.path):
                self.registrar_accion(
                    request=request,
                    accion='view',
                    content_type=None,
                    object_id=None,
                    descripcion=f"Visualización de página: {request.path}"
                )
    
    def process_response(self, request, response):
        """Captura responses para auditoría"""
        if request.user.is_authenticated and response.status_code in [200, 201, 204]:
            # Determinar acción basada en el método HTTP
            if request.method == 'POST':
                accion = 'create'
                descripcion = f"Creación vía {request.path}"
            elif request.method in ['PUT', 'PATCH']:
                accion = 'update'
                descripcion = f"Actualización vía {request.path}"
            elif request.method == 'DELETE':
                accion = 'delete'
                descripcion = f"Eliminación vía {request.path}"
            else:
                return response
            
            # Solo registrar acciones que afecten datos (no CSRF, no AJAX)
            if not self.es_request_excluido(request):
                self.registrar_accion(
                    request=request,
                    accion=accion,
                    content_type=None,
                    object_id=None,
                    descripcion=descripcion
                )
        
        return response
    
    def es_pagina_importante(self, path):
        """Determina si una página es importante para auditar"""
        paginas_importantes = [
            '/pacientes/',
            '/partos/',
            '/recien-nacidos/',
            '/altas/',
            '/usuarios/',
            '/admin/',
        ]
        return any(path.startswith(p) for p in paginas_importantes)
    
    def es_request_excluido(self, request):
        """Determina si un request debe ser excluido de la auditoría"""
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        if 'csrf' in request.path.lower():
            return True
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return True
        
        return False
    
    def registrar_accion(self, request, accion, content_type, object_id, descripcion):
        """Registra una acción en la auditoría"""
        try:
            registro = RegistroAuditoria(
                usuario=request.user,
                accion=accion,
                content_type=content_type,
                object_id=object_id,
                descripcion=descripcion,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            registro.save()
        except Exception as e:
            # Log del error pero no interrumpir la aplicación
            print(f"Error en auditoría: {e}")
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip