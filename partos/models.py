# partos/models.py
from django.db import models
from pacientes.models import Madre

class Parto(models.Model):
    """
    Modelo de Parto - Módulo 2 simplificado
    Registra el proceso del parto asociado a una madre.
    """
    
    TIPO_PARTO = [
        ('natural', 'Natural'),
        ('cesarea', 'Cesárea'),
        ('instrumental', 'Instrumental'),
    ]
    
    madre = models.ForeignKey(
        Madre,
        on_delete=models.CASCADE,
        related_name='partos',
        verbose_name="Madre"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_PARTO,
        verbose_name="Tipo de parto"
    )
    fecha_hora_inicio = models.DateTimeField(
        verbose_name="Fecha y hora de inicio"
    )
    fecha_hora_termino = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y hora de término"
    )
    
    # Complicaciones
    tuvo_complicaciones = models.BooleanField(
        default=False,
        verbose_name="¿Tuvo complicaciones?"
    )
    complicaciones = models.TextField(
        blank=True,
        verbose_name="Descripción de complicaciones",
        help_text="Ej: hemorragia, sufrimiento fetal"
    )
    
    # Personal clínico
    medico_responsable = models.CharField(
        max_length=200,
        verbose_name="Médico responsable"
    )
    matrona_responsable = models.CharField(
        max_length=200,
        verbose_name="Matrona responsable"
    )
    personal_apoyo = models.TextField(
        blank=True,
        verbose_name="Personal de apoyo",
        help_text="Enfermeros y otros profesionales"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones generales"
    )
    
    # Auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Parto"
        verbose_name_plural = "Partos"
        ordering = ['-fecha_hora_inicio']
    
    def __str__(self):
        return f"Parto {self.get_tipo_display()} - {self.madre.nombre} ({self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')})"
    
    def tiene_registros_completos(self):
        """Valida si el parto tiene todos los datos necesarios"""
        return all([
            self.tipo,
            self.fecha_hora_inicio,
            self.fecha_hora_termino,
            self.medico_responsable,
            self.matrona_responsable
        ])
    
    def duracion_horas(self):
        """Calcula la duración del parto en horas"""
        if self.fecha_hora_inicio and self.fecha_hora_termino:
            delta = self.fecha_hora_termino - self.fecha_hora_inicio
            return round(delta.total_seconds() / 3600, 2)
        return None