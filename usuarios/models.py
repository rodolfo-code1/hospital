# usuarios/models.py
# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class Usuario(AbstractUser):
    ROLES = [
        ('medico', 'Médico'),
        ('matrona', 'Matrona'),
        ('administrativo', 'Administrativo'),
        ('supervisor', 'Supervisor'),
        ('encargado_ti', 'Encargado TI'),
        ('recepcionista', 'Recepcionista'),
    ]
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='administrativo',
        verbose_name="Rol"
    )
    rut = models.CharField(
        max_length=12,
        unique=True,
        verbose_name="RUT",
        help_text="RUT del usuario (ej: 12345678-9)"
    )
    telefono = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Teléfono"
    )
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
    
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_rol_display()}"
    
    def es_medico(self):
        return self.rol == 'medico'
    
    def es_administrativo(self):
        return self.rol == 'administrativo'
    
    def es_supervisor(self):
        return self.rol == 'supervisor'

    def es_encargado_ti(self):
        return self.rol == 'encargado_ti'
    
    def es_recepcionista(self):
        return self.rol == 'recepcionista'


class AuditoriaLogin(models.Model):
    """Registro de auditoría de inicios de sesión"""
    TIPO_EVENTO = [
        ('login', 'Inicio de Sesión'),
        ('logout', 'Cierre de Sesión'),
        ('login_fallido', 'Login Fallido'),
    ]
    
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='auditorias_login'
    )
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO)
    fecha_evento = models.DateTimeField(auto_now_add=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, verbose_name="Navegador/Dispositivo")
    session_key = models.CharField(max_length=40, blank=True, null=True)
    nombre_usuario = models.CharField(max_length=150, blank=True, verbose_name="Nombre Usuario Intentado")
    exitoso = models.BooleanField(default=True)
    razon_fallo = models.CharField(max_length=255, blank=True)
    
    class Meta:
        verbose_name = "Auditoría Login"
        verbose_name_plural = "Auditorías Login"
        ordering = ['-fecha_evento']
        indexes = [
            models.Index(fields=['-fecha_evento']),
            models.Index(fields=['usuario', '-fecha_evento']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.get_full_name() if self.usuario else self.nombre_usuario
        return f"{usuario_str} - {self.get_tipo_evento_display()} - {self.fecha_evento.strftime('%d/%m/%Y %H:%M')}"


class AuditoriaModificacion(models.Model):
    """Registro de auditoría de modificaciones de datos"""
    TIPO_OPERACION = [
        ('create', 'Creación'),
        ('update', 'Modificación'),
        ('delete', 'Eliminación'),
    ]
    
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias_modificacion'
    )
    tipo_operacion = models.CharField(max_length=20, choices=TIPO_OPERACION)
    fecha_evento = models.DateTimeField(auto_now_add=True)
    modelo = models.CharField(max_length=100, verbose_name="Modelo Afectado")
    id_objeto = models.IntegerField(verbose_name="ID del Objeto")
    descripcion = models.TextField(verbose_name="Descripción del Cambio", blank=True)
    valores_anteriores = models.JSONField(default=dict, blank=True)
    valores_nuevos = models.JSONField(default=dict, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    
    class Meta:
        verbose_name = "Auditoría Modificación"
        verbose_name_plural = "Auditorías Modificación"
        ordering = ['-fecha_evento']
        indexes = [
            models.Index(fields=['-fecha_evento']),
            models.Index(fields=['usuario', '-fecha_evento']),
            models.Index(fields=['modelo', 'id_objeto']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_operacion_display()} - {self.modelo} (ID: {self.id_objeto}) - {self.fecha_evento.strftime('%d/%m/%Y %H:%M')}"
