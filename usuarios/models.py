# usuarios/models.py
# usuarios/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

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