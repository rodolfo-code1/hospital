from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
import json

class RegistroAuditoria(models.Model):
    """
    Modelo para registrar todas las modificaciones realizadas en el sistema
    """
    ACCION_CHOICES = [
        ('create', 'Crear'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('view', 'Ver'),
        ('login', 'Iniciar sesión'),
        ('logout', 'Cerrar sesión'),
    ]
    
    # Información de la acción
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_auditoria',
        verbose_name="Usuario"
    )
    accion = models.CharField(
        max_length=10,
        choices=ACCION_CHOICES,
        verbose_name="Acción"
    )
    
    # Información del objeto modificado
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Tipo de objeto"
    )
    object_id = models.PositiveIntegerField(
        verbose_name="ID del objeto"
    )
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Detalles del cambio
    valores_anteriores = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Valores anteriores"
    )
    valores_nuevos = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Valores nuevos"
    )
    campos_modificados = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Campos modificados"
    )
    
    # Metadata
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name="Dirección IP"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        verbose_name="User Agent"
    )
    
    # Información adicional
    descripcion = models.CharField(
        max_length=500,
        null=True, 
        blank=True,
        verbose_name="Descripción"
    )
    
    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['usuario', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.usuario} - {self.get_accion_display()} - {self.content_type} ({self.object_id}) - {self.timestamp}"
    
    def get_valores_anteriores_display(self):
        """Retorna una versión formateada de los valores anteriores"""
        if not self.valores_anteriores:
            return "Sin datos"
        
        try:
            return json.dumps(self.valores_anteriores, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(self.valores_anteriores)
    
    def get_valores_nuevos_display(self):
        """Retorna una versión formateada de los valores nuevos"""
        if not self.valores_nuevos:
            return "Sin datos"
        
        try:
            return json.dumps(self.valores_nuevos, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(self.valores_nuevos)

class ConfiguracionAuditoria(models.Model):
    """
    Configuración del sistema de auditoría
    """
    modelo_auditado = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name="Modelo a auditar"
    )
    registrar_creacion = models.BooleanField(
        default=True,
        verbose_name="Registrar creación"
    )
    registrar_actualizacion = models.BooleanField(
        default=True,
        verbose_name="Registrar actualización"
    )
    registrar_eliminacion = models.BooleanField(
        default=True,
        verbose_name="Registrar eliminación"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
    class Meta:
        verbose_name = "Configuración de Auditoría"
        verbose_name_plural = "Configuraciones de Auditoría"
        unique_together = ['modelo_auditado']
    
    def __str__(self):
        return f"Auditoría para {self.modelo_auditado}"