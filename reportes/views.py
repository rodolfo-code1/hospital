from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from altas.models import Alta
from usuarios.models import AuditoriaLogin, AuditoriaModificacion
from usuarios.decorators import supervisor_requerido

# ==========================================
# VISTAS DE REPORTES PARA SUPERVISOR
# ==========================================

@login_required
@supervisor_requerido
def dashboard_reportes(request):
    """Dashboard principal de reportes"""
    # El dashboard principal ahora redirige al panel de supervisor (home)
    return redirect('app:home')

@login_required
@supervisor_requerido
def reporte_seccion_a(request):
    """Sección A: Información General de Partos (REM)"""
    # Filtros de rango de fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    partos = Parto.objects.all()
    
    if fecha_inicio:
        partos = partos.filter(fecha_hora_inicio__gte=fecha_inicio)
    if fecha_fin:
        partos = partos.filter(fecha_hora_inicio__lte=fecha_fin)
    
    # Estadísticas de partos
    total_partos = partos.count()
    partos_por_tipo = list(partos.values('tipo').annotate(count=Count('id')))
    partos_con_complicaciones = partos.filter(tuvo_complicaciones=True).count()
    
    # Calcular porcentajes
    for p in partos_por_tipo:
        p['porcentaje'] = round((p['count'] / total_partos * 100) if total_partos > 0 else 0, 1)
    
    porcentaje_complicaciones = round((partos_con_complicaciones / total_partos * 100) if total_partos > 0 else 0, 1)
    
    context = {
        'total_partos': total_partos,
        'partos_por_tipo': partos_por_tipo,
        'partos_con_complicaciones': partos_con_complicaciones,
        'porcentaje_complicaciones': porcentaje_complicaciones,
        'partos': partos[:20],  # Mostrar últimos 20
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'reportes/seccion_a.html', context)

@login_required
@supervisor_requerido
def reporte_seccion_b(request):
    """Sección B: Interrupción del Embarazo"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    abortos = Aborto.objects.all()
    
    if fecha_inicio:
        abortos = abortos.filter(fecha_derivacion__gte=fecha_inicio)
    if fecha_fin:
        abortos = abortos.filter(fecha_derivacion__lte=fecha_fin)
    
    # Estadísticas de abortos
    total_abortos = abortos.count()
    abortos_por_tipo = list(abortos.values('tipo').annotate(count=Count('id')))
    abortos_confirmados = abortos.filter(estado='confirmado').count()
    abortos_por_causal = list(abortos.values('causal').annotate(count=Count('id')))
    
    # Calcular porcentajes
    porcentaje_confirmado = round((abortos_confirmados / total_abortos * 100) if total_abortos > 0 else 0, 1)
    
    context = {
        'total_abortos': total_abortos,
        'abortos_por_tipo': abortos_por_tipo,
        'abortos_confirmados': abortos_confirmados,
        'porcentaje_confirmado': porcentaje_confirmado,
        'abortos_por_causal': abortos_por_causal,
        'abortos': abortos[:20],
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'reportes/seccion_b.html', context)

@login_required
@supervisor_requerido
def reporte_seccion_c(request):
    """Sección C: Métodos Anticonceptivos al Alta"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    altas = Alta.objects.filter(madre__isnull=False)
    
    if fecha_inicio:
        altas = altas.filter(fecha_creacion__gte=fecha_inicio)
    if fecha_fin:
        altas = altas.filter(fecha_creacion__lte=fecha_fin)
    
    # Estadísticas de anticoncepción
    total_altas_madre = altas.count()
    altas_con_anticonceptivo = altas.filter(se_entrego_anticonceptivo=True).count()
    metodos_entregados = list(altas.filter(se_entrego_anticonceptivo=True).values('metodo_anticonceptivo').annotate(count=Count('id')))
    
    # Calcular porcentaje cobertura
    porcentaje_cobertura = round((altas_con_anticonceptivo / total_altas_madre * 100) if total_altas_madre > 0 else 0, 1)
    
    # Agregar porcentajes a metodos
    for m in metodos_entregados:
        m['porcentaje'] = round((m['count'] / altas_con_anticonceptivo * 100) if altas_con_anticonceptivo > 0 else 0, 1)
    
    context = {
        'total_altas_madre': total_altas_madre,
        'altas_con_anticonceptivo': altas_con_anticonceptivo,
        'metodos_entregados': metodos_entregados,
        'porcentaje_cobertura': porcentaje_cobertura,
        'altas': altas[:20],
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'reportes/seccion_c.html', context)

