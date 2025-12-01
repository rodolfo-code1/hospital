from django.db import models
from pacientes.models import Madre
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class Parto(models.Model):
    TIPO_PARTO = [
        ('eutocico', 'Parto Eutócico (Normal)'),
        ('cesarea_electiva', 'Cesárea Electiva'),
        ('cesarea_urgencia', 'Cesárea Urgencia'),
        ('forceps', 'Fórceps'),
        ('vacuum', 'Vacuum'),
        ('podalica', 'Podálica'),
    ]
    
    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name='partos')
    
    # --- DATOS DEL PARTO (Planilla URNI) ---
    tipo = models.CharField(max_length=30, choices=TIPO_PARTO, verbose_name="Tipo de parto")
    fecha_hora_inicio = models.DateTimeField(verbose_name="Fecha/Hora Inicio")
    fecha_hora_termino = models.DateTimeField(verbose_name="Fecha/Hora Nacimiento", null=True, blank=True)
    
    # Edad Gestacional (Columnas E y G del Excel)
    edad_gestacional_semanas = models.IntegerField(
        verbose_name="EG (Semanas)", 
        validators=[MinValueValidator(20), MaxValueValidator(45)],
        null=True, blank=True
    )
    edad_gestacional_dias = models.IntegerField(
        verbose_name="EG (Días)", 
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        default=0
    )
    
    acompanante = models.CharField(max_length=200, verbose_name="Acompañante en Pabellón", blank=True)
    
    # Equipo Médico
    medico_responsable = models.CharField(max_length=200, verbose_name="Médico")
    matrona_responsable = models.CharField(max_length=200, verbose_name="Matrona")
    personal_apoyo = models.TextField(blank=True, verbose_name="Personal de Apoyo")
    
    # Complicaciones
    tuvo_complicaciones = models.BooleanField(default=False, verbose_name="¿Complicaciones?")
    complicaciones = models.TextField(blank=True, verbose_name="Descripción Complicaciones")
    observaciones = models.TextField(blank=True)
    
    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='partos_registrados'
    )
    
    class Meta:
        verbose_name = "Parto"
        verbose_name_plural = "Partos"
        ordering = ['-fecha_hora_inicio']
    
    def __str__(self):
        return f"Parto {self.get_tipo_display()} - {self.madre.nombre} ({self.madre.rut})"

    def tiene_registros_completos(self):
        return all([self.tipo, self.fecha_hora_termino, self.medico_responsable])