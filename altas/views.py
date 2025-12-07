from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Prefetch
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from .forms import (
    CrearAltaForm, ConfirmarAltaClinicaForm, ConfirmarAltaAdministrativaForm, BuscarAltaForm
)
from .utils import generar_certificado_pdf, exportar_altas_excel
from usuarios.decorators import rol_requerido, medico_requerido
import json

# --- PANEL MÉDICO & ESTADOS ---

@login_required
@medico_requerido
def panel_medico(request):
    """
    Dashboard Clínico para Médicos.
    Muestra estadísticas de flujo y pacientes en sala.
    """
    # 1. ESTADÍSTICAS
    en_proceso = Alta.objects.filter(alta_clinica_confirmada=False).count()
    por_firmar = Alta.objects.filter(registros_completos=True, alta_clinica_confirmada=False).count()
    pendientes_cierre = Alta.objects.filter(alta_clinica_confirmada=True).exclude(estado='completada').count()
    completadas = Alta.objects.filter(estado='completada').count()

    stats = {
        'en_proceso': en_proceso,
        'por_firmar': por_firmar,
        'pendientes': pendientes_cierre,
        'completadas': completadas
    }

    # 2. PACIENTES EN SALA
    pacientes = Madre.objects.exclude(
        estado_alta='alta_administrativa'
    ).prefetch_related(
        'partos__recien_nacidos'
    ).order_by('fecha_ingreso')

    context = {
        'pacientes': pacientes,
        'stats': stats
    }
    return render(request, 'altas/panel_medico.html', context)

@login_required
@medico_requerido
def cambiar_estado_salud(request, tipo_paciente, pk):
    """
    Actualiza el semáforo de salud (Sano/Observación/Crítico).
    INCLUYE RESTRICCIÓN DE SEGURIDAD: No permite pasar a 'sano' si hay alertas pendientes.
    """
    nuevo_estado = request.POST.get('estado_salud')
    
    if tipo_paciente == 'madre':
        paciente = get_object_or_404(Madre, pk=pk)
        
        # --- VALIDACIÓN DE SEGURIDAD (MADRE) ---
        if nuevo_estado == 'sano':
            # Verificar si tiene algún parto con complicaciones NO revisado
            complicaciones_sin_revisar = paciente.partos.filter(
                tuvo_complicaciones=True,
                alerta_revisada=False
            ).exists()
            
            if complicaciones_sin_revisar:
                messages.error(request, "⛔ ACCIÓN DENEGADA: La paciente tiene complicaciones de parto pendientes de revisión. Verifique el Panel de Alertas.")
                return redirect('altas:panel_medico')
        # ---------------------------------------
        
    else:
        paciente = get_object_or_404(RecienNacido, pk=pk)
        
        # --- VALIDACIÓN DE SEGURIDAD (RN) ---
        if nuevo_estado == 'sano':
            # Verificar si tiene criterios de riesgo (APGAR/Peso)
            es_riesgoso = (
                paciente.apgar_1_min < 7 or 
                paciente.apgar_5_min < 7 or 
                paciente.peso < 2.5 or 
                paciente.peso > 4.0
            )
            
            # Si es riesgoso y el médico NO ha marcado el "Check" de revisado
            if es_riesgoso and not paciente.alerta_revisada:
                messages.error(request, "⛔ ACCIÓN DENEGADA: El Recién Nacido tiene criterios de riesgo. Debe validar la alerta clínica antes de dar el alta.")
                return redirect('altas:panel_medico')
        # ------------------------------------
    
    # Si pasa las validaciones, guardamos el cambio
    paciente.estado_salud = nuevo_estado
    paciente.save()
    
    messages.success(request, f'Estado actualizado a {paciente.get_estado_salud_display()}.')
    return redirect('altas:panel_medico')


# --- ALERTAS CLÍNICAS ---

