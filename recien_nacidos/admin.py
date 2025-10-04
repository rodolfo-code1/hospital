# recien_nacidos/admin.py
from django.contrib import admin
from .models import RecienNacido

@admin.register(RecienNacido)
class RecienNacidoAdmin(admin.ModelAdmin):
    list_display = ('codigo_unico', 'nombre', 'sexo', 'peso', 'talla', 'apgar_1_min', 'apgar_5_min', 'parto', 'requiere_derivacion')
    list_filter = ('sexo', 'condicion_nacimiento', 'requiere_derivacion', 'fecha_registro')
    search_fields = ('codigo_unico', 'nombre', 'parto__madre__nombre', 'parto__madre__rut')
    readonly_fields = ('codigo_unico', 'fecha_registro', 'fecha_actualizacion')
    
    fieldsets = (
        ('Identificación', {
            'fields': ('codigo_unico', 'parto', 'nombre', 'sexo')
        }),
        ('Datos Clínicos', {
            'fields': ('peso', 'talla', 'condicion_nacimiento')
        }),
        ('Valoración APGAR', {
            'fields': ('apgar_1_min', 'apgar_5_min', 'apgar_10_min')
        }),
        ('Derivación', {
            'fields': ('requiere_derivacion', 'servicio_derivacion')
        }),
        ('Controles y Procedimientos', {
            'fields': ('vacunas_aplicadas', 'examenes_realizados')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )