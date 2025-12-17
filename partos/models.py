# hospital/partos/models.py
from django.db import models
from pacientes.models import Madre
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords

class Parto(models.Model):
    """
    Modelo de Evento de Parto (Módulo 2).
    
    Registra los detalles clínicos del nacimiento. Es el punto central que vincula
    a una Madre con uno o más Recién Nacidos.
    
    Validaciones:
    - Edad Gestacional: Rango biológico válido (20-45 semanas).
    - Tipos de Parto: Estandarizados para reportes REM.
    """
    
    # Opciones estandarizadas para estadísticas del MINSAL
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
    
    # Edad Gestacional: Validación crítica para detectar prematuros
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
    
    # --- EQUIPO MÉDICO ---
    # Se guardan como texto libre o selectores para flexibilidad en reportes
    medico_responsable = models.CharField(max_length=200, verbose_name="Médico")
    matrona_responsable = models.CharField(max_length=200, verbose_name="Matrona")
    personal_apoyo = models.TextField(blank=True, verbose_name="Personal de Apoyo")
    
    # --- GESTIÓN DE RIESGO ---
    tuvo_complicaciones = models.BooleanField(default=False, verbose_name="¿Complicaciones?")
    complicaciones = models.TextField(blank=True, verbose_name="Descripción Complicaciones")
    observaciones = models.TextField(blank=True)
    
    # Semáforo para que el médico revise casos complicados antes del alta
    alerta_revisada = models.BooleanField(default=False, verbose_name="Alerta Revisada por Médico")

    # --- AUDITORÍA ---
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='partos_registrados'
    )

    # Historial de cambios
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Parto"
        verbose_name_plural = "Partos"
        ordering = ['-fecha_hora_inicio']
    
    def __str__(self):
        return f"Parto {self.get_tipo_display()} - {self.madre.nombre} ({self.madre.rut})"

    def tiene_registros_completos(self):
        """Verifica campos mínimos para cerrar el proceso."""
        return all([self.tipo, self.fecha_hora_termino, self.medico_responsable])


class Aborto(models.Model):
    """
    Modelo de Gestión de Interrupción del Embarazo / Aborto.
    
    Maneja tanto abortos espontáneos como casos bajo la Ley IVE (21.030).
    Tiene un flujo de estados propio: Derivado -> Confirmado/Descartado.
    """
    TIPO_ABORTO = [
        ('espontaneo', 'Espontáneo / Incompleto'),
        ('retenido', 'Huevo / Retenido'),
        ('ive', 'IVE (Ley 21.030)'),
    ]
    
    # Causales legales para estadísticas IVE
    CAUSALES = [
        ('na', 'No Aplica (Espontáneo)'),
        ('causal_1', 'Causal 1: Riesgo vital materno'),
        ('causal_2', 'Causal 2: Inviabilidad fetal'),
        ('causal_3', 'Causal 3: Violación'),
    ]

    # Flujo de trabajo
    ESTADOS = [
        ('derivado', 'Derivado por Matrona (Pendiente)'), # Esperando médico
        ('confirmado', 'Procedimiento Realizado'),        # Resuelto
        ('descartado', 'Descartado / Falsa Alarma'),      # Falsa alarma
    ]

    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name='abortos')
    tipo = models.CharField(max_length=20, choices=TIPO_ABORTO, default='espontaneo')
    causal = models.CharField(max_length=20, choices=CAUSALES, default='na')
    
    # --- FASE 1: DERIVACIÓN (Matrona) ---
    fecha_derivacion = models.DateTimeField(auto_now_add=True)
    matrona_derivadora = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='abortos_derivados',
        on_delete=models.SET_NULL, null=True
    )
    observacion_matrona = models.TextField(verbose_name="Motivo de Derivación")

    # --- FASE 2: RESOLUCIÓN (Médico) ---
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    medico_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='abortos_resueltos',
        on_delete=models.SET_NULL, null=True, blank=True
    )
    diagnostico_final = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='derivado')

    # Historial de cambios
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Caso Aborto/IVE"
        verbose_name_plural = "Casos Aborto/IVE"

    def __str__(self):
        return f"Caso {self.madre.nombre} - {self.get_estado_display()}"