# pacientes/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Madre(models.Model):
    PREVISION_CHOICES = [
        ('fonasa_a', 'FONASA A'),
        ('fonasa_b', 'FONASA B'),
        ('fonasa_c', 'FONASA C'),
        ('fonasa_d', 'FONASA D'),
        ('isapre', 'ISAPRE'),
        ('particular', 'PARTICULAR'),
        ('otra', 'OTRA'),
    ]

    rut = models.CharField(max_length=12, unique=True, verbose_name="RUT", help_text="Ej: 12.345.678-9")
    nombre = models.CharField(max_length=200, verbose_name="Nombre completo")
    
    # --- DATOS DEMOGRÁFICOS (Planilla URNI) ---
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento", null=True, blank=True)
    edad = models.IntegerField(validators=[MinValueValidator(10), MaxValueValidator(60)], verbose_name="Edad")
    nacionalidad = models.CharField(max_length=100, default="Chilena", verbose_name="Nacionalidad")
    prevision = models.CharField(max_length=20, choices=PREVISION_CHOICES, default='fonasa_b', verbose_name="Previsión")
    
    direccion = models.CharField(max_length=300, verbose_name="Dirección", blank=True)
    comuna = models.CharField(max_length=100, verbose_name="Comuna", blank=True)
    cesfam = models.CharField(max_length=150, verbose_name="CESFAM de Origen", blank=True, help_text="Centro de Salud Familiar")
    
    telefono = models.CharField(max_length=15, verbose_name="Teléfono", blank=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Correo electrónico")
    
    alerta_recepcion = models.TextField(
        blank=True, 
        verbose_name="Alerta de Ingreso", 
        help_text="Observación crítica al momento de la recepción (Ej: Sangrado, dolor agudo)"
    )

    # --- ANTECEDENTES OBSTÉTRICOS ---
    controles_prenatales = models.IntegerField(default=0, verbose_name="N° Controles")
    embarazos_anteriores = models.IntegerField(default=0, verbose_name="Para (Partos previos)")
    patologias = models.TextField(blank=True, verbose_name="Diagnósticos / Patologías", help_text="Ej: RNT 38 SEM AEG, HMD")
    
    # --- AUDITORÍA ---
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='madres_registradas',
        verbose_name="Registrado por"
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

    responsable_clinico = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fichas_clinicas_completadas',
        verbose_name="Matrona Responsable"
    )

    class Meta:
        verbose_name = "Madre"
        verbose_name_plural = "Madres"
        ordering = ['-fecha_ingreso']
    
    def __str__(self):
        return f"{self.nombre} ({self.rut})"

    def tiene_registros_completos(self):
        return all([self.nombre, self.rut, self.edad, self.comuna])