# pacientes/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Madre(models.Model):
    """
    Modelo de Madre (Paciente) - Módulo 1 simplificado
    Representa a las madres ingresadas al área de obstetricia.
    """
    
    rut = models.CharField(
        max_length=12,
        unique=True,
        verbose_name="RUT",
        help_text="RUT de la madre (ej: 12345678-9)"
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre completo"
    )
    edad = models.IntegerField(
        validators=[MinValueValidator(12), MaxValueValidator(60)],
        verbose_name="Edad"
    )
    direccion = models.CharField(
        max_length=300,
        verbose_name="Dirección"
    )
    telefono = models.CharField(
        max_length=15,
        verbose_name="Teléfono"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Correo electrónico"
    )
    
    # Antecedentes clínicos básicos
    controles_prenatales = models.IntegerField(
        default=0,
        verbose_name="Número de controles prenatales"
    )
    embarazos_anteriores = models.IntegerField(
        default=0,
        verbose_name="Embarazos anteriores"
    )
    patologias = models.TextField(
        blank=True,
        verbose_name="Patologías",
        help_text="Ej: hipertensión, diabetes gestacional"
    )
    
    # Campos de auditoría
    fecha_ingreso = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de ingreso"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    class Meta:
        verbose_name = "Madre"
        verbose_name_plural = "Madres"
        ordering = ['-fecha_ingreso']
    
    def __str__(self):
        return f"{self.nombre} ({self.rut})"
    
    def tiene_registros_completos(self):
        """Valida si la madre tiene todos los datos básicos necesarios"""
        return all([
            self.nombre,
            self.rut,
            self.edad,
            self.direccion,
            self.telefono,
            self.controles_prenatales > 0
        ])