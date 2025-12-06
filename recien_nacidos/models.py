from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from partos.models import Parto
import uuid
from django.conf import settings

class RecienNacido(models.Model):
    # ... (Constantes SEXO y CONDICION se mantienen igual) ...
    SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino'), ('I', 'Indeterminado')]
    CONDICION_CHOICES = [('vivo', 'Vivo'), ('mortinato', 'Mortinato')]

    # --- OPCIONES APGAR (Puntaje 0, 1, 2) ---
    OPCIONES_FC = [(0, 'Ausente'), (1, '< 100 lpm'), (2, '> 100 lpm')]
    OPCIONES_RESP = [(0, 'Ausente'), (1, 'Lenta / Irregular'), (2, 'Buena / Llanto fuerte')]
    OPCIONES_TONO = [(0, 'Flácido'), (1, 'Cierta flexión'), (2, 'Movimiento activo')]
    OPCIONES_REFLEJOS = [(0, 'Sin respuesta'), (1, 'Mueca'), (2, 'Tos / Estornudo / Llanto')]
    OPCIONES_COLOR = [(0, 'Azul / Pálido'), (1, 'Cuerpo rosado, manos/pies azules'), (2, 'Completamente rosado')]

    # Identificación
    codigo_unico = models.CharField(max_length=50, unique=True, editable=False)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='recien_nacidos')
    nombre = models.CharField(max_length=200, blank=True, verbose_name="Nombre RN")
    
    # Antropometría
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    peso = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Peso (kg)")
    talla = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="Talla (cm)")
    perimetro_cefalico = models.DecimalField(max_digits=4, decimal_places=1, verbose_name="CC (cm)", null=True, blank=True)
    
    # --- DETALLE APGAR MINUTO 1 ---
    ap1_latidos = models.IntegerField(default=0, choices=OPCIONES_FC, verbose_name="1' Frec. Cardíaca")
    ap1_respiracion = models.IntegerField(default=0, choices=OPCIONES_RESP, verbose_name="1' Respiración")
    ap1_tono = models.IntegerField(default=0, choices=OPCIONES_TONO, verbose_name="1' Tono Muscular")
    ap1_reflejos = models.IntegerField(default=0, choices=OPCIONES_REFLEJOS, verbose_name="1' Reflejos")
    ap1_color = models.IntegerField(default=0, choices=OPCIONES_COLOR, verbose_name="1' Color")
    
    # --- DETALLE APGAR MINUTO 5 ---
    ap5_latidos = models.IntegerField(default=0, choices=OPCIONES_FC, verbose_name="5' Frec. Cardíaca")
    ap5_respiracion = models.IntegerField(default=0, choices=OPCIONES_RESP, verbose_name="5' Respiración")
    ap5_tono = models.IntegerField(default=0, choices=OPCIONES_TONO, verbose_name="5' Tono Muscular")
    ap5_reflejos = models.IntegerField(default=0, choices=OPCIONES_REFLEJOS, verbose_name="5' Reflejos")
    ap5_color = models.IntegerField(default=0, choices=OPCIONES_COLOR, verbose_name="5' Color")

    # --- TOTALES (Calculados automáticamente) ---
    apgar_1_min = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 1' Total")
    apgar_5_min = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 5' Total")
    apgar_10_min = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(10)], verbose_name="APGAR 10'")
    
    condicion_nacimiento = models.CharField(max_length=20, choices=CONDICION_CHOICES, default='vivo')
    
    # Estados y Alertas
    estado_salud = models.CharField(max_length=20, choices=[('sano','Sano'),('observacion','Obs.'),('critico','Crítico')], default='observacion')
    estado_alta = models.CharField(max_length=20, choices=[('hospitalizado','Hosp.'),('en_proceso','Alta Proc.'),('alta_administrativa','Egresado')], default='hospitalizado')
    alerta_revisada = models.BooleanField(default=False)

    # Indicadores Calidad
    lactancia_precoz = models.BooleanField(default=False)
    apego_piel_a_piel = models.BooleanField(default=False)
    profilaxis_ocular = models.BooleanField(default=True)
    
    # Vacunas
    vacuna_hepatitis_b = models.BooleanField(default=False)
    responsable_vacuna_vhb = models.CharField(max_length=150, blank=True)
    vacuna_bcg = models.BooleanField(default=False)
    
    # Otros
    requiere_derivacion = models.BooleanField(default=False)
    servicio_derivacion = models.CharField(max_length=200, blank=True)
    examenes_realizados = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    
    # Auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recien_nacidos_registrados')
    
    class Meta:
        verbose_name = "Recién Nacido"
        verbose_name_plural = "Recién Nacidos"
        ordering = ['-fecha_registro']
    
    def save(self, *args, **kwargs):
        if not self.codigo_unico:
            self.codigo_unico = f"RN-{uuid.uuid4().hex[:8].upper()}"
        # Opcional: Recalcular totales aquí por seguridad (backend)
        self.apgar_1_min = self.ap1_latidos + self.ap1_respiracion + self.ap1_tono + self.ap1_reflejos + self.ap1_color
        self.apgar_5_min = self.ap5_latidos + self.ap5_respiracion + self.ap5_tono + self.ap5_reflejos + self.ap5_color
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.codigo_unico}"

    def tiene_registros_completos(self):
        return all([self.peso, self.talla, self.sexo])