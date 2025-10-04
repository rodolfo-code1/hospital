# recien_nacidos/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from partos.models import Parto
import uuid

class RecienNacido(models.Model):
    """
    Modelo de Recién Nacido - Módulo 3 simplificado
    Registra la información del recién nacido vinculado a un parto.
    """
    
    CONDICION_NACIMIENTO = [
        ('vivo', 'Vivo'),
        ('mortinato', 'Mortinato'),
    ]
    
    SEXO = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('I', 'Indeterminado'),
    ]
    
    # Identificación única
    codigo_unico = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        verbose_name="Código único",
        help_text="Identificador único del RN"
    )
    
    # Relación con el parto
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='recien_nacidos',
        verbose_name="Parto"
    )
    
    # Datos básicos
    nombre = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nombre (si ya fue asignado)"
    )
    sexo = models.CharField(
        max_length=1,
        choices=SEXO,
        verbose_name="Sexo"
    )
    
    # Datos clínicos
    peso = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.5), MaxValueValidator(8.0)],
        verbose_name="Peso (kg)",
        help_text="Peso en kilogramos"
    )
    talla = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(30.0), MaxValueValidator(70.0)],
        verbose_name="Talla (cm)",
        help_text="Talla en centímetros"
    )
    
    # APGAR (Escala de valoración del recién nacido)
    apgar_1_min = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="APGAR al minuto 1"
    )
    apgar_5_min = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="APGAR a los 5 minutos"
    )
    apgar_10_min = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="APGAR a los 10 minutos"
    )
    
    # Condición
    condicion_nacimiento = models.CharField(
        max_length=20,
        choices=CONDICION_NACIMIENTO,
        default='vivo',
        verbose_name="Condición al nacer"
    )
    
    # Derivaciones
    requiere_derivacion = models.BooleanField(
        default=False,
        verbose_name="¿Requiere derivación?"
    )
    servicio_derivacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Servicio de derivación",
        help_text="Ej: UCI Neonatal, Neonatología"
    )
    
    # Controles y procedimientos
    vacunas_aplicadas = models.TextField(
        blank=True,
        verbose_name="Vacunas aplicadas"
    )
    examenes_realizados = models.TextField(
        blank=True,
        verbose_name="Exámenes realizados"
    )
    
    # Observaciones
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones clínicas"
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
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"
        ordering = ['-fecha_registro']
    
    def save(self, *args, **kwargs):
        """Genera código único automáticamente si no existe"""
        if not self.codigo_unico:
            self.codigo_unico = f"RN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        nombre = self.nombre if self.nombre else "Sin nombre"
        return f"{nombre} ({self.codigo_unico}) - Madre: {self.parto.madre.nombre}"
    
    def tiene_registros_completos(self):
        """Valida si el RN tiene todos los datos necesarios"""
        return all([
            self.codigo_unico,
            self.sexo,
            self.peso,
            self.talla,
            self.apgar_1_min is not None,
            self.apgar_5_min is not None,
            self.condicion_nacimiento
        ])
    
    def tiene_apgar_critico(self):
        """Detecta si el APGAR es crítico (menor a 7)"""
        return self.apgar_1_min < 7 or self.apgar_5_min < 7
    
    def peso_adecuado(self):
        """Verifica si el peso es adecuado (entre 2.5 y 4.0 kg)"""
        return 2.5 <= float(self.peso) <= 4.0