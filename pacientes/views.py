# hospital/pacientes/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Exists, OuterRef
from .models import Madre
from .forms import MadreForm, MadreRecepcionForm
from usuarios.decorators import rol_requerido
from usuarios.models import Usuario
from app.models import Notificacion

from partos.models import Aborto, Parto
from recien_nacidos.models import RecienNacido
import qrcode
from io import BytesIO
from django.http import HttpResponse
from usuarios.decorators import rol_requerido
from django.urls import reverse
from simple_history.utils import update_change_reason

# ==========================================
# SECCIÓN 1: VISTA DE RECEPCIÓN (ADMISIÓN)
# ==========================================

@login_required
def registrar_madre_recepcion(request):
    """
    Vista principal de Admisión. 
    Permite registrar una nueva paciente y clasificar su riesgo (Triage).
    
    Lógica de Notificación (Semáforo):
    - Si el estado es 'Crítico' (Rojo) o 'Observación' (Amarillo), o si se escribe
      una alerta de texto, el sistema envía una Notificación URGENTE a todas las matronas.
    - Si es 'Sano' (Verde), envía una notificación informativa.
    """
    if request.method == 'POST':
        form = MadreRecepcionForm(request.POST)
    
        if form.is_valid():
            # Guardamos sin commit para asignar el usuario creador
            madre = form.save(commit=False)
            madre.creado_por = request.user
            madre.save()
            
            # --- INICIO LÓGICA DE NOTIFICACIÓN SEMÁFORO ---
            
            # 1. Obtener datos de riesgo
            estado_semaforo = madre.estado_salud # 'sano', 'observacion', 'critico'
            texto_alerta = madre.alerta_recepcion
            
            # 2. Determinar prioridad de la notificación
            # Es urgente si hay alerta escrita O si el color es rojo/amarillo
            es_urgente = bool(texto_alerta) or estado_semaforo in ['critico', 'observacion']
            tipo_noti = 'urgente' if es_urgente else 'info'
            
            # 3. Construcción del título dinámico
            if estado_semaforo == 'critico':
                titulo_noti = "🔴 INGRESO CRÍTICO (ALTO RIESGO)"
            elif estado_semaforo == 'observacion':
                titulo_noti = "🟡 Ingreso en Observación"
            else:
                titulo_noti = "🟢 Nuevo Ingreso (Baja Complejidad)"
            
            # 4. Construcción del mensaje
            mensaje_texto = f"Paciente: {madre.nombre}\nRUT: {madre.rut}"
            if texto_alerta:
                mensaje_texto += f"\n⚠️ OBS: {texto_alerta}"
            
            # 5. Envío masivo a todas las Matronas
            matronas = Usuario.objects.filter(rol='matrona')
            notificaciones = []
            for matrona in matronas:
                notificaciones.append(Notificacion(
                    usuario=matrona,
                    titulo=titulo_noti,
                    mensaje=mensaje_texto,
                    tipo=tipo_noti,
                    link=f"/pacientes/completar/{madre.pk}/" # Link directo a la ficha
                ))
            Notificacion.objects.bulk_create(notificaciones)
            # --- FIN LÓGICA NOTIFICACIÓN ---

            messages.success(request, f'Paciente ingresada con clasificación {madre.get_estado_salud_display()}.')
            return redirect('app:home')
    else:
        form = MadreRecepcionForm()
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form,
        'titulo': 'Admisión de Paciente',
        'subtitulo': 'Registro y Clasificación de Riesgo'
    })


