from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Parto, Aborto
from .forms import PartoForm, DerivacionAbortoForm, ResolverAbortoForm
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
    Vista exclusiva para Matronas: Muestra SOLO sus registros.
    """
    registros = Parto.objects.filter(creado_por=request.user).select_related('madre').order_by('-fecha_registro')

    fecha_busqueda = request.GET.get('fecha')
    if fecha_busqueda:
        registros = registros.filter(fecha_registro__date=fecha_busqueda)

    context = {
        'registros': registros,
        'fecha_busqueda': fecha_busqueda
    }
    return render(request, 'partos/mis_registros.html', context)


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