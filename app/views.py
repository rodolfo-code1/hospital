# app/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from datetime import datetime, timedelta
import json
import calendar

from altas.models import Alta
from partos.models import Parto
from pacientes.models import Madre
from recien_nacidos.models import RecienNacido
from auditoria.models import RegistroAuditoria

def es_supervisor(user):
    """Verificar si el usuario es supervisor"""
    return user.is_authenticated and user.rol == 'supervisor'

@login_required
def home(request):
    """
    Dashboard principal del sistema.
    """
    user = request.user
    context = {}

    # Lógica para MÉDICOS
    if user.rol == 'medico':
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()

    # Lógica para ADMINISTRATIVOS
    if user.rol == 'administrativo':
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    
    # Lógica para MATRONAS
    if user.rol == 'matrona':
        hoy = timezone.now().date()
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user  
        ).count()
    
    # Lógica para SUPERVISORES
    if user.rol == 'supervisor':
        context['total_usuarios_activos'] = user.__class__.objects.filter(
            is_active=True
        ).count()
        context['total_madres_registradas'] = Madre.objects.count()
        context['total_partos_mes'] = Parto.objects.filter(
            fecha_registro__month=timezone.now().month,
            fecha_registro__year=timezone.now().year
        ).count()

    return render(request, 'home.html', context)

@user_passes_test(es_supervisor)
def supervisor_dashboard(request):
    """
    Dashboard principal del supervisor
    """
    context = {
        'titulo': 'Dashboard Supervisor',
        'estadisticas_generales': obtener_estadisticas_generales(),
        'actividad_reciente': obtener_actividad_reciente(),
    }
    return render(request, 'supervisor/dashboard.html', context)

@user_passes_test(es_supervisor)
def supervisor_reportes(request):
    """
    Página principal de reportes para supervisor
    """
    context = {
        'titulo': 'Reportes REM A24 - Atención Obstétrica y del Recién Nacido',
        'secciones': [
            {
                'codigo': 'A',
                'nombre': 'INFORMACIÓN GENERAL DE PARTOS',
                'descripcion': 'Partos vaginales, cesáreas y complicaciones',
                'icono': 'fas fa-baby',
                'enlaces': [
                    {'nombre': 'Partos Vaginales', 'url': 'app:reporte_partos', 'parametros': '?tipo=vaginal'},
                    {'nombre': 'Cesáreas', 'url': 'app:reporte_partos', 'parametros': '?tipo=cesarea'},
                    {'nombre': 'Complicaciones', 'url': 'app:reporte_partos', 'parametros': '?tipo=complicaciones'},
                ]
            },
            {
                'codigo': 'B',
                'nombre': 'INTERRUPCIÓN VOLUNTARIA DEL EMBARAZO',
                'descripcion': 'IVE y programas de acompañamiento',
                'icono': 'fas fa-heart',
                'enlaces': [
                    {'nombre': 'IVE - Registro General', 'url': 'app:reporte_ive', 'parametros': ''},
                    {'nombre': 'Acompañamiento IVE', 'url': 'app:reporte_ive', 'parametros': '?seccion=acompanamiento'},
                ]
            },
            {
                'codigo': 'C',
                'nombre': 'MÉTODO ANTICONCEPTIVO AL ALTA',
                'descripcion': 'Métodos anticonceptivos prescritos al alta',
                'icono': 'fas fa-pills',
                'enlaces': [
                    {'nombre': 'Métodos Anticonceptivos', 'url': 'app:reporte_anticonceptivos', 'parametros': ''},
                ]
            },
            {
                'codigo': 'D',
                'nombre': 'INFORMACIÓN DE RECIÉN NACIDOS',
                'descripcion': 'Nacidos vivos y nacidos fallecidos',
                'icono': 'fas fa-baby-carry',
                'enlaces': [
                    {'nombre': 'Recién Nacidos Vivos', 'url': 'app:reporte_recien_nacidos', 'parametros': '?estado=vivo'},
                    {'nombre': 'Nacidos Fallecidos', 'url': 'app:reporte_recien_nacidos', 'parametros': '?estado=fallecido'},
                ]
            }
        ]
    }
    return render(request, 'supervisor/reportes.html', context)