def crear_notificacion_ingreso(madre, reingreso=False):
    """
    Función auxiliar para generar notificaciones (utilizada en otros contextos de reingreso).
    """
    tiene_alerta = bool(madre.alerta_recepcion)
    tipo = 'urgente' if tiene_alerta else 'info'
    titulo = "🚨 ALERTA INGRESO" if tiene_alerta else ("🔄 REINGRESO" if reingreso else "Nuevo Ingreso")
    msg = f"Paciente: {madre.nombre}\nRUT: {madre.rut}"
    if tiene_alerta: msg += f"\n⚠️: {madre.alerta_recepcion}"
    
    matronas = Usuario.objects.filter(rol='matrona')
    objs = [Notificacion(usuario=m, titulo=titulo, mensaje=msg, tipo=tipo, link=f"/pacientes/completar/{madre.pk}/") for m in matronas]
    Notificacion.objects.bulk_create(objs)


# ==========================================
# SECCIÓN 2: GESTIÓN CLÍNICA (MATRONA)
# ==========================================

@login_required
def lista_pacientes(request):
    """
    Lista de Trabajo Principal para la Matrona.
    
    Lógica de Filtrado Inteligente:
    Muestra SOLO pacientes hospitalizadas que requieren acción clínica.
    Se ocultan automáticamente aquellas que:
    1. Ya tienen un evento de Aborto/IVE resuelto por el médico (confirmado).
    2. Ya dieron a luz y tienen al Recién Nacido registrado en el sistema.
    """
    # 1. Base: Solo pacientes activos en el hospital
    madres = Madre.objects.filter(estado_alta='hospitalizado').order_by('-fecha_ingreso')
    
    # 2. Filtrado Lógico en Python
    madres_pendientes = []
    
    for m in madres:
        # A. Excluir si tiene Aborto ya resuelto en este ingreso
        tiene_aborto_listo = m.abortos.filter(
            estado='confirmado',
            fecha_derivacion__gte=m.fecha_ingreso
        ).exists()
        
        if tiene_aborto_listo:
            continue # Paciente gestionada, no mostrar en lista de pendientes

        # B. Excluir si ya tiene Parto + Recién Nacido registrado
        tiene_rn_listo = False
        partos_ingreso = m.partos.filter(fecha_registro__gte=m.fecha_ingreso)
        for p in partos_ingreso:
            if p.recien_nacidos.exists():
                tiene_rn_listo = True
                break
        
        if tiene_rn_listo:
            continue # Ciclo de parto completo, no mostrar

        # Si pasa los filtros, es una paciente pendiente
        madres_pendientes.append(m)

    # 3. Búsqueda manual por nombre o RUT dentro de la lista filtrada
    query = request.GET.get('q')
    if query:
        query = query.lower()
        madres_pendientes = [
            m for m in madres_pendientes 
            if query in m.rut.lower() or query in m.nombre.lower()
        ]
        
    return render(request, 'pacientes/lista_pacientes.html', {
        'madres': madres_pendientes,
        'query': query
    })


@login_required
def ver_ficha_clinica(request, pk):
    """Vista de solo lectura de la ficha clínica."""
    madre = get_object_or_404(Madre, pk=pk)
    form = MadreForm(instance=madre)
    # Deshabilitar todos los campos para modo lectura
    for field in form.fields.values(): field.widget.attrs['disabled'] = True
    return render(request, 'pacientes/ver_ficha.html', {'form': form, 'madre': madre, 'titulo': 'Ficha Clínica'})


@login_required
def editar_ficha_clinica(request, pk):
    """
    Vista para editar datos de la paciente.
    Usa el formulario de recepción para permitir actualizar el semáforo de riesgo.
    """
    madre = get_object_or_404(Madre, pk=pk)
    
    if request.method == 'POST':
        form = MadreRecepcionForm(request.POST, instance=madre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ficha actualizada correctamente.')
            return redirect('pacientes:ver_ficha', pk=madre.pk)
    else:
        form = MadreRecepcionForm(instance=madre)
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form, 
        'titulo': 'Editar Ficha', 
        'subtitulo': f'{madre.nombre}'
    })

# --- Redirecciones de compatibilidad para URLs antiguas ---
@login_required
def registrar_madre(request): return redirect('pacientes:admision_madre')
@login_required
def buscar_madre(request): return redirect('pacientes:lista_pacientes')
@login_required
def completar_madre(request, pk): return redirect('pacientes:ver_ficha', pk=pk)