@login_required
@medico_requerido
def marcar_alerta_revisada(request, tipo, pk):
    """Marca una alerta como revisada."""
    if tipo == 'parto':
        obj = get_object_or_404(Parto, pk=pk)
    elif tipo == 'rn':
        obj = get_object_or_404(RecienNacido, pk=pk)
    
    obj.alerta_revisada = True
    obj.save()
    
    messages.success(request, 'Alerta marcada como revisada.')
    return redirect('altas:alertas_clinicas')

@login_required
@medico_requerido
def alertas_clinicas(request):
    """Vista de alertas (Solo muestra las NO revisadas)"""
    rn_criticos = RecienNacido.objects.filter(
        alerta_revisada=False
    ).filter(
        Q(apgar_1_min__lt=7) | Q(apgar_5_min__lt=7) | Q(peso__lt=2.5) | Q(peso__gt=4.0)
    ).select_related('parto', 'parto__madre').order_by('-fecha_registro')

    partos_complicados = Parto.objects.filter(
        tuvo_complicaciones=True,
        alerta_revisada=False
    ).select_related('madre').order_by('-fecha_hora_inicio')

    return render(request, 'altas/alertas_clinicas.html', {
        'rn_criticos': rn_criticos,
        'partos_complicados': partos_complicados,
    })


# --- FLUJO DE ALTA ---

@login_required
def crear_alta(request):
    initial_data = {}
    if request.GET.get('madre'): initial_data['madre'] = request.GET.get('madre')
    if request.GET.get('rn'): initial_data['recien_nacido'] = request.GET.get('rn')

    if request.method == 'POST':
        form = CrearAltaForm(request.POST)
        if form.is_valid():
            alta = form.save()
            alta.validar_registros()
            
            if alta.madre:
                alta.madre.estado_alta = 'alta_medica'
                alta.madre.save()
            if alta.recien_nacido:
                alta.recien_nacido.estado_alta = 'alta_medica'
                alta.recien_nacido.save()
                
            # Auto-firma para médicos
            if request.user.rol == 'medico' or request.user.rol == 'jefatura':
                alta.medico_confirma = request.user.get_full_name() or request.user.username
                alta.alta_clinica_confirmada = True
                alta.estado = 'alta_clinica'
                alta.save()
                messages.success(request, 'Alta generada y firmada automáticamente.')
            else:
                messages.success(request, 'Alta generada pendiente de firma.')
                
            return redirect('altas:panel_medico')
    else:
        form = CrearAltaForm(initial=initial_data)
    
    # Datos para JS
    rns_por_madre = {}
    partos_por_madre = {}
    
    rns = RecienNacido.objects.filter(estado_alta='hospitalizado', estado_salud='sano').select_related('parto__madre')
    for rn in rns:
        madre_id = rn.parto.madre.id
        if madre_id not in rns_por_madre: rns_por_madre[madre_id] = []
        rns_por_madre[madre_id].append({'id': rn.id, 'nombre': str(rn)})
        
    partos = Parto.objects.filter(estado_alta='hospitalizado')
    for parto in partos:
        if parto.madre_id not in partos_por_madre: partos_por_madre[parto.madre_id] = []
        partos_por_madre[parto.madre_id].append({'id': parto.id, 'nombre': str(parto)})

    context = {
        'form': form, 
        'titulo': 'Generar Nueva Alta',
        'json_rns': json.dumps(rns_por_madre),
        'json_partos': json.dumps(partos_por_madre)
    }
    return render(request, 'altas/crear_alta.html', context)

