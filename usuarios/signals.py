# usuarios/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import AnonymousUser
from usuarios.models import AuditoriaModificacion
from usuarios.middleware import _thread_locals
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from altas.models import Alta
from pacientes.models import Madre
import logging

logger = logging.getLogger(__name__)

# Modelos que queremos auditar
MODELOS_AUDITADOS = [Parto, Aborto, RecienNacido, Alta, Madre]


def get_current_user():
    """Obtener el usuario actual del request almacenado en thread-local"""
    try:
        request = getattr(_thread_locals, 'request', None)
        if request:
            return request.user
    except AttributeError:
        pass
    return None


@receiver(post_save)
def registrar_creacion_modificacion(sender, instance, created, **kwargs):
    """
    Señal que registra creaciones y modificaciones de modelos auditados.
    """
    # Solo auditar modelos especificados
    if sender not in MODELOS_AUDITADOS:
        return
    
    try:
        # Obtener el usuario actual
        usuario = get_current_user()
        
        # Si no hay usuario o es anónimo, no registrar
        if not usuario or isinstance(usuario, AnonymousUser):
            usuario = None
        
        # Determinar tipo de operación
        tipo_operacion = 'create' if created else 'update'
        
        # Preparar descripción
        descripcion = f"{sender.__name__} {'creado' if created else 'modificado'}"
        if hasattr(instance, '__str__'):
            descripcion += f": {str(instance)[:100]}"
        
        # Crear registro de auditoría
        AuditoriaModificacion.objects.create(
            usuario=usuario,
            tipo_operacion=tipo_operacion,
            modelo=sender.__name__,
            id_objeto=instance.pk,
            descripcion=descripcion,
            valores_nuevos={
                'id': instance.pk,
                'modelo': sender.__name__,
            }
        )
    except Exception as e:
        logger.error(f"Error registrando auditoría de modificación: {str(e)}")


@receiver(post_delete)
def registrar_eliminacion(sender, instance, **kwargs):
    """
    Señal que registra eliminaciones de modelos auditados.
    """
    # Solo auditar modelos especificados
    if sender not in MODELOS_AUDITADOS:
        return
    
    try:
        # Obtener el usuario actual
        usuario = get_current_user()
        
        # Si no hay usuario o es anónimo, no registrar
        if not usuario or isinstance(usuario, AnonymousUser):
            usuario = None
        
        # Preparar descripción
        descripcion = f"{sender.__name__} eliminado: {str(instance)[:100]}"
        
        # Crear registro de auditoría
        AuditoriaModificacion.objects.create(
            usuario=usuario,
            tipo_operacion='delete',
            modelo=sender.__name__,
            id_objeto=instance.pk if instance.pk else 0,
            descripcion=descripcion,
        )
    except Exception as e:
        logger.error(f"Error registrando auditoría de eliminación: {str(e)}")
