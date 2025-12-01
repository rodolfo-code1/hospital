from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Madre
from .forms import MadreForm, MadreRecepcionForm
from usuarios.decorators import rol_requerido
from usuarios.models import Usuario
from app.models import Notificacion

# ==========================================
# VISTA RECEPCIONISTA: ADMISIÓN + NOTIFICACIÓN
# ==========================================
@login_required
def registrar_madre_recepcion(request):
    # 1. Validación de seguridad manual para este flujo específico
    if request.user.rol not in ['recepcionista', 'jefatura', 'encargado_ti']:
         messages.error(request, "No tienes permiso para acceder a Admisión.")
         return redirect('app:home')

    if request.method == 'POST':
        form = MadreRecepcionForm(request.POST)
        if form.is_valid():
            # Guardar la madre
            madre = form.save(commit=False)
            madre.creado_por = request.user
            madre.save()
            
            # --- LÓGICA DE NOTIFICACIÓN AUTOMÁTICA ---
            # Detectar si es una alerta urgente (si escribió algo en el campo alerta)
            tiene_alerta = bool(madre.alerta_recepcion)
            tipo_noti = 'urgente' if tiene_alerta else 'info'
            titulo_noti = "🚨 INGRESO CRÍTICO" if tiene_alerta else "Nuevo Ingreso"
            
            # Construir el mensaje
            mensaje_texto = f"Paciente: {madre.nombre}\nRUT: {madre.rut}"
            if tiene_alerta:
                mensaje_texto += f"\n⚠️ ALERTA: {madre.alerta_recepcion}"
            
            # Buscar destinatarios (Todas las Matronas)
            matronas = Usuario.objects.filter(rol='matrona')
            
            # Crear notificación para cada matrona
            notificaciones = []
            for matrona in matronas:
                notificaciones.append(Notificacion(
                    usuario=matrona,
                    titulo=titulo_noti,
                    mensaje=mensaje_texto,
                    tipo=tipo_noti,
                    # El link lleva directo a ver la ficha de la paciente
                    link=f"/pacientes/ficha/{madre.pk}/"
                ))
            
            # Guardado masivo (más eficiente)
            Notificacion.objects.bulk_create(notificaciones)
            # -----------------------------------------

            messages.success(request, f'Paciente {madre.nombre} ingresada y equipo clínico notificado.')
            return redirect('app:home')
    else:
        form = MadreRecepcionForm()
    
    context = {
        'form': form,
        'titulo': 'Admisión e Ingreso Clínico',
        'subtitulo': 'Registro completo de paciente (Recepción)'
    }
    return render(request, 'pacientes/registrar_madre.html', context)


# ==========================================
# GESTIÓN CLÍNICA (MATRONA)
# ==========================================

@login_required
def lista_pacientes(request):
    """Listado de pacientes para que la matrona vea los ingresos"""
    madres = Madre.objects.all().order_by('-fecha_ingreso')
    
    query = request.GET.get('q')
    if query:
        madres = madres.filter(
            Q(rut__icontains=query) | 
            Q(nombre__icontains=query)
        )
        
    return render(request, 'pacientes/lista_pacientes.html', {
        'madres': madres, 
        'query': query
    })


@login_required
def ver_ficha_clinica(request, pk):
    """
    Vista de Solo Lectura.
    Muestra los datos bloqueados para revisión antes de editar.
    """
    madre = get_object_or_404(Madre, pk=pk)
    form = MadreForm(instance=madre)
    
    # Bloquear todos los campos visualmente
    for field in form.fields.values():
        field.widget.attrs['disabled'] = True

    return render(request, 'pacientes/ver_ficha.html', {
        'form': form,
        'madre': madre,
        'titulo': 'Ficha Clínica (Vista Previa)'
    })


@login_required
def editar_ficha_clinica(request, pk):
    """
    Edición Real: La matrona completa los antecedentes faltantes.
    """
    madre = get_object_or_404(Madre, pk=pk)
    
    if request.method == 'POST':
        form = MadreForm(request.POST, instance=madre)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ficha clínica de {madre.nombre} actualizada correctamente.')
            # Al guardar, volvemos a la vista de lectura
            return redirect('pacientes:ver_ficha', pk=madre.pk)
    else:
        form = MadreForm(instance=madre)
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form,
        'titulo': 'Editar Ficha Clínica',
        'subtitulo': f'Modificando datos de: {madre.nombre}'
    })


# ==========================================
# REDIRECCIONES DE COMPATIBILIDAD
# (Mantener para evitar errores de enlaces antiguos)
# ==========================================
@login_required
def registrar_madre(request):
    return redirect('pacientes:admision_madre')

@login_required
def buscar_madre(request):
    return redirect('pacientes:lista_pacientes')

@login_required
def completar_madre(request, pk):
    return redirect('pacientes:ver_ficha', pk=pk)