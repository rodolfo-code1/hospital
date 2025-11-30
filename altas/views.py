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
    """Dashboard Clínico: Muestra pacientes hospitalizados agrupados por familia."""
    # Excluir a las madres que ya se fueron (Alta administrativa completa)
    pacientes = Madre.objects.exclude(
        estado_alta='alta_administrativa'
    ).prefetch_related(
        'partos__recien_nacidos'
    ).order_by('fecha_ingreso')
    
    return render(request, 'altas/panel_medico.html', {'pacientes': pacientes})

@login_required
@medico_requerido
def cambiar_estado_salud(request, tipo_paciente, pk):
    """Actualiza el semáforo de salud (Sano/Observación/Crítico)"""
    nuevo_estado = request.POST.get('estado_salud')
    
    if tipo_paciente == 'madre':
        paciente = get_object_or_404(Madre, pk=pk)
    else:
        paciente = get_object_or_404(RecienNacido, pk=pk)
    
    paciente.estado_salud = nuevo_estado
    paciente.save()
    
    messages.success(request, f'Estado de salud actualizado.')
    return redirect('altas:panel_medico')

# --- FLUJO DE ALTA ---

@login_required
def crear_alta(request):
    """Inicia el proceso de alta. Puede venir pre-llenado del panel médico."""
    initial_data = {}
    if request.GET.get('madre'): initial_data['madre'] = request.GET.get('madre')
    if request.GET.get('rn'): initial_data['recien_nacido'] = request.GET.get('rn')

    if request.method == 'POST':
        form = CrearAltaForm(request.POST)
        if form.is_valid():
            alta = form.save()
            alta.validar_registros()
            
            # Cambiar estado interno del paciente a "Alta Médica" (esperando cierre admin)
            if alta.madre:
                alta.madre.estado_alta = 'alta_medica'
                alta.madre.save()
            if alta.recien_nacido:
                alta.recien_nacido.estado_alta = 'alta_medica'
                alta.recien_nacido.save()
                
            messages.success(request, 'Alta generada. El paciente ha pasado a estado "Alta Médica".')
            
            # --- CAMBIO: Redirigir al Panel Médico en lugar del Detalle ---
            return redirect('altas:panel_medico') 
            # ------------------------------------------------------------
            
    else:
        form = CrearAltaForm(initial=initial_data)
    
    return render(request, 'altas/crear_alta.html', {'form': form, 'titulo': 'Generar Nueva Alta'})
    # --- LÓGICA PARA FILTRADO JS ---
    # Creamos un diccionario: { id_madre: [ {id: id_rn, nombre: "RN-..."} ] }
    rns_por_madre = {}
    partos_por_madre = {}
    
    # Solo consideramos RN sanos y hospitalizados para el mapa
    rns = RecienNacido.objects.filter(estado_alta='hospitalizado', estado_salud='sano').select_related('parto__madre')
    for rn in rns:
        madre_id = rn.parto.madre.id
        if madre_id not in rns_por_madre: rns_por_madre[madre_id] = []
        rns_por_madre[madre_id].append({'id': rn.id, 'nombre': str(rn)})
        
    partos = Parto.objects.all()
    for parto in partos:
        if parto.madre_id not in partos_por_madre: partos_por_madre[parto.madre_id] = []
        partos_por_madre[parto.madre_id].append({'id': parto.id, 'nombre': str(parto)})

    context = {
        'form': form, 
        'titulo': 'Generar Nueva Alta',
        # Convertimos a JSON string para usar en JS seguro
        'json_rns': json.dumps(rns_por_madre),
        'json_partos': json.dumps(partos_por_madre)
    }
    return render(request, 'altas/crear_alta.html', context)
@login_required
def lista_altas(request):
    altas = Alta.objects.all().select_related('madre', 'recien_nacido')
    form_buscar = BuscarAltaForm(request.GET or None)
    
    if form_buscar.is_valid():
        buscar = form_buscar.cleaned_data.get('buscar')
        estado = form_buscar.cleaned_data.get('estado')
        if buscar:
            altas = altas.filter(Q(madre__nombre__icontains=buscar) | Q(madre__rut__icontains=buscar))
        if estado:
            altas = altas.filter(estado=estado)
    
    context = {
        'altas': altas, 'form_buscar': form_buscar,
        'pendientes': altas.filter(estado='pendiente').count(),
        'completadas': altas.filter(estado='completada').count(),
    }
    return render(request, 'altas/lista_altas.html', context)

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
    if request.method == 'POST':
        form = ConfirmarAltaClinicaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_clinica(form.cleaned_data['medico_nombre'])
            if form.cleaned_data.get('observaciones_clinicas'):
                alta.observaciones += f"\n[Médico]: {form.cleaned_data['observaciones_clinicas']}"
                alta.save()
            messages.success(request, 'Alta clínica confirmada.')
            return redirect('altas:detalle_alta', pk=pk)
    else:
        form = ConfirmarAltaClinicaForm()
    return render(request, 'altas/confirmar_alta.html', {'alta': alta, 'form': form, 'tipo_confirmacion': 'clínica'})

@login_required
@rol_requerido('administrativo')
def confirmar_alta_administrativa(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if request.method == 'POST':
        form = ConfirmarAltaAdministrativaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_administrativa(form.cleaned_data['administrativo_nombre'])
            if form.cleaned_data.get('observaciones_administrativas'):
                alta.observaciones += f"\n[Admin]: {form.cleaned_data['observaciones_administrativas']}"
                alta.save()
            try:
                generar_certificado_pdf(alta)
                messages.info(request, 'Proceso completado y certificado generado.')
            except: pass
            return redirect('altas:detalle_alta', pk=pk)
    else:
        form = ConfirmarAltaAdministrativaForm()
    return render(request, 'altas/confirmar_alta.html', {'alta': alta, 'form': form, 'tipo_confirmacion': 'administrativa'})

@login_required
def historial_altas(request):
    altas = Alta.objects.filter(estado='completada').order_by('-fecha_alta')
    return render(request, 'altas/historial_altas.html', {'altas': altas, 'total': altas.count()})

@login_required
def exportar_excel(request):
    return exportar_altas_excel(Alta.objects.all())

@login_required
def descargar_certificado(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    return generar_certificado_pdf(alta)

@login_required
@medico_requerido
def alertas_clinicas(request):
    """Vista de alertas para el médico"""
    rn_criticos = RecienNacido.objects.filter(
        Q(apgar_1_min__lt=7) | Q(apgar_5_min__lt=7) | Q(peso__lt=2.5) | Q(peso__gt=4.0)
    ).select_related('parto', 'parto__madre').order_by('-fecha_registro')[:20]

    partos_complicados = Parto.objects.filter(
        tuvo_complicaciones=True
    ).select_related('madre').order_by('-fecha_hora_inicio')[:20]

    return render(request, 'altas/alertas_clinicas.html', {
        'rn_criticos': rn_criticos,
        'partos_complicados': partos_complicados,
    })