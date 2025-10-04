# partos/admin.py
from django.contrib import admin
from .models import Parto

@admin.register(Parto)
class PartoAdmin(admin.ModelAdmin):
    list_display = ('madre', 'tipo', 'fecha_hora_inicio', 'fecha_hora_termino', 'tuvo_complicaciones', 'medico_responsable')
    list_filter = ('tipo', 'tuvo_complicaciones', 'fecha_hora_inicio')
    search_fields = ('madre__nombre', 'madre__rut', 'medico_responsable', 'matrona_responsable')
    readonly_fields = ('fecha_registro', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información del Parto', {
            'fields': ('madre', 'tipo', 'fecha_hora_inicio', 'fecha_hora_termino')
        }),
        ('Personal Clínico', {
            'fields': ('medico_responsable', 'matrona_responsable', 'personal_apoyo')
        }),
        ('Complicaciones', {
            'fields': ('tuvo_complicaciones', 'complicaciones')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )