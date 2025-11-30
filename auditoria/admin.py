from django.contrib import admin
from .models import RegistroAuditoria, ConfiguracionAuditoria

@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'content_type', 'object_id', 'timestamp', 'descripcion')
    list_filter = ('accion', 'content_type', 'timestamp', 'usuario')
    search_fields = ('usuario__username', 'descripcion', 'valores_anteriores', 'valores_nuevos')
    readonly_fields = ('timestamp', 'usuario')
    ordering = ('-timestamp',)
    
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'accion', 'timestamp')
        }),
        ('Objeto Modificado', {
            'fields': ('content_type', 'object_id')
        }),
        ('Datos del Cambio', {
            'fields': ('valores_anteriores', 'valores_nuevos', 'campos_modificados')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent', 'descripcion')
        }),
    )

@admin.register(ConfiguracionAuditoria)
class ConfiguracionAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('modelo_auditado', 'registrar_creacion', 'registrar_actualizacion', 'registrar_eliminacion', 'activo')
    list_filter = ('registrar_creacion', 'registrar_actualizacion', 'registrar_eliminacion', 'activo')
    search_fields = ('modelo_auditado__model', 'modelo_auditado__app_label')