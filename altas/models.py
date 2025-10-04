# altas/models.py
from django.db import models
from django.core.exceptions import ValidationError
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from django.utils import timezone

class Alta(models.Model):
    """
    Modelo de Alta - Módulo 4
    Gestiona el proceso de alta médica y administrativa de madre y recién nacido.
    """
    
    ESTADO_ALTA = [
        ('pendiente', 'Pendiente de Validación'),
        ('validada', 'Registros Validados'),
        ('alta_clinica', 'Alta Clínica Confirmada'),
        ('alta_administrativa', 'Alta Administrativa Confirmada'),
        ('completada', 'Alta Completada'),
        ('rechazada', 'Rechazada'),
    ]
    
    # Relaciones
    madre = models.OneToOneField(
        Madre,
        on_delete=models.CASCADE,
        related_name='alta',
        verbose_name="Madre"
    )
    parto = models.OneToOneField(
        Parto,
        on_delete=models.CASCADE,
        related_name='alta',
        verbose_name="Parto"
    )
    recien_nacido = models.OneToOneField(
        RecienNacido,
        on_delete=models.CASCADE,
        related_name='alta',
        verbose_name="Recién Nacido"
    )
    
    # Estado del proceso
    estado = models.CharField(
        max_length=30,
        choices=ESTADO_ALTA,
        default='pendiente',
        verbose_name="Estado del alta"
    )
    
    # Validaciones
    registros_completos = models.BooleanField(
        default=False,
        verbose_name="¿Registros completos?",
        help_text="Validación automática de que madre, parto y RN tienen datos completos"
    )
    observaciones_validacion = models.TextField(
        blank=True,
        verbose_name="Observaciones de validación",
        help_text="Campos faltantes o problemas detectados"
    )
    
    # Confirmaciones
    alta_clinica_confirmada = models.BooleanField(
        default=False,
        verbose_name="Alta clínica confirmada"
    )
    medico_confirma = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Médico que confirma alta clínica"
    )
    fecha_confirmacion_clinica = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha confirmación clínica"
    )
    
    alta_administrativa_confirmada = models.BooleanField(
        default=False,
        verbose_name="Alta administrativa confirmada"
    )
    administrativo_confirma = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Administrativo que confirma alta"
    )
    fecha_confirmacion_administrativa = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha confirmación administrativa"
    )
    
    # Documentos generados
    certificado_generado = models.BooleanField(
        default=False,
        verbose_name="¿Certificado PDF generado?"
    )
    ruta_certificado = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Ruta del certificado PDF"
    )
    
    # Fechas del proceso
    fecha_alta = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de alta definitiva"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )
    
    # Observaciones generales
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones generales"
    )
    
    class Meta:
        verbose_name = "Alta"
        verbose_name_plural = "Altas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Alta - {self.madre.nombre} ({self.get_estado_display()})"
    
    def validar_registros(self):
        """
        Valida que madre, parto y recién nacido tengan registros completos.
        Actualiza el campo registros_completos y observaciones_validacion.
        """
        problemas = []
        
        # Validar madre
        if not self.madre.tiene_registros_completos():
            problemas.append("Madre: faltan datos personales o clínicos")
        
        # Validar parto
        if not self.parto.tiene_registros_completos():
            problemas.append("Parto: faltan datos del proceso o personal clínico")
        
        # Validar recién nacido
        if not self.recien_nacido.tiene_registros_completos():
            problemas.append("Recién Nacido: faltan datos clínicos o valoración APGAR")
        
        # Actualizar estado
        if problemas:
            self.registros_completos = False
            self.observaciones_validacion = " | ".join(problemas)
            self.estado = 'pendiente'
        else:
            self.registros_completos = True
            self.observaciones_validacion = "Todos los registros están completos"
            if self.estado == 'pendiente':
                self.estado = 'validada'
        
        self.save()
        return self.registros_completos
    
    def confirmar_alta_clinica(self, medico_nombre):
        """Confirma el alta clínica por parte del médico"""
        if not self.registros_completos:
            raise ValidationError("No se puede confirmar alta clínica sin registros completos")
        
        self.alta_clinica_confirmada = True
        self.medico_confirma = medico_nombre
        self.fecha_confirmacion_clinica = timezone.now()
        self.estado = 'alta_clinica'
        self.save()
        
        # Verificar si se completa el alta
        self._verificar_alta_completa()
    
    def confirmar_alta_administrativa(self, administrativo_nombre):
        """Confirma el alta administrativa"""
        if not self.alta_clinica_confirmada:
            raise ValidationError("Debe confirmarse primero el alta clínica")
        
        self.alta_administrativa_confirmada = True
        self.administrativo_confirma = administrativo_nombre
        self.fecha_confirmacion_administrativa = timezone.now()
        self.estado = 'alta_administrativa'
        self.save()
        
        # Verificar si se completa el alta
        self._verificar_alta_completa()
    
    def _verificar_alta_completa(self):
        """Verifica si ambas confirmaciones están completas"""
        if self.alta_clinica_confirmada and self.alta_administrativa_confirmada:
            self.estado = 'completada'
            self.fecha_alta = timezone.now()
            self.save()
    
    def puede_confirmar_alta_clinica(self):
        """Verifica si se puede confirmar el alta clínica"""
        return self.registros_completos and not self.alta_clinica_confirmada
    
    def puede_confirmar_alta_administrativa(self):
        """Verifica si se puede confirmar el alta administrativa"""
        return self.alta_clinica_confirmada and not self.alta_administrativa_confirmada
    
    def esta_completada(self):
        """Verifica si el proceso de alta está completado"""
        return self.estado == 'completada'