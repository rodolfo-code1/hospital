from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db.models import Q
from django.db import models
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import RegistroAuditoria
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

def es_supervisor(user):
    """Verificar si el usuario es supervisor"""
    return user.is_authenticated and user.rol == 'supervisor'

@user_passes_test(es_supervisor)
def lista_auditoria(request):
    """
    Lista los registros de auditoría con filtros
    """
    # Obtener parámetros de filtrado
    usuario_id = request.GET.get('usuario')
    accion = request.GET.get('accion')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    modelo = request.GET.get('modelo')
    busqueda = request.GET.get('busqueda')
    
    # Query base
    registros = RegistroAuditoria.objects.select_related(
        'usuario', 'content_type'
    ).all()
    
    # Aplicar filtros
    if usuario_id:
        registros = registros.filter(usuario_id=usuario_id)
    
    if accion:
        registros = registros.filter(accion=accion)
    
    if modelo:
        registros = registros.filter(content_type__model=modelo)
    
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            registros = registros.filter(timestamp__date__gte=fecha_desde.date())
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            registros = registros.filter(timestamp__date__lte=fecha_hasta.date())
        except ValueError:
            pass
    
    if busqueda:
        registros = registros.filter(
            Q(descripcion__icontains=busqueda) |
            Q(usuario__username__icontains=busqueda) |
            Q(usuario__first_name__icontains=busqueda) |
            Q(usuario__last_name__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(registros, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para los filtros
    usuarios = User.objects.all()
    modelos = ContentType.objects.all()
    acciones = dict(RegistroAuditoria.ACCION_CHOICES)
    
    context = {
        'page_obj': page_obj,
        'usuarios': usuarios,
        'modelos': modelos,
        'acciones': acciones,
        'filtros_activos': {
            'usuario': usuario_id,
            'accion': accion,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'modelo': modelo,
            'busqueda': busqueda,
        }
    }
    
    return render(request, 'auditoria/lista_auditoria.html', context)

@user_passes_test(es_supervisor)
def detalle_auditoria(request, pk):
    """
    Muestra el detalle de un registro de auditoría específico
    """
    registro = get_object_or_404(RegistroAuditoria, pk=pk)
    
    context = {
        'registro': registro
    }
    
    return render(request, 'auditoria/detalle_auditoria.html', context)

@user_passes_test(es_supervisor)
def estadisticas_auditoria(request):
    """
    Retorna estadísticas de auditoría en formato JSON
    """
    # Estadísticas por usuario
    stats_usuarios = RegistroAuditoria.objects.values(
        'usuario__username', 'usuario__first_name', 'usuario__last_name'
    ).annotate(
        total_acciones=models.Count('id'),
        creaciones=models.Count('id', filter=models.Q(accion='create')),
        actualizaciones=models.Count('id', filter=models.Q(accion='update')),
        eliminaciones=models.Count('id', filter=models.Q(accion='delete')),
    ).order_by('-total_acciones')[:10]
    
    # Estadísticas por acción
    stats_acciones = RegistroAuditoria.objects.values('accion').annotate(
        total=models.Count('id')
    ).order_by('-total')
    
    # Estadísticas por día (últimos 30 días)
    fecha_inicio = timezone.now() - timedelta(days=30)
    stats_diarias = RegistroAuditoria.objects.filter(
        timestamp__gte=fecha_inicio
    ).extra(
        select={'fecha': 'DATE(timestamp)'}
    ).values('fecha').annotate(
        total=models.Count('id')
    ).order_by('fecha')
    
    # Estadísticas por modelo
    stats_modelos = RegistroAuditoria.objects.values(
        'content_type__model'
    ).annotate(
        total=models.Count('id')
    ).order_by('-total')[:10]
    
    data = {
        'usuarios': list(stats_usuarios),
        'acciones': list(stats_acciones),
        'diarias': list(stats_diarias),
        'modelos': list(stats_modelos),
    }
    
    return JsonResponse(data)