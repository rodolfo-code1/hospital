# hospital/app/models.py
from django.db import models
from django.conf import settings

class Notificacion(models.Model):
    """
    Modelo de Notificaciones del Sistema.
    
    Permite enviar alertas asincrónicas a los usuarios. Se utiliza para avisar sobre:
    - Nuevas altas por firmar (para médicos).
    - Pacientes críticos (para jefatura).
    - Trámites pendientes (para administrativos).
    
    Atributos:
        usuario: El destinatario de la notificación.
        tipo: Define la prioridad visual (Información vs Urgente/Alerta roja).
        link: URL opcional para redirigir al usuario directamente a la ficha o acción requerida.
    """
    
    TIPO_CHOICES = [
        ('info', 'Información'),        # Mensajes generales o de éxito
        ('urgente', 'URGENTE / ALERTA'), # Alertas críticas (ej: RN con Apgar bajo)
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        verbose_name="Para"
    )
    titulo = models.CharField(max_length=100)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    
    # Estado de lectura para controlar si aparece en la campana de notificaciones
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Enlace directo a la acción (ej: '/altas/confirmar/5/')
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-fecha_creacion'] # Las más nuevas primero

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"