@login_required
@supervisor_requerido
def reporte_seccion_d(request):
    """Sección D: Información de Recién Nacidos"""
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    rn = RecienNacido.objects.all()
    
    if fecha_inicio:
        rn = rn.filter(fecha_registro__gte=fecha_inicio)
    if fecha_fin:
        rn = rn.filter(fecha_registro__lte=fecha_fin)
    
    # Estadísticas de recién nacidos
    total_rn = rn.count()
    rn_masculino = rn.filter(sexo='M').count()
    rn_femenino = rn.filter(sexo='F').count()
    
    # APGAR bajo (< 7 en 1 min o 5 min)
    rn_apgar_bajo = rn.filter(Q(apgar_1_min__lt=7) | Q(apgar_5_min__lt=7)).count()
    
    # Peso
    peso_promedio = rn.aggregate(Avg('peso'))['peso__avg']
    rn_bajo_peso = rn.filter(peso__lt=2.5).count()
    rn_macrosomia = rn.filter(peso__gt=4.0).count()
    
    # Lactancia y atención inmediata
    lactancia_precoz = rn.filter(lactancia_precoz=True).count()
    apego_piel_a_piel = rn.filter(apego_piel_a_piel=True).count()
    
    # Calcular porcentajes
    porcentaje_apgar_bajo = round((rn_apgar_bajo / total_rn * 100) if total_rn > 0 else 0, 1)
    porcentaje_bajo_peso = round((rn_bajo_peso / total_rn * 100) if total_rn > 0 else 0, 1)
    porcentaje_macrosomia = round((rn_macrosomia / total_rn * 100) if total_rn > 0 else 0, 1)
    porcentaje_lactancia = round((lactancia_precoz / total_rn * 100) if total_rn > 0 else 0, 1)
    porcentaje_apego = round((apego_piel_a_piel / total_rn * 100) if total_rn > 0 else 0, 1)
    
    context = {
        'total_rn': total_rn,
        'rn_masculino': rn_masculino,
        'rn_femenino': rn_femenino,
        'rn_apgar_bajo': rn_apgar_bajo,
        'porcentaje_apgar_bajo': porcentaje_apgar_bajo,
        'peso_promedio': round(peso_promedio, 3) if peso_promedio else 0,
        'rn_bajo_peso': rn_bajo_peso,
        'porcentaje_bajo_peso': porcentaje_bajo_peso,
        'rn_macrosomia': rn_macrosomia,
        'porcentaje_macrosomia': porcentaje_macrosomia,
        'lactancia_precoz': lactancia_precoz,
        'porcentaje_lactancia': porcentaje_lactancia,
        'apego_piel_a_piel': apego_piel_a_piel,
        'porcentaje_apego': porcentaje_apego,
        'rn': rn[:20],
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    
    return render(request, 'reportes/seccion_d.html', context)

@login_required
@supervisor_requerido
def metricas_generales(request):
    """Métricas generales del sistema"""
    # Rango de fechas
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Por defecto: últimos 30 días
    if not fecha_inicio:
        fecha_inicio = (timezone.now() - timedelta(days=30)).date()
    if not fecha_fin:
        fecha_fin = timezone.now().date()
    
    # Partos
    partos = Parto.objects.filter(fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin])
    total_partos = partos.count()
    
    # Recién nacidos
    rn = RecienNacido.objects.filter(fecha_registro__date__range=[fecha_inicio, fecha_fin])
    total_rn = rn.count()
    
    # Altas
    altas_madre = Alta.objects.filter(
        madre__isnull=False,
        fecha_creacion__date__range=[fecha_inicio, fecha_fin]
    )
    altas_rn = Alta.objects.filter(
        recien_nacido__isnull=False,
        fecha_creacion__date__range=[fecha_inicio, fecha_fin]
    )
    total_altas_madre = altas_madre.count()
    total_altas_rn = altas_rn.count()
    
    # Abortos
    abortos = Aborto.objects.filter(fecha_derivacion__date__range=[fecha_inicio, fecha_fin])
    total_abortos = abortos.count()
    
    # Calcular indicadores
    razon_rn_parto = round((total_rn / total_partos) if total_partos > 0 else 0, 2)
    tasa_aborto = round((total_abortos / (total_partos + total_abortos) * 100) if (total_partos + total_abortos) > 0 else 0, 1)
    porcentaje_altas = round((total_altas_madre / total_partos * 100) if total_partos > 0 else 0, 1)
    dias_periodo = (timezone.now().date() - fecha_inicio).days + 1
    promedio_rn_dia = round((total_rn / dias_periodo) if dias_periodo > 0 else 0, 1)
    
    context = {
        'total_partos': total_partos,
        'total_rn': total_rn,
        'total_altas_madre': total_altas_madre,
        'total_altas_rn': total_altas_rn,
        'total_abortos': total_abortos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'razon_rn_parto': razon_rn_parto,
        'tasa_aborto': tasa_aborto,
        'porcentaje_altas': porcentaje_altas,
        'promedio_rn_dia': promedio_rn_dia,
    }
    
    return render(request, 'reportes/metricas_generales.html', context)

@login_required
@supervisor_requerido
def auditoria_view(request):
    """Vista de auditoría completa"""
    # Auditoría de logins
    auditorias_login = AuditoriaLogin.objects.all().select_related('usuario')[:100]
    
    # Auditoría de modificaciones
    auditorias_modificacion = AuditoriaModificacion.objects.all().select_related('usuario')[:100]
    
    # Filtros
    tipo_auditoria = request.GET.get('tipo', 'login')  # login o modificacion
    usuario_id = request.GET.get('usuario')
    
    if tipo_auditoria == 'modificacion':
        auditorias = auditorias_modificacion
        if usuario_id:
            auditorias = auditorias.filter(usuario_id=usuario_id)
    else:
        auditorias = auditorias_login
        if usuario_id:
            auditorias = auditorias.filter(usuario_id=usuario_id)
    
    # Estadísticas
    total_logins = AuditoriaLogin.objects.filter(exitoso=True).count()
    total_logins_fallidos = AuditoriaLogin.objects.filter(exitoso=False).count()
    total_modificaciones = AuditoriaModificacion.objects.count()
    
    context = {
        'auditorias': auditorias[:100],
        'tipo_auditoria': tipo_auditoria,
        'total_logins': total_logins,
        'total_logins_fallidos': total_logins_fallidos,
        'total_modificaciones': total_modificaciones,
    }
    
    return render(request, 'reportes/auditoria.html', context)