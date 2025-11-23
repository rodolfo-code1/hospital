# usuarios/decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def rol_requerido(*roles_permitidos):
    """
    Decorador que verifica si el usuario tiene uno de los roles permitidos.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.rol in roles_permitidos:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(
                    request, 
                    f'No tienes permisos para acceder a esta página. Se requiere rol: {", ".join(roles_permitidos)}'
                )
                return redirect('usuarios:login')
        return _wrapped_view
    return decorator

def medico_requerido(view_func):
    return rol_requerido('medico')(view_func)

def matrona_requerida(view_func):
    return rol_requerido('matrona')(view_func)

def administrativo_requerido(view_func):
    return rol_requerido('administrativo')(view_func)

def personal_clinico_requerido(view_func):
    """Decorador para personal clínico (ahora solo médico y matrona)"""
    return rol_requerido('medico', 'matrona')(view_func)

def supervisor_requerido(view_func):
    return rol_requerido('supervisor')(view_func)

def encargado_ti_requerido(view_func):
    return rol_requerido('encargado_ti')(view_func)