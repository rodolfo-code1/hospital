from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Exists, OuterRef
from .models import Madre
from .forms import MadreForm, MadreRecepcionForm
from usuarios.decorators import rol_requerido
from usuarios.models import Usuario
from app.models import Notificacion
# --- IMPORTS NUEVOS PARA FILTRADO ---
from partos.models import Aborto, Parto
from recien_nacidos.models import RecienNacido

# ==========================================
# VISTA RECEPCIONISTA: ADMISIÓN + ALERTA
# ==========================================
@login_required
def registrar_madre_recepcion(request):
    if request.user.rol not in ['recepcionista', 'jefatura', 'encargado_ti']:
         messages.error(request, "No tienes permiso para acceder a Admisión.")
         return redirect('app:home')

    if request.method == 'POST':
        # RUT crudo para verificar reingreso
        rut_raw = request.POST.get('rut', '').replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_raw[:-1]}-{rut_raw[-1]}" if len(rut_raw) > 1 else rut_raw
        
        madre_existente = Madre.objects.filter(rut=rut_formateado).first()

        if madre_existente:
            # --- REINGRESO (Si ya existe) ---
            if madre_existente.estado_alta == 'hospitalizado':
                messages.warning(request, f'La paciente {madre_existente.nombre} ya está activa en sala.')
                return redirect('app:home')
            else:
                # Reactivar paciente antigua
                form = MadreRecepcionForm(request.POST, instance=madre_existente)
                if form.is_valid():
                    madre = form.save(commit=False)
                    madre.estado_alta = 'hospitalizado' # Reactivar
                    madre.estado_salud = 'observacion'
                    # Importante: update fecha_ingreso para que cuente como nuevo ciclo
                    from django.utils import timezone
                    madre.fecha_ingreso = timezone.now() 
                    madre.save()
                    
                    # Notificar
                    crear_notificacion_ingreso(madre, reingreso=True)
                    messages.success(request, f'REINGRESO: Paciente {madre.nombre} activada.')
                    return redirect('app:home')
        else:
            # --- NUEVO INGRESO ---
            form = MadreRecepcionForm(request.POST)
            if form.is_valid():
                madre = form.save(commit=False)
                madre.creado_por = request.user
                madre.save()
                
                crear_notificacion_ingreso(madre, reingreso=False)
                messages.success(request, f'Paciente {madre.nombre} registrada.')
                return redirect('app:home')
    else:
        form = MadreRecepcionForm()
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form,
        'titulo': 'Admisión de Paciente',
        'subtitulo': 'Registro o Reingreso de Pacientes'
    })

def crear_notificacion_ingreso(madre, reingreso=False):
    """Auxiliar para notificar a matronas"""
    tiene_alerta = bool(madre.alerta_recepcion)
    tipo = 'urgente' if tiene_alerta else 'info'
    titulo = "🚨 ALERTA INGRESO" if tiene_alerta else ("🔄 REINGRESO" if reingreso else "Nuevo Ingreso")
    msg = f"Paciente: {madre.nombre}\nRUT: {madre.rut}"
    if tiene_alerta: msg += f"\n⚠️: {madre.alerta_recepcion}"
    
    matronas = Usuario.objects.filter(rol='matrona')
    objs = [Notificacion(usuario=m, titulo=titulo, mensaje=msg, tipo=tipo, link=f"/pacientes/completar/{madre.pk}/") for m in matronas]
    Notificacion.objects.bulk_create(objs)


# ==========================================
# GESTIÓN CLÍNICA (MATRONA) - LISTADO FILTRADO
# ==========================================

@login_required
def lista_pacientes(request):
    """
    Listado de trabajo para la Matrona.
    Muestra pacientes hospitalizadas que AÚN requieren atención (Parto o Completar ficha).
    EXCLUYE:
    1. Pacientes con Aborto/IVE ya resuelto por el médico.
    2. Pacientes que ya tienen Recién Nacido registrado en este ingreso.
    """
    # 1. Base: Solo las que están en el hospital
    madres = Madre.objects.filter(estado_alta='hospitalizado').order_by('-fecha_ingreso')
    
    # 2. Filtrado Lógico (Python) para excluir casos resueltos
    madres_pendientes = []
    
    for m in madres:
        # A. Verificar si tiene Aborto Resuelto (Confirmado) en este ingreso
        tiene_aborto_listo = m.abortos.filter(
            estado='confirmado',
            fecha_derivacion__gte=m.fecha_ingreso
        ).exists()
        
        if tiene_aborto_listo:
            continue # Saltamos esta madre (ya la atiende el médico o está lista)

        # B. Verificar si ya tiene Parto con Recién Nacido en este ingreso
        # (Buscamos partos desde que ingresó y vemos si tienen hijos)
        tiene_rn_listo = False
        partos_ingreso = m.partos.filter(fecha_registro__gte=m.fecha_ingreso)
        for p in partos_ingreso:
            if p.recien_nacidos.exists():
                tiene_rn_listo = True
                break
        
        if tiene_rn_listo:
            continue # Saltamos esta madre (ya dio a luz y se registró al bebé)

        # Si pasa los filtros, la agregamos a la lista
        madres_pendientes.append(m)

    # 3. Búsqueda en la lista filtrada
    query = request.GET.get('q')
    if query:
        query = query.lower()
        madres_pendientes = [
            m for m in madres_pendientes 
            if query in m.rut.lower() or query in m.nombre.lower()
        ]
        
    return render(request, 'pacientes/lista_pacientes.html', {
        'madres': madres_pendientes, # Pasamos la lista filtrada
        'query': query
    })


@login_required
def ver_ficha_clinica(request, pk):
    madre = get_object_or_404(Madre, pk=pk)
    form = MadreForm(instance=madre)
    for field in form.fields.values(): field.widget.attrs['disabled'] = True
    return render(request, 'pacientes/ver_ficha.html', {'form': form, 'madre': madre, 'titulo': 'Ficha Clínica'})

@login_required
def editar_ficha_clinica(request, pk):
    madre = get_object_or_404(Madre, pk=pk)
    if request.method == 'POST':
        form = MadreForm(request.POST, instance=madre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ficha actualizada.')
            return redirect('pacientes:ver_ficha', pk=madre.pk)
    else:
        form = MadreForm(instance=madre)
    return render(request, 'pacientes/registrar_madre.html', {'form': form, 'titulo': 'Editar Ficha', 'subtitulo': f'{madre.nombre}'})

# Compatibilidad
@login_required
def registrar_madre(request): return redirect('pacientes:admision_madre')
@login_required
def buscar_madre(request): return redirect('pacientes:lista_pacientes')
@login_required
def completar_madre(request, pk): return redirect('pacientes:ver_ficha', pk=pk)