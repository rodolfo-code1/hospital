# altas/admin.py
from django.contrib import admin
from .models import Alta

@admin.register(Alta)
class AltaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'registros_completos', 'fecha_creacion')
    search_fields = ('madre__nombre', 'madre__rut')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'fecha_alta')
    
    fieldsets = (
        ('Información del Alta', {
            'fields': ('madre', 'parto', 'recien_nacido', 'estado')
        }),
        ('Validación de Registros', {
            'fields': ('registros_completos', 'observaciones_validacion')
        }),
        ('Alta Clínica', {
            'fields': (
                'alta_clinica_confirmada',
                'medico_confirma',
                'fecha_confirmacion_clinica'
            )
        }),
        ('Alta Administrativa', {
            'fields': (
                'alta_administrativa_confirmada',
                'administrativo_confirma',
                'fecha_confirmacion_administrativa'
            )
        }),
        ('Documentos', {
            'fields': ('certificado_generado', 'ruta_certificado')
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
                'fecha_alta'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['validar_registros_action']
    
    def validar_registros_action(self, request, queryset):
        """Acción para validar registros de altas seleccionadas"""
        validadas = 0
        for alta in queryset:
            if alta.validar_registros():
                validadas += 1
        
        self.message_user(
            request,
            f"{validadas} alta(s) validada(s) correctamente."
        )
    
    validar_registros_action.short_description = "Validar registros de altas seleccionadas"