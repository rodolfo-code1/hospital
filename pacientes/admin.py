# pacientes/admin.py
from django.contrib import admin
from .models import Madre

@admin.register(Madre)
class MadreAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'edad', 'telefono', 'controles_prenatales', 'fecha_ingreso')
    list_filter = ('edad', 'fecha_ingreso')
    search_fields = ('rut', 'nombre', 'email')
    readonly_fields = ('fecha_ingreso', 'fecha_actualizacion')
    
    fieldsets = (
        ('Datos Personales', {
            'fields': ('rut', 'nombre', 'edad', 'direccion', 'telefono', 'email')
        }),
        ('Antecedentes Clínicos', {
            'fields': ('controles_prenatales', 'embarazos_anteriores', 'patologias')
        }),
        ('Auditoría', {
            'fields': ('fecha_ingreso', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )