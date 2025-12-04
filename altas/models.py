from django.db import models
from django.core.exceptions import ValidationError
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from django.utils import timezone
from partos.models import Parto, Aborto
from simple_history.models import HistoricalRecords

class Alta(models.Model):
    """
    Modelo de Alta - Módulo 4
    Gestiona el proceso de egreso. Permite altas individuales o conjuntas.
    """
    ESTADO_ALTA = [
        ('pendiente', 'Pendiente de Validación'),
        ('validada', 'Registros Validados'),
        ('alta_clinica', 'Alta Clínica Confirmada'),
        ('alta_administrativa', 'Alta Administrativa Confirmada'),
        ('completada', 'Alta Completada'),
        ('rechazada', 'Rechazada'),
    ]

    # Opciones de Anticonceptivos (MAC)
    METODOS_ANTICONCEPTIVOS = [
        ('ninguno', 'Ninguno / No aplica'),
        ('diu', 'DIU (Dispositivo Intrauterino)'),
        ('implante', 'Implante Subdérmico'),
        ('oral', 'Anticonceptivo Oral (Pastillas)'),
        ('inyeccion', 'Inyectable'),
        ('preservativo', 'Preservativos'),
        ('ligadura', 'Ligadura de Trompas (Esterilización)'),
        ('otro', 'Otro Método'),

    
    ]
    
    # Relaciones Opcionales
    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name='altas', verbose_name="Madre", null=True, blank=True)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='altas', verbose_name="Parto", null=True, blank=True)
    recien_nacido = models.ForeignKey(RecienNacido, on_delete=models.CASCADE, related_name='altas', verbose_name="Recién Nacido", null=True, blank=True)
    
    estado = models.CharField(max_length=30, choices=ESTADO_ALTA, default='pendiente')
    
    # Validaciones
    registros_completos = models.BooleanField(default=False, verbose_name="¿Registros completos?")
    observaciones_validacion = models.TextField(blank=True, verbose_name="Obs. Validación")
    
    # Confirmación Clínica
    alta_clinica_confirmada = models.BooleanField(default=False)
    medico_confirma = models.CharField(max_length=200, blank=True)
    fecha_confirmacion_clinica = models.DateTimeField(null=True, blank=True)

    # --- NUEVOS CAMPOS: ANTICONCEPCIÓN ---
    se_entrego_anticonceptivo = models.BooleanField(default=False, verbose_name="¿Se entregó MAC?")
    metodo_anticonceptivo = models.CharField(
        max_length=50, 
        choices=METODOS_ANTICONCEPTIVOS, 
        default='ninguno',
        verbose_name="Método entregado",
        blank=True
    )
    # -------------------------------------
    
    # Confirmación Administrativa
    alta_administrativa_confirmada = models.BooleanField(default=False)
    administrativo_confirma = models.CharField(max_length=200, blank=True)
    fecha_confirmacion_administrativa = models.DateTimeField(null=True, blank=True)
    
    # Documentos y Auditoría
    certificado_generado = models.BooleanField(default=False)
    ruta_certificado = models.CharField(max_length=500, blank=True)
    fecha_alta = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    observaciones = models.TextField(blank=True)

    aborto = models.ForeignKey(
        Aborto,
        on_delete=models.CASCADE,
        related_name='altas',
        verbose_name="Evento Aborto",
        null=True, blank=True
    )
    
    # Historial de cambios
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Alta"
        verbose_name_plural = "Altas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        nombre = "Alta General"
        if self.madre: nombre = f"Alta Madre: {self.madre.nombre}"
        elif self.recien_nacido: nombre = f"Alta RN: {self.recien_nacido.codigo_unico}"
        return f"{nombre} ({self.get_estado_display()})"
    
    def validar_registros(self):
        problemas = []
        if self.madre and not self.madre.tiene_registros_completos():
            problemas.append("Madre: Faltan datos")
        
        # Validar Parto O Aborto
        if self.parto and not self.parto.tiene_registros_completos():
            problemas.append("Parto: Faltan datos")
        
        # Si es aborto, asumimos que al confirmarlo el médico llenó todo
        if self.aborto and self.aborto.estado != 'confirmado':
            problemas.append("Aborto: Procedimiento no confirmado por médico")
        if self.madre and not self.madre.tiene_registros_completos(): problemas.append("Madre: Faltan datos")
        if self.parto and not self.parto.tiene_registros_completos(): problemas.append("Parto: Faltan datos")
        if self.recien_nacido and not self.recien_nacido.tiene_registros_completos(): problemas.append("RN: Faltan datos")
        
        if problemas:
            self.registros_completos = False
            self.observaciones_validacion = " | ".join(problemas)
            self.estado = 'pendiente'
        else:
            self.registros_completos = True
            self.observaciones_validacion = "Registros completos"
            if self.estado == 'pendiente': self.estado = 'validada'
        self.save()
        return self.registros_completos
    
    def confirmar_alta_clinica(self, medico_nombre):
        self.alta_clinica_confirmada = True
        self.medico_confirma = medico_nombre
        self.fecha_confirmacion_clinica = timezone.now()
        self.estado = 'alta_clinica'
        self.save()
        self._verificar_alta_completa()
    
    def confirmar_alta_administrativa(self, admin_nombre):
        self.alta_administrativa_confirmada = True
        self.administrativo_confirma = admin_nombre
        self.fecha_confirmacion_administrativa = timezone.now()
        self.estado = 'alta_administrativa'
        if self.madre:
            self.madre.estado_alta = 'alta_administrativa'
            self.madre.save()
        if self.recien_nacido:
            self.recien_nacido.estado_alta = 'alta_administrativa'
            self.recien_nacido.save()
        self.save()
        self._verificar_alta_completa()
    
    def _verificar_alta_completa(self):
        if self.alta_clinica_confirmada and self.alta_administrativa_confirmada:
            self.estado = 'completada'
            self.fecha_alta = timezone.now()
            self.save()
    
    def puede_confirmar_alta_clinica(self):
        return self.registros_completos and not self.alta_clinica_confirmada
    
    def puede_confirmar_alta_administrativa(self):
        return self.alta_clinica_confirmada and not self.alta_administrativa_confirmada
    
    def esta_completada(self):
        return self.estado == 'completada'