@user_passes_test(es_supervisor)
def supervisor_auditoria(request):
    """
    Página principal de auditoría para supervisor
    """
    context = {
        'titulo': 'Sistema de Auditoría',
        'resumen_auditoria': obtener_resumen_auditoria(),
    }
    return render(request, 'supervisor/auditoria.html', context)

@user_passes_test(es_supervisor)
def supervisor_metricas(request):
    """
    Página de métricas con gráficos estadísticos
    """
    context = {
        'titulo': 'Métricas y Estadísticas',
        'metricas_generales': obtener_metricas_generales(),
    }
    return render(request, 'supervisor/metricas.html', context)

# === FUNCIONES AUXILIARES ===

def obtener_estadisticas_generales():
    """Obtiene estadísticas generales del sistema"""
    hoy = timezone.now()
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'total_usuarios': User.__class__.objects.filter(is_active=True).count(),
        'usuarios_nuevos_mes': User.__class__.objects.filter(
            date_joined__gte=inicio_mes, is_active=True
        ).count(),
        'total_madres': Madre.objects.count(),
        'madres_nuevas_mes': Madre.objects.filter(fecha_ingreso__gte=inicio_mes).count(),
        'total_partos': Parto.objects.count(),
        'partos_mes': Parto.objects.filter(fecha_registro__gte=inicio_mes).count(),
        'total_recien_nacidos': RecienNacido.objects.count(),
        'recien_nacidos_mes': RecienNacido.objects.filter(
            fecha_nacimiento__gte=inicio_mes
        ).count(),
        'total_altas': Alta.objects.count(),
        'altas_mes': Alta.objects.filter(fecha_alta__gte=inicio_mes).count(),
    }

def obtener_actividad_reciente():
    """Obtiene la actividad reciente del sistema"""
    ultimos_7_dias = timezone.now() - timedelta(days=7)
    
    return {
        'registros_auditoria': RegistroAuditoria.objects.filter(
            timestamp__gte=ultimos_7_dias
        ).count(),
        'usuarios_activos': RegistroAuditoria.objects.filter(
            timestamp__gte=ultimos_7_dias
        ).values('usuario').distinct().count(),
        'acciones_hoy': RegistroAuditoria.objects.filter(
            timestamp__date=timezone.now().date()
        ).count(),
    }

def obtener_resumen_auditoria():
    """Obtiene resumen de actividad de auditoría"""
    hoy = timezone.now()
    inicio_semana = hoy - timedelta(days=7)
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    return {
        'total_registros': RegistroAuditoria.objects.count(),
        'registros_semana': RegistroAuditoria.objects.filter(
            timestamp__gte=inicio_semana
        ).count(),
        'registros_mes': RegistroAuditoria.objects.filter(
            timestamp__gte=inicio_mes
        ).count(),
        'usuarios_activos': RegistroAuditoria.objects.filter(
            timestamp__gte=inicio_semana
        ).values('usuario').distinct().count(),
        'acciones_hoy': RegistroAuditoria.objects.filter(
            timestamp__date=hoy.date()
        ).count(),
    }

def obtener_metricas_generales():
    """Obtiene métricas para gráficos estadísticos"""
    hoy = timezone.now()
    inicio_año = hoy.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Datos mensuales del año actual
    datos_mensuales = []
    for mes in range(1, hoy.month + 1):
        fecha_inicio = hoy.replace(month=mes, day=1, hour=0, minute=0, second=0, microsecond=0)
        if mes == 12:
            fecha_fin = fecha_inicio.replace(year=fecha_inicio.year + 1, month=1)
        else:
            fecha_fin = fecha_inicio.replace(month=mes + 1)
        
        partos_mes = Parto.objects.filter(
            fecha_registro__gte=fecha_inicio,
            fecha_registro__lt=fecha_fin
        ).count()
        
        datos_mensuales.append({
            'mes': calendar.month_name[mes],
            'partos': partos_mes
        })
    
    # Tipos de parto
    tipos_parto = Parto.objects.values('tipo').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Estadísticas de recién nacidos
    stats_recien_nacidos = RecienNacido.objects.aggregate(
        peso_promedio=Avg('peso'),
        apgar_promedio=Avg('apgar_1_min'),
        total_vivos=Count('id', filter=Q(estado_vital='vivo')),
        total_fallecidos=Count('id', filter=Q(estado_vital='fallecido')),
    )
    
    return {
        'datos_mensuales': datos_mensuales,
        'tipos_parto': list(tipos_parto),
        'estadisticas_recien_nacidos': stats_recien_nacidos,
    }

