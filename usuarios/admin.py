# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AuditoriaLogin, AuditoriaModificacion

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'rol', 'rut', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'rut')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('rol', 'rut', 'telefono')}),
    )

@admin.register(AuditoriaLogin)
class AuditoriaLoginAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_evento', 'fecha_evento', 'direccion_ip', 'exitoso')
    list_filter = ('tipo_evento', 'exitoso', 'fecha_evento')
    search_fields = ('usuario__username', 'nombre_usuario', 'direccion_ip')
    readonly_fields = ('usuario', 'tipo_evento', 'fecha_evento', 'direccion_ip', 'user_agent', 'nombre_usuario', 'exitoso', 'razon_fallo')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(AuditoriaModificacion)
class AuditoriaModificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_operacion', 'modelo', 'id_objeto', 'fecha_evento')
    list_filter = ('tipo_operacion', 'modelo', 'fecha_evento')
    search_fields = ('usuario__username', 'modelo', 'id_objeto')
    readonly_fields = ('usuario', 'tipo_operacion', 'modelo', 'id_objeto', 'fecha_evento', 'descripcion', 'valores_anteriores', 'valores_nuevos')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser