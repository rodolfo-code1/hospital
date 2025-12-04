from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from partos.models import Parto
import uuid
from django.conf import settings
from simple_history.models import HistoricalRecords

class RecienNacido(models.Model):
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('I', 'Indeterminado')]
    CONDICION_CHOICES = [('vivo', 'Vivo'), ('mortinato', 'Mortinato')]
    
    # Identificación
    codigo_unico = models.CharField(max_length=50, unique=True, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='recien_nacidos')
    nombre = models.CharField(max_length=200, blank=True, verbose_name="Nombre RN")
    
    # --- ANTROPOMETRÍA (Planilla URNI) ---
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Peso (kg)", help_text="Ej: 3.450")
    talla = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Talla (cm)")
    perimetro_cefalico = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="CC (cm)", null=True, blank=True)
    
    # --- VITALIDAD ---
    apgar_1_min = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 1'")
    apgar_5_min = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 5'")
    apgar_10_min = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 10'")
    condicion_nacimiento = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='vivo')
    
    # --- INDICADORES DE CALIDAD Y ATENCIÓN INMEDIATA ---
    lactancia_precoz = models.BooleanField(default=False, verbose_name="Lactancia < 1hr")
    apego_piel_a_piel = models.BooleanField(default=False, verbose_name="Apego")
    profilaxis_ocular = models.BooleanField(default=True, verbose_name="Profilaxis Ocular")
    
    # --- VACUNAS (Planilla URNI - Sección Vacunas) ---
    vacuna_hepatitis_b = models.BooleanField(default=False, verbose_name="Vacuna Hepatitis B")
    responsable_vacuna_vhb = models.CharField(max_length=150, blank=True, verbose_name="Resp. Vacuna VHB")
    vacuna_bcg = models.BooleanField(default=False, verbose_name="Vacuna BCG")
    
    # Derivación y Estado
    requiere_derivacion = models.BooleanField(default=False)
    servicio_derivacion = models.CharField(max_length=200, blank=True, verbose_name="Destino (Ej: UCI, Sala)")
    
    # Otros
    examenes_realizados = models.TextField(blank=True, verbose_name="Gases/Exámenes")
    observaciones = models.TextField(blank=True)
    
    alerta_revisada = models.BooleanField(default=False, verbose_name="Alerta Revisada por Médico")

    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recien_nacidos_registrados'
    )
    
    ESTADO_ALTA = [
        ('hospitalizado', 'Hospitalizado'),
        ('alta_medica', 'Alta Médica (Esperando Admin)'),
        ('alta_administrativa', 'Alta Completa (Egresado)'),
    ]
    estado_alta = models.CharField(
        max_length=20, 
        choices=ESTADO_ALTA, 
        default='hospitalizado',
        verbose_name="Estado Alta"
    )

    ESTADO_SALUD = [
        ('sano', 'Sano / Alta Probable'),
        ('observacion', 'En Observación'),
        ('critico', 'Crítico / UCI'),
    ]
    estado_salud = models.CharField(
        max_length=20, 
        choices=ESTADO_SALUD, 
        default='observacion',
        verbose_name="Estado de Salud"
    )

    # Historial de cambios
    history = HistoricalRecords()

    class Meta:
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"
        ordering = ['-fecha_registro']
    
    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = f"RN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo_unico} ({self.sexo})"
        
    def tiene_registros_completos(self):
        return all([self.peso, self.talla, self.sexo, self.apgar_1_min])