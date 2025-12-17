from django.db import models
from django.core.exceptions import ValidationError
from pacientes.models import Madre
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from django.utils import timezone
from simple_history.models import HistoricalRecords

class Alta(models.Model):
    """
    Modelo principal para gestionar el proceso de egreso hospitalario.
    
    Funciona como un 'contenedor' que agrupa a los pacientes involucrados en un evento clínico
    (Madre, Recién Nacido, Parto o Aborto) y gestiona su transición fuera del hospital.
    
    Atributos Principales:
        - estado: Controla el flujo (pendiente -> validada -> alta_clinica -> alta_administrativa -> completada).
        - validaciones: Campos booleanos que aseguran la integridad de los datos antes de firmar.
        - firmas: Registra quién (médico/administrativo) autorizó cada etapa y cuándo.
    """
    # Estados del flujo de trabajo
    ESTADO_ALTA = [
        ('pendiente', 'Pendiente de Validación'),       # Faltan datos obligatorios
        ('validada', 'Registros Validados'),            # Datos completos, listo para firma médica
        ('alta_clinica', 'Alta Clínica Confirmada'),    # Médico autorizó salida
        ('alta_administrativa', 'Alta Administrativa Confirmada'), # Admisión cerró cuenta
        ('completada', 'Alta Completada'),              # Proceso finalizado
        ('rechazada', 'Rechazada'),                     # Alta cancelada o devuelta
    ]
    # Opciones para reporte REM Sección C (Estadísticas de Anticoncepción)
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
    
    # --- RELACIONES ---
    # Un alta puede estar asociada a una Madre, un Parto, un Recién Nacido o un Aborto.
    # Son opcionales (null=True) porque un alta puede ser solo de la madre o solo del bebé.
    madre = models.ForeignKey(
        Madre,
        on_delete=models.CASCADE,
        related_name='altas',
        verbose_name="Madre",
        null=True, blank=True
    )
    parto = models.ForeignKey(
        Parto,
        on_delete=models.CASCADE,
        related_name='altas',
        verbose_name="Parto",
        null=True, blank=True
    )
    recien_nacido = models.ForeignKey(
        RecienNacido,
        on_delete=models.CASCADE,
        related_name='altas',
        verbose_name="Recién Nacido",
        null=True, blank=True
    )

    # Relación con Aborto (para cerrar el ciclo IVE)
    aborto = models.ForeignKey(
        'partos.Aborto',
        on_delete=models.CASCADE,
        related_name='altas',
        verbose_name="Evento Aborto",
        null=True, blank=True
    )
    
    estado = models.CharField(max_length=30, choices=ESTADO_ALTA, default='pendiente')
    
    # Validaciones
    registros_completos = models.BooleanField(default=False, verbose_name="¿Registros completos?")
    observaciones_validacion = models.TextField(blank=True, verbose_name="Obs. Validación")
    
    # --- CONFIRMACIÓN CLÍNICA (Firma Médica) ---
    alta_clinica_confirmada = models.BooleanField(default=False)
    medico_confirma = models.CharField(max_length=200, blank=True)
    fecha_confirmacion_clinica = models.DateTimeField(null=True, blank=True)
    
    se_entrego_anticonceptivo = models.BooleanField(default=False, verbose_name="¿Se entregó MAC?")
    metodo_anticonceptivo = models.CharField(
        max_length=50, 
        choices=METODOS_ANTICONCEPTIVOS, 
        default='ninguno',
        verbose_name="Método entregado",
        blank=True
    )
    
    # --- CONFIRMACIÓN ADMINISTRATIVA (Firma Admisión) ---
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
    
    # Historial de auditoría (guarda cada cambio en el modelo)
    history = HistoricalRecords()
    
    class Meta:
        verbose_name = "Alta"
        verbose_name_plural = "Altas"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        """Retorna una descripción legible del alta para el panel de administración."""
        nombre = "Alta General"
        if self.madre: nombre = f"Alta Madre: {self.madre.nombre}"
        elif self.recien_nacido: nombre = f"Alta RN: {self.recien_nacido.codigo_unico}"
        return f"{nombre} ({self.get_estado_display()})"
    
    def validar_registros(self):
        """
        Ejecuta las reglas de negocio para verificar que los expedientes estén completos.
        
        Lógica:
        1. Revisa cada entidad relacionada (Madre, Parto, RN).
        2. Llama a métodos de validación internos de esos modelos (`tiene_registros_completos`).
        3. Si hay errores, el estado vuelve a 'pendiente'.
        4. Si todo está bien, el estado pasa a 'validada'.
        
        Returns:
            bool: True si todo está correcto, False si faltan datos.
        """
        problemas = []
        if self.madre and not self.madre.tiene_registros_completos():
            problemas.append("Madre: Faltan datos")
        if self.parto and not self.parto.tiene_registros_completos():
            problemas.append("Parto: Faltan datos")
        if self.recien_nacido and not self.recien_nacido.tiene_registros_completos():
            problemas.append("RN: Faltan datos")
        if self.aborto and self.aborto.estado != 'confirmado':
            problemas.append("Aborto: No confirmado por médico")
            
        if problemas:
            self.registros_completos = False
            self.observaciones_validacion = " | ".join(problemas)
            self.estado = 'pendiente'
        else:
            self.registros_completos = True
            self.observaciones_validacion = "Registros completos"
            if self.estado == 'pendiente':
                self.estado = 'validada'
        
        self.save()
        return self.registros_completos
    
    def confirmar_alta_clinica(self, medico_nombre):
        """
        Registra la firma del médico responsable.
        
        Args:
            medico_nombre (str): Nombre del usuario médico logueado.
        """
        self.alta_clinica_confirmada = True
        self.medico_confirma = medico_nombre
        self.fecha_confirmacion_clinica = timezone.now()
        self.estado = 'alta_clinica'
        self.save()
        self._verificar_alta_completa()
    
    def confirmar_alta_administrativa(self, admin_nombre):
        """
        Registra el cierre administrativo y LIBERA los recursos del hospital.
        
        Efectos secundarios importantes:
        - Cambia el estado interno de Madre, RN y Parto a 'alta_administrativa'.
        - Esto hace que desaparezcan de los listados de pacientes hospitalizados.
        
        Args:
            admin_nombre (str): Nombre del funcionario administrativo.
        """
        self.alta_administrativa_confirmada = True
        self.administrativo_confirma = admin_nombre
        self.fecha_confirmacion_administrativa = timezone.now()
        self.estado = 'alta_administrativa'
        
        # --- CAMBIO CLAVE: CERRAR LOS ESTADOS PARA QUE DESAPAREZCAN DE LAS LISTAS ---
        
        # 1. Liberar Madre
        if self.madre:
            self.madre.estado_alta = 'alta_administrativa'
            self.madre.save()
            
        # 2. Liberar Recién Nacido
        if self.recien_nacido:
            self.recien_nacido.estado_alta = 'alta_administrativa'
            self.recien_nacido.save()
            
        # 3. Cerrar el Parto 
        # Al cerrar el parto, deja de aparecer en el selector de "Registrar RN"
        if self.parto:
            self.parto.estado_alta = 'alta_administrativa'
            self.parto.save()
            
        # 4. Si es un aborto, también se cierra
        if self.aborto:
            
            pass
            
        self.save()
        self._verificar_alta_completa()
    
    def _verificar_alta_completa(self):
        """Método interno que finaliza el proceso si ambas firmas existen."""
        if self.alta_clinica_confirmada and self.alta_administrativa_confirmada:
            self.estado = 'completada'
            self.fecha_alta = timezone.now()
            self.save()
    
    def puede_confirmar_alta_clinica(self):
        """Verifica si el alta está lista para firma médica (validada y sin firmar)."""
        return self.registros_completos and not self.alta_clinica_confirmada
    
    def puede_confirmar_alta_administrativa(self):
        """Verifica si el alta está lista para cierre administrativo (ya tiene firma médica)."""
        return self.alta_clinica_confirmada and not self.alta_administrativa_confirmada
    
    def esta_completada(self):
        return self.estado == 'completada'