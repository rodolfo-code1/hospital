# hospital/partos/views.py
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
from usuarios.models import Usuario
from app.models import Notificacion

# ==========================================
# GESTIÓN DE PARTOS (MATRONA)
# ==========================================

@login_required
def registrar_parto(request):
    """
    Vista para registrar el nacimiento de un bebé.
    Asocia automáticamente a la matrona logueada como creadora del registro.
    """
    if request.method == 'POST':
        form = PartoForm(request.POST)
        if form.is_valid():
            parto = form.save(commit=False)
            parto.creado_por = request.user  # Auditoría automática
            parto.save()
            
            messages.success(
                request,
                f'Parto registrado exitosamente para {parto.madre.nombre}'
            )
            # Redirige al home para continuar con el registro del recién nacido
            return redirect('app:home')
        else:
            # Manejo de errores específicos del campo 'madre' (ej: duplicados)
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
    Panel 'Mi Turno' para Matronas.
    
    Objetivo: Mostrar TODO el trabajo realizado por la matrona en un turno específico.
    Desafío: Incluir no solo los registros creados, sino también las fichas que editó.
    
    Lógica de Turnos:
    - Día: 08:00 a 20:00 del mismo día.
    - Noche: 20:00 del día actual a 08:00 del día siguiente.
    """
    # 1. Configuración Inicial (Defaults: Turno actual)
    ahora = timezone.localtime(timezone.now())
    fecha_seleccionada = ahora.date()
    
    # Cálculo automático del turno actual
    if 8 <= ahora.hour < 20:
        turno_seleccionado = 'dia'
    else:
        turno_seleccionado = 'noche'
        # Si es madrugada (ej: 03:00 AM), el turno pertenece administrativamente a "ayer"
        if ahora.hour < 8:
            fecha_seleccionada = ahora.date() - timedelta(days=1)

    # 2. Procesar Formulario de Filtro (si el usuario cambia la fecha)
    form_filtro = FiltroTurnoForm(request.GET or None)
    if form_filtro.is_valid():
        if form_filtro.cleaned_data['fecha']:
            fecha_seleccionada = form_filtro.cleaned_data['fecha']
        if form_filtro.cleaned_data['turno']:
            turno_seleccionado = form_filtro.cleaned_data['turno']
    else:
        # Pre-llenar formulario con los valores por defecto calculados
        form_filtro = FiltroTurnoForm(initial={'fecha': fecha_seleccionada, 'turno': turno_seleccionado})

    # 3. Calcular Rango Horario Exacto para la base de datos
    base_time = timezone.datetime.combine(fecha_seleccionada, timezone.datetime.min.time())
    base_time = timezone.make_aware(base_time)

    if turno_seleccionado == 'dia':
        inicio_turno = base_time.replace(hour=8, minute=0)
        fin_turno = base_time.replace(hour=20, minute=0)
        nombre_turno = "Día"
    else: 
        inicio_turno = base_time.replace(hour=20, minute=0)
        fin_turno = (base_time + timedelta(days=1)).replace(hour=8, minute=0)
        nombre_turno = "Noche"

    # ========================================================
    # 4. CONSULTAS FILTRADAS (Lógica Combinada)
    # ========================================================
    
    # A. MADRES (Ingresos o Ediciones)
    # Buscamos en el HISTORIAL (auditoría) para encontrar pacientes que la matrona
    # tocó (editó/creó) durante este rango de horas, aunque no sea la "creadora" original.
    ids_madres_gestionadas = Madre.history.filter(
        history_user=request.user,
        history_date__range=(inicio_turno, fin_turno)
    ).values_list('id', flat=True).distinct()
    
    madres = Madre.objects.filter(id__in=ids_madres_gestionadas).order_by('-fecha_actualizacion')

    # B. PARTOS (Creados directamente por ella)
    partos = Parto.objects.filter(
        creado_por=request.user,
        fecha_registro__range=(inicio_turno, fin_turno)
    ).select_related('madre').order_by('-fecha_registro')

    # C. RECIÉN NACIDOS (Creados directamente por ella)
    rns = RecienNacido.objects.filter(
        creado_por=request.user,
        fecha_registro__range=(inicio_turno, fin_turno)
    ).select_related('parto__madre').order_by('-fecha_registro')

    # D. DERIVACIONES DE ABORTO (Realizadas por ella)
    abortos = Aborto.objects.filter(
        matrona_derivadora=request.user,
        fecha_derivacion__range=(inicio_turno, fin_turno)
    ).select_related('madre').order_by('-fecha_derivacion')

    # 5. Estadísticas para tarjetas resumen
    stats = {
        'total_madres': madres.count(),
        'total_partos': partos.count(),
        'total_rns': rns.count(),
        'total_abortos': abortos.count(),
    }

    context = {
        'form_filtro': form_filtro,
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
    """
    Paso 1: Matrona detecta y deriva un caso sospechoso o solicitud IVE.
    
    Acciones Críticas:
    1. Crea el registro de derivación.
    2. Cambia el estado de salud de la madre a 'Observación' (bloquea el alta).
    3. Envía una NOTIFICACIÓN URGENTE a todos los médicos disponibles.
    """
    if request.method == 'POST':
        form = DerivacionAbortoForm(request.POST)
        if form.is_valid():
            caso = form.save(commit=False)
            caso.matrona_derivadora = request.user
            caso.save()
            
            # 1. Bloqueo preventivo de alta (Estado Observación)
            caso.madre.estado_salud = 'observacion'
            caso.madre.save()
            
            # --- 2. SISTEMA DE ALERTA MÉDICA ---
            medicos = Usuario.objects.filter(rol='medico')
            notificaciones = []
            
            mensaje_alerta = f"Paciente: {caso.madre.nombre} ({caso.madre.rut})\nMotivo: {caso.observacion_matrona}"
            
            # Enviamos a TODOS los médicos para asegurar respuesta rápida
            for medico in medicos:
                notificaciones.append(Notificacion(
                    usuario=medico,
                    titulo="🚨 DERIVACIÓN URGENTE: IVE/ABORTO",
                    mensaje=mensaje_alerta,
                    tipo='urgente',
                    link=f"/partos/resolver-ive/{caso.pk}/" # Link directo a la resolución
                ))
            
            Notificacion.objects.bulk_create(notificaciones)
            # --------------------------------------
            
            messages.warning(request, f'Caso derivado. Se ha enviado una ALERTA a todo el equipo médico.')
            return redirect('app:home')
        else:
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
    """
    Vista para el Médico: Lista de espera de casos IVE/Aborto.
    Muestra solo los casos en estado 'derivado' (pendientes de acción).
    """
    casos = Aborto.objects.filter(estado='derivado').order_by('-fecha_derivacion')
    return render(request, 'partos/panel_abortos.html', {'casos': casos})


@login_required
@medico_requerido
def resolver_aborto(request, pk):
    """
    Paso 2: Médico confirma diagnóstico y procedimiento.
    
    Acciones:
    1. Registra diagnósticos y causales (si aplica).
    2. Cambia estado del caso a 'confirmado'.
    3. Mantiene paciente en 'Observación' para cuidados post-procedimiento.
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
            
            # Asegurar estado para monitorización en sala
            caso.madre.estado_salud = 'observacion' 
            caso.madre.save()
            
            messages.success(request, 'Procedimiento registrado. Paciente derivada a Sala de Hospitalización (Observación).')
            return redirect('app:home')
    else:
        form = ResolverAbortoForm(instance=caso)
    
    return render(request, 'partos/resolver_aborto.html', {'form': form, 'caso': caso})