@login_required
def historial_recepcion(request):
    """
    Vista histórica para personal de admisión.
    Muestra todos los ingresos sin filtros de estado, para auditoría o consultas.
    """
    if request.user.rol not in ['recepcionista', 'encargado_ti']:
         messages.error(request, "Acceso restringido a personal de admisión.")
         return redirect('app:home')

    madres = Madre.objects.all().order_by('-fecha_ingreso')
    
    query = request.GET.get('q')
    if query:
        madres = madres.filter(
            Q(rut__icontains=query) | 
            Q(nombre__icontains=query)
        )
    
    return render(request, 'pacientes/historial_recepcion.html', {
        'madres': madres,
        'query': query
    })

# ==========================================
# SECCIÓN 3: GESTIÓN ADMINISTRATIVA (QR)
# ==========================================

@login_required
@rol_requerido('administrativo')
def admin_buscar_paciente(request):
    """
    Buscador específico para Administrativos.
    Objetivo: Generar brazaletes QR e identificación.
    Filtro: Solo muestra pacientes que AÚN no han egresado administrativamente.
    """
    madres = Madre.objects.exclude(
        estado_alta='alta_administrativa'
    ).order_by('-fecha_ingreso')
    
    query = request.GET.get('q')
    if query:
        madres = madres.filter(
            Q(rut__icontains=query) | 
            Q(nombre__icontains=query)
        )
    
    return render(request, 'pacientes/admin_buscar.html', {
        'madres': madres, 
        'query': query
    })

@login_required
@rol_requerido('administrativo',)
def ver_brazalete(request, pk):
    """Vista previa para impresión del brazalete de identificación."""
    madre = get_object_or_404(Madre, pk=pk)
    return render(request, 'pacientes/brazalete.html', {'madre': madre})

@login_required
def ficha_qr_madre(request, pk):
    """
    Ficha digital móvil.
    Es la vista que se abre al escanear el QR del brazalete.
    Muestra resumen clínico y los hijos asociados.
    """
    madre = get_object_or_404(Madre, pk=pk)
    partos = madre.partos.all().prefetch_related('recien_nacidos').order_by('-fecha_hora_inicio')
    
    return render(request, 'pacientes/ficha_qr_madre.html', {
        'madre': madre,
        'partos': partos
    })

@login_required
def generar_qr_imagen(request, pk):
    """
    Genera dinámicamente una imagen PNG con el código QR.
    El QR contiene la URL absoluta hacia la 'ficha_qr_madre'.
    """
    madre = get_object_or_404(Madre, pk=pk)
    
    # 1. Construir URL interna
    path_relativo = reverse('pacientes:ficha_qr_madre', args=[pk])
    url_completa = request.build_absolute_uri(path_relativo)
    
    # 2. Generar imagen QR en memoria
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(url_completa)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    return HttpResponse(buffer.getvalue(), content_type="image/png")


# ==========================================
# SECCIÓN 4: AUDITORÍA DE USUARIO
# ==========================================

@login_required
def historial_trabajo_matrona(request):
    """
    Historial personal de la Matrona (Mi Trabajo).
    Muestra todos los pacientes que el usuario ha 'tocado' (creado o editado).
    Utiliza django-simple-history para rastrear la participación.
    """
    # 1. Buscar IDs de madres donde el usuario actual aparece en el historial
    ids_gestionados = Madre.history.filter(
        history_user=request.user
    ).values_list('id', flat=True).distinct()
    
    # 2. Recuperar los objetos reales
    pacientes = Madre.objects.filter(id__in=ids_gestionados).order_by('-fecha_actualizacion')
    
    context = {
        'madres': pacientes,
        'titulo': 'Mi Historial de Atenciones',
        'subtitulo': 'Pacientes gestionadas o editadas por mí'
    }
    return render(request, 'pacientes/lista_pacientes.html', context)