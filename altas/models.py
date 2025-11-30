# altas/models.py
from django.db import models
from django.core.exceptions import ValidationError
from django.db import models
from django.core.exceptions import ValidationError
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from django.utils import timezone

class Alta(models.Model):
    ESTADO_ALTA = [
        ('pendiente', 'Pendiente de Validación'),
        ('validada', 'Registros Validados'),
        ('alta_clinica', 'Alta Clínica Confirmada'),
        ('alta_administrativa', 'Alta Administrativa Confirmada'),
        ('completada', 'Alta Completada'),
    ]
    
    # CAMBIO: ForeignKey con null=True para permitir altas individuales
    madre = models.ForeignKey(Madre, on_delete=models.CASCADE, related_name='altas', null=True, blank=True)
    parto = models.ForeignKey(Parto, on_delete=models.CASCADE, related_name='altas', null=True, blank=True)
    recien_nacido = models.ForeignKey(RecienNacido, on_delete=models.CASCADE, related_name='altas', null=True, blank=True)
    
    estado = models.CharField(max_length=30, choices=ESTADO_ALTA, default='pendiente')
    
    registros_completos = models.BooleanField(default=False)
    observaciones_validacion = models.TextField(blank=True)
    
    alta_clinica_confirmada = models.BooleanField(default=False)
    medico_confirma = models.CharField(max_length=200, blank=True)
    fecha_confirmacion_clinica = models.DateTimeField(null=True, blank=True)
    
    alta_administrativa_confirmada = models.BooleanField(default=False)
    administrativo_confirma = models.CharField(max_length=200, blank=True)
    fecha_confirmacion_administrativa = models.DateTimeField(null=True, blank=True)
    
    certificado_generado = models.BooleanField(default=False)
    ruta_certificado = models.CharField(max_length=500, blank=True)
    
    fecha_alta = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Alta"
        verbose_name_plural = "Altas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Alta #{self.id} ({self.get_estado_display()})"

    def validar_registros(self):
        problemas = []
        if self.madre and not self.madre.tiene_registros_completos():
            problemas.append("Madre: Datos incompletos")
        if self.recien_nacido and not self.recien_nacido.tiene_registros_completos():
            problemas.append("RN: Datos incompletos")
            
        if problemas:
            self.registros_completos = False
            self.observaciones_validacion = " | ".join(problemas)
        else:
            self.registros_completos = True
            self.observaciones_validacion = "Completo"
            if self.estado == 'pendiente':
                self.estado = 'validada'
        self.save()
        return self.registros_completos

    def confirmar_alta_clinica(self, medico):
        self.alta_clinica_confirmada = True
        self.medico_confirma = medico
        self.fecha_confirmacion_clinica = timezone.now()
        self.estado = 'alta_clinica'
        self.save()
        self._verificar_alta_completa()

    def confirmar_alta_administrativa(self, admin):
        self.alta_administrativa_confirmada = True
        self.administrativo_confirma = admin
        self.fecha_confirmacion_administrativa = timezone.now()
        self.estado = 'alta_administrativa'
        
        # Liberar pacientes
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