@login_required
def lista_altas(request):
    altas = Alta.objects.all().select_related('madre', 'recien_nacido').order_by('-fecha_creacion')
    form_buscar = BuscarAltaForm(request.GET or None)
    
    if form_buscar.is_valid():
        buscar = form_buscar.cleaned_data.get('buscar')
        estado = form_buscar.cleaned_data.get('estado')
        if buscar:
            altas = altas.filter(Q(madre__nombre__icontains=buscar) | Q(madre__rut__icontains=buscar))
        if estado:
            altas = altas.filter(estado=estado)
    
    # Estadísticas para la lista
    qs_global = Alta.objects.all()
    stats = {
        'en_proceso': qs_global.exclude(estado='completada').count(),
        'firma_medica': qs_global.filter(registros_completos=True, alta_clinica_confirmada=False).count(),
        'cierre_admin': qs_global.filter(alta_clinica_confirmada=True, alta_administrativa_confirmada=False).count(),
        'completadas': qs_global.filter(estado='completada').count()
    }
    
    return render(request, 'altas/lista_altas.html', {'altas': altas, 'form_buscar': form_buscar, 'stats': stats})

@login_required
def detalle_alta(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if request.method == 'POST' and 'validar' in request.POST:
        if alta.validar_registros():
            messages.success(request, 'Registros validados.')
        else:
            messages.warning(request, f'Incompleto: {alta.observaciones_validacion}')
        return redirect('altas:detalle_alta', pk=pk)
    
    return render(request, 'altas/detalle_alta.html', {
        'alta': alta,
        'puede_confirmar_clinica': alta.puede_confirmar_alta_clinica(),
        'puede_confirmar_administrativa': alta.puede_confirmar_alta_administrativa(),
    })

@login_required
@medico_requerido
def confirmar_alta_clinica(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if not alta.puede_confirmar_alta_clinica():
        return redirect('altas:detalle_alta', pk=pk)
    
    nombre = request.user.get_full_name() or request.user.username
    if request.method == 'POST':
        form = ConfirmarAltaClinicaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_clinica(nombre)
            alta.se_entrego_anticonceptivo = form.cleaned_data.get('se_entrego_anticonceptivo')
            alta.metodo_anticonceptivo = form.cleaned_data.get('metodo_anticonceptivo')
            if form.cleaned_data.get('observaciones_clinicas'):
                alta.observaciones += f"\n[Med]: {form.cleaned_data['observaciones_clinicas']}"
            alta.save()
            messages.success(request, 'Alta firmada.')
            return redirect('altas:detalle_alta', pk=pk)
    else:
        form = ConfirmarAltaClinicaForm(initial={'medico_nombre': nombre})
    return render(request, 'altas/confirmar_alta.html', {'alta': alta, 'form': form, 'tipo_confirmacion': 'clínica'})

@login_required
@rol_requerido('administrativo')
def confirmar_alta_administrativa(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if not alta.puede_confirmar_alta_administrativa():
        return redirect('altas:detalle_alta', pk=pk)
    
    nombre = request.user.get_full_name() or request.user.username
    if request.method == 'POST':
        form = ConfirmarAltaAdministrativaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_administrativa(nombre)
            if form.cleaned_data.get('observaciones_administrativas'):
                alta.observaciones += f"\n[Admin]: {form.cleaned_data['observaciones_administrativas']}"
            alta.save()
            return redirect('altas:detalle_alta', pk=pk)
    else:
        form = ConfirmarAltaAdministrativaForm(initial={'administrativo_nombre': nombre})
    return render(request, 'altas/confirmar_alta.html', {'alta': alta, 'form': form, 'tipo_confirmacion': 'administrativa'})

@login_required
def historial_altas(request):
    altas = Alta.objects.all().order_by('-fecha_creacion')
    # Recalcular stats para historial
    en_proceso = altas.filter(alta_clinica_confirmada=False).count()
    pendientes = altas.filter(alta_clinica_confirmada=True, alta_administrativa_confirmada=False).count()
    completadas = altas.filter(estado='completada').count()
    
    stats = {'total': altas.count(), 'en_proceso': en_proceso, 'pendientes': pendientes, 'completadas': completadas}
    return render(request, 'altas/historial_altas.html', {'altas': altas, 'stats': stats})

@login_required
def exportar_excel(request):
    return exportar_altas_excel(Alta.objects.all())

@login_required
@rol_requerido('administrativo', 'supervisor') 
def descargar_certificado(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    return generar_certificado_pdf(alta)