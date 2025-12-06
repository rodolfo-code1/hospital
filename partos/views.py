from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from .models import Parto, Aborto
from pacientes.models import Madre
from recien_nacidos.models import RecienNacido
from .forms import PartoForm, DerivacionAbortoForm, ResolverAbortoForm, FiltroTurnoForm
from usuarios.decorators import rol_requerido, medico_requerido
# ==========================================
# GESTIÓN DE PARTOS (MATRONA)
# ==========================================

@login_required
def registrar_parto(request):
    """Vista para registrar un nuevo parto"""
    if request.method == 'POST':
        form = PartoForm(request.POST)
        if form.is_valid():
            parto = form.save(commit=False)
            parto.creado_por = request.user  # Asigna la matrona actual
            parto.save()
            
            messages.success(
                request,
                f'Parto registrado exitosamente para {parto.madre.nombre}'
            )
            return redirect('app:home')
        else:
            # --- NUEVO: NOTIFICACIÓN DE ERROR ---
            # Si la validación clean_madre falla (ya tiene parto o aborto), mostramos la alerta aquí
            if 'madre' in form.errors:
                messages.error(request, f"⛔ ERROR: {form.errors['madre'][0]}")
            else:
                messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = PartoForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Parto',
        'subtitulo': 'Registro del proceso de parto'
    }
    return render(request, 'partos/registrar_parto.html', context)


@login_required
@rol_requerido('matrona')
def mis_registros_clinicos(request):
    """
    Panel de Turno: Muestra registros por usuario, fecha y turno específico.
    Permite navegar al pasado.
    """
    # Valores por defecto (Ahora)
    ahora = timezone.localtime(timezone.now())
    fecha_seleccionada = ahora.date()
    
    # Determinar turno actual por defecto
    if 8 <= ahora.hour < 20:
        turno_seleccionado = 'dia'
    else:
        turno_seleccionado = 'noche'
        # Si es madrugada (00:00 - 08:00), el turno pertenece a la fecha de "ayer"
        if ahora.hour < 8:
            fecha_seleccionada = ahora.date() - timedelta(days=1)

    # Procesar formulario de filtro si viene en la URL (GET)
    form_filtro = FiltroTurnoForm(request.GET or None)
    
    if form_filtro.is_valid():
        if form_filtro.cleaned_data['fecha']:
            fecha_seleccionada = form_filtro.cleaned_data['fecha']
        if form_filtro.cleaned_data['turno']:
            turno_seleccionado = form_filtro.cleaned_data['turno']
    else:
        # Pre-llenar formulario con los defaults calculados
        form_filtro = FiltroTurnoForm(initial={'fecha': fecha_seleccionada, 'turno': turno_seleccionado})

    # Calcular rangos exactos según la selección
    # Usamos la fecha seleccionada como base
    base_time = timezone.datetime.combine(fecha_seleccionada, timezone.datetime.min.time())
    base_time = timezone.make_aware(base_time)

    if turno_seleccionado == 'dia':
        inicio_turno = base_time.replace(hour=8, minute=0)
        fin_turno = base_time.replace(hour=20, minute=0)
        nombre_turno = "Día"
    else: # Noche
        inicio_turno = base_time.replace(hour=20, minute=0)
        # El turno noche termina al día siguiente
        fin_turno = (base_time + timedelta(days=1)).replace(hour=8, minute=0)
        nombre_turno = "Noche"

    # Consultas filtradas
    madres = Madre.objects.filter(
        creado_por=request.user,
        fecha_ingreso__range=(inicio_turno, fin_turno)
    ).order_by('-fecha_ingreso')

    partos = Parto.objects.filter(
        creado_por=request.user,
        fecha_registro__range=(inicio_turno, fin_turno)
    ).select_related('madre').order_by('-fecha_registro')

    rns = RecienNacido.objects.filter(
        creado_por=request.user,
        fecha_registro__range=(inicio_turno, fin_turno)
    ).select_related('parto__madre').order_by('-fecha_registro')

    abortos = Aborto.objects.filter(
        matrona_derivadora=request.user,
        fecha_derivacion__range=(inicio_turno, fin_turno)
    ).select_related('madre').order_by('-fecha_derivacion')

    stats = {
        'total_madres': madres.count(),
        'total_partos': partos.count(),
        'total_rns': rns.count(),
        'total_abortos': abortos.count(),
    }

    context = {
        'form_filtro': form_filtro, # Enviamos el form a la plantilla
        'nombre_turno': nombre_turno,
        'fecha_actual': fecha_seleccionada,
        'inicio_turno': inicio_turno,
        'fin_turno': fin_turno,
        'madres': madres,
        'partos': partos,
        'rns': rns,
        'abortos': abortos,
        'stats': stats
    }
    
    return render(request, 'partos/mi_turno.html', context)
# ==========================================
# GESTIÓN DE ABORTOS / IVE
# ==========================================

@login_required
@rol_requerido('matrona')
def derivar_aborto(request):
    """Matrona deriva un caso sospechoso o solicitud IVE al médico"""
    if request.method == 'POST':
        form = DerivacionAbortoForm(request.POST)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.matrona_derivadora = request.user
            caso.save()
            
            # Cambiar estado salud de madre a Observación automáticamente
            caso.madre.estado_salud = 'observacion'
            caso.madre.save()
            
            messages.warning(request, f'Caso derivado al equipo médico. Paciente: {caso.madre.nombre}')
            return redirect('app:home')
        else:
            # --- NUEVO: NOTIFICACIÓN DE ERROR DE BLOQUEO ---
            # Si clean_madre falla (ya tiene parto o aborto), avisa fuerte a la matrona
            if 'madre' in form.errors:
                messages.error(request, f"⛔ NO SE PUEDE DERIVAR: {form.errors['madre'][0]}")
            else:
                messages.error(request, "Error en el formulario.")
    else:
        form = DerivacionAbortoForm()
    
    return render(request, 'partos/derivar_aborto.html', {'form': form})


@login_required
@medico_requerido
def panel_abortos(request):
    """Médico ve la lista de casos derivados pendientes"""
    casos = Aborto.objects.filter(estado='derivado').order_by('-fecha_derivacion')
    return render(request, 'partos/panel_abortos.html', {'casos': casos})


@login_required
@medico_requerido
def resolver_aborto(request, pk):
    """
    Médico confirma el diagnóstico y procedimiento.
    Al terminar, redirige al PANEL PRINCIPAL.
    """
    caso = get_object_or_404(Aborto, pk=pk)
    
    if request.method == 'POST':
        form = ResolverAbortoForm(request.POST, instance=caso)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.medico_responsable = request.user
            caso.fecha_resolucion = timezone.now()
            caso.estado = 'confirmado'
            caso.save()
            
            # La paciente queda en observación para evaluación posterior en sala
            caso.madre.estado_salud = 'observacion'
            caso.madre.save()
            
            messages.success(request, 'Procedimiento registrado. Paciente derivada a Sala de Hospitalización (Observación).')
            
            # Volver al Panel Principal
            return redirect('app:home')
    else:
        form = ResolverAbortoForm(instance=caso)
    
    return render(request, 'partos/resolver_aborto.html', {'form': form, 'caso': caso})