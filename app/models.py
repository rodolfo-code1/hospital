from django.db import models
from django.conf import settings

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('info', 'Información'),
        ('urgente', 'URGENTE / ALERTA'),
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
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Opcional: Link para ir directo a la ficha
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.titulo}"