# === VISTAS DE REPORTES ESPECÍFICOS ===

@user_passes_test(es_supervisor)
def reporte_partos(request):
    """
    Reporte de partos (Sección A del REM A24)
    """
    tipo_reporte = request.GET.get('tipo', 'todos')
    
    # Obtener datos de partos
    partos = Parto.objects.select_related('madre', 'creado_por').all()
    
    if tipo_reporte == 'vaginal':
        partos = partos.filter(tipo_parto='vaginal')
        titulo = "Partos Vaginales"
    elif tipo_reporte == 'cesarea':
        partos = partos.filter(tipo_parto='cesarea')
        titulo = "Cesáreas"
    elif tipo_reporte == 'complicaciones':
        # Aquí incluirías lógica para filtrar partos con complicaciones
        titulo = "Partos con Complicaciones"
    else:
        titulo = "Todos los Partos"
    
    # Aplicar filtros de fecha
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d')
            partos = partos.filter(fecha_registro__date__gte=fecha_desde.date())
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            partos = partos.filter(fecha_registro__date__lte=fecha_hasta.date())
        except ValueError:
            pass
    
    context = {
        'titulo': f"REM A24 - Sección A: {titulo}",
        'partos': partos,
        'tipo_reporte': tipo_reporte,
        'total_partos': partos.count(),
        'estadisticas': {
            'partos_vaginales': partos.filter(tipo_parto='vaginal').count(),
            'cesareas': partos.filter(tipo_parto='cesarea').count(),
            'partos_complicados': 0,  # Implementar lógica de complicaciones
        }
    }
    
    return render(request, 'supervisor/reportes/partos.html', context)

@user_passes_test(es_supervisor)
def reporte_ive(request):
    """
    Reporte de IVE (Sección B del REM A24)
    """
    seccion = request.GET.get('seccion', 'general')
    
    context = {
        'titulo': 'REM A24 - Sección B: Interrupción Voluntaria del Embarazo',
        'seccion': seccion,
        'mensaje': 'Funcionalidad de IVE en desarrollo',
    }
    
    return render(request, 'supervisor/reportes/ive.html', context)

@user_passes_test(es_supervisor)
def reporte_anticonceptivos(request):
    """
    Reporte de métodos anticonceptivos (Sección C del REM A24)
    """
    context = {
        'titulo': 'REM A24 - Sección C: Método Anticonceptivo al Alta',
        'mensaje': 'Funcionalidad de anticonceptivos en desarrollo',
    }
    
    return render(request, 'supervisor/reportes/anticonceptivos.html', context)

@user_passes_test(es_supervisor)
def reporte_recien_nacidos(request):
    """
    Reporte de recién nacidos (Sección D del REM A24)
    """
    estado = request.GET.get('estado', 'todos')
    
    recien_nacidos = RecienNacido.objects.select_related('parto__madre').all()
    
    if estado == 'vivo':
        recien_nacidos = recien_nacidos.filter(estado_vital='vivo')
        titulo = "Recién Nacidos Vivos"
    elif estado == 'fallecido':
        recien_nacidos = recien_nacidos.filter(estado_vital='fallecido')
        titulo = "Nacidos Fallecidos"
    else:
        titulo = "Todos los Recién Nacidos"
    
    context = {
        'titulo': f"REM A24 - Sección D: {titulo}",
        'recien_nacidos': recien_nacidos,
        'estado': estado,
        'total_recien_nacidos': recien_nacidos.count(),
        'estadisticas': {
            'vivos': recien_nacidos.filter(estado_vital='vivo').count(),
            'fallecidos': recien_nacidos.filter(estado_vital='fallecido').count(),
            'peso_promedio': recien_nacidos.aggregate(peso_avg=Avg('peso'))['peso_avg'],
        }
    }
    
    return render(request, 'supervisor/reportes/recien_nacidos.html', context)