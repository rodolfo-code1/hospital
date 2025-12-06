# usuarios/middleware.py
from threading import local

# Thread-local storage para almacenar el usuario actual
_thread_locals = local()


def get_current_user():
    """Obtener el usuario actual del contexto"""
    return getattr(_thread_locals, 'request', None)


class CurrentUserMiddleware:
    """
    Middleware que almacena el usuario actual en thread-local storage
    para que sea accesible desde signals y otras partes del código.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        _thread_locals.request = request
        
        response = self.get_response(request)
        
        # Limpiar después de procesar
        _thread_locals.request = None
        
        return response
