# altas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from .forms import (
    CrearAltaForm,
    ConfirmarAltaClinicaForm,
    ConfirmarAltaAdministrativaForm,
    BuscarAltaForm,
    MadreForm,
    PartoForm,
    RecienNacidoForm
)
from .utils import generar_certificado_pdf, exportar_altas_excel
from usuarios.decorators import rol_requerido

# ==========================================
# VISTAS DE REGISTRO (MATRONA/ADMIN)
# ==========================================

@login_required
def registrar_madre(request):
    """Vista para registrar una nueva madre"""
    if request.method == 'POST':
        form = MadreForm(request.POST)
        if form.is_valid():
            # --- CORRECCIÓN: Guardar el usuario ---
            madre = form.save(commit=False)
            madre.creado_por = request.user
            madre.save()
            # -------------------------------------
            messages.success(
                request,
                f'Madre {madre.nombre} registrada exitosamente con RUT {madre.rut}'
            )
            return redirect('app:home')
    else:
        form = MadreForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Nueva Madre',
        'subtitulo': 'Ingreso de paciente al área de obstetricia'
    }
    return render(request, 'pacientes/registrar_madre.html', context)

@login_required
def registrar_parto(request):
    """Vista para registrar un nuevo parto"""
    if request.method == 'POST':
        form = PartoForm(request.POST)
        if form.is_valid():
            parto = form.save(commit=False) # Pausa el guardado
            parto.creado_por = request.user # Asigna la matrona actual
            parto.save() # Guarda definitivamente
            messages.success(
                request,
                f'Parto registrado exitosamente para {parto.madre.nombre}'
            )
            # CORREGIDO
            return redirect('app:home')
    else:
        form = PartoForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Parto',
        'subtitulo': 'Registro del proceso de parto'
    }
    return render(request, 'partos/registrar_parto.html', context)


@login_required
def registrar_recien_nacido(request):
    """Vista para registrar un recién nacido"""
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST)
        if form.is_valid():
            # --- CORRECCIÓN: Guardar el usuario ---
            rn = form.save(commit=False)
            rn.creado_por = request.user
            rn.save()
            # -------------------------------------
            messages.success(
                request,
                f'Recién nacido registrado exitosamente. Código: {rn.codigo_unico}'
            )
            return redirect('app:home')
    else:
        form = RecienNacidoForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Recién Nacido',
        'subtitulo': 'Registro inicial del RN'
    }
    return render(request, 'recien_nacidos/registrar_recien_nacido.html', context)
# ==========================================
# GESTIÓN DE ALTAS
# ==========================================

@login_required
def lista_altas(request):
    """
    Lista de todas las altas con filtros de búsqueda.
    """
    altas = Alta.objects.all().select_related('madre', 'parto', 'recien_nacido')
    form_buscar = BuscarAltaForm(request.GET or None)
    
    # Aplicar filtros si el formulario es válido
    if form_buscar.is_valid():
        buscar = form_buscar.cleaned_data.get('buscar')
        estado = form_buscar.cleaned_data.get('estado')
        fecha_desde = form_buscar.cleaned_data.get('fecha_desde')
        fecha_hasta = form_buscar.cleaned_data.get('fecha_hasta')
        
        if buscar:
            altas = altas.filter(
                Q(madre__nombre__icontains=buscar) |
                Q(madre__rut__icontains=buscar)
            )
        
        if estado:
            altas = altas.filter(estado=estado)
        
        if fecha_desde:
            altas = altas.filter(fecha_creacion__gte=fecha_desde)
        
        if fecha_hasta:
            altas = altas.filter(fecha_creacion__lte=fecha_hasta)
    
    context = {
        'altas': altas,
        'form_buscar': form_buscar,
        'total_altas': altas.count(),
        'pendientes': altas.filter(estado='pendiente').count(),
        'completadas': altas.filter(estado='completada').count(),
    }
    
    return render(request, 'altas/lista_altas.html', context)


@login_required
def crear_alta(request):
    """
    Vista para crear un nuevo proceso de alta.
    """
    if request.method == 'POST':
        form = CrearAltaForm(request.POST)
        if form.is_valid():
            alta = form.save()
            # Validar automáticamente los registros al crear
            alta.validar_registros()
            
            messages.success(
                request,
                f'Alta creada exitosamente para {alta.madre.nombre}. '
                f'Estado: {alta.get_estado_display()}'
            )
            return redirect('altas:detalle_alta', pk=alta.pk)
    else:
        form = CrearAltaForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nueva Alta'
    }
    
    return render(request, 'altas/crear_alta.html', context)


@login_required
def detalle_alta(request, pk):
    """
    Vista de detalle de un alta específica.
    Muestra toda la información y permite validar registros.
    """
    alta = get_object_or_404(Alta, pk=pk)
    
    # Si se solicita revalidar los registros
    if request.method == 'POST' and 'validar' in request.POST:
        if alta.validar_registros():
            messages.success(request, 'Registros validados correctamente. El alta está lista para confirmación.')
        else:
            messages.warning(
                request,
                f'Registros incompletos. {alta.observaciones_validacion}'
            )
        return redirect('altas:detalle_alta', pk=pk)
    
    context = {
        'alta': alta,
        'puede_confirmar_clinica': alta.puede_confirmar_alta_clinica(),
        'puede_confirmar_administrativa': alta.puede_confirmar_alta_administrativa(),
    }
    
    return render(request, 'altas/detalle_alta.html', context)


@login_required
@rol_requerido('medico') # Nota: quitamos 'jefatura' si ya no existe ese rol
def confirmar_alta_clinica(request, pk):
    """
    Vista para confirmar el alta clínica (Médico).
    """
    alta = get_object_or_404(Alta, pk=pk)
    
    if not alta.puede_confirmar_alta_clinica():
        messages.error(
            request,
            'No se puede confirmar el alta clínica. Verifica que los registros estén completos.'
        )
        return redirect('altas:detalle_alta', pk=pk)
    
    if request.method == 'POST':
        form = ConfirmarAltaClinicaForm(request.POST)
        if form.is_valid():
            try:
                medico_nombre = form.cleaned_data['medico_nombre']
                observaciones = form.cleaned_data.get('observaciones_clinicas', '')
                
                # Confirmar alta clínica
                alta.confirmar_alta_clinica(medico_nombre)
                
                # Agregar observaciones si hay
                if observaciones:
                    alta.observaciones += f"\n[Alta Clínica] {observaciones}"
                    alta.save()
                
                messages.success(
                    request,
                    f'Alta clínica confirmada por {medico_nombre}.'
                )
                return redirect('altas:detalle_alta', pk=pk)
            
            except Exception as e:
                messages.error(request, f'Error al confirmar alta clínica: {str(e)}')
    else:
        form = ConfirmarAltaClinicaForm()
    
    context = {
        'alta': alta,
        'form': form,
        'tipo_confirmacion': 'clínica'
    }
    
    return render(request, 'altas/confirmar_alta.html', context)


@login_required
@rol_requerido('administrativo') 
def confirmar_alta_administrativa(request, pk):
    """
    Vista para confirmar el alta administrativa (Administrativo).
    """
    alta = get_object_or_404(Alta, pk=pk)
    
    if not alta.puede_confirmar_alta_administrativa():
        messages.error(
            request,
            'No se puede confirmar el alta administrativa. Debe confirmarse primero el alta clínica.'
        )
        return redirect('altas:detalle_alta', pk=pk)
    
    if request.method == 'POST':
        form = ConfirmarAltaAdministrativaForm(request.POST)
        if form.is_valid():
            try:
                administrativo_nombre = form.cleaned_data['administrativo_nombre']
                observaciones = form.cleaned_data.get('observaciones_administrativas', '')
                
                # Confirmar alta administrativa
                alta.confirmar_alta_administrativa(administrativo_nombre)
                
                # Agregar observaciones si hay
                if observaciones:
                    alta.observaciones += f"\n[Alta Administrativa] {observaciones}"
                    alta.save()
                
                messages.success(
                    request,
                    f'Alta administrativa confirmada por {administrativo_nombre}. '
                    f'El proceso de alta está COMPLETADO.'
                )
                
                # Generar certificado PDF automáticamente
                try:
                    generar_certificado_pdf(alta)
                    messages.info(request, 'Certificado PDF generado exitosamente.')
                except Exception as e:
                    messages.warning(request, f'Alta completada, pero error al generar PDF: {str(e)}')
                
                return redirect('altas:detalle_alta', pk=pk)
            
            except Exception as e:
                messages.error(request, f'Error al confirmar alta administrativa: {str(e)}')
    else:
        form = ConfirmarAltaAdministrativaForm()
    
    context = {
        'alta': alta,
        'form': form,
        'tipo_confirmacion': 'administrativa'
    }
    
    return render(request, 'altas/confirmar_alta.html', context)


@login_required
def historial_altas(request):
    """
    Vista del historial completo de altas completadas.
    """
    altas_completadas = Alta.objects.filter(
        estado='completada'
    ).select_related('madre', 'parto', 'recien_nacido').order_by('-fecha_alta')
    
    context = {
        'altas': altas_completadas,
        'total': altas_completadas.count()
    }
    
    return render(request, 'altas/historial_altas.html', context)


@login_required
def exportar_excel(request):
    """
    Vista para exportar altas a Excel.
    """
    try:
        # Filtrar por estado si se proporciona
        estado = request.GET.get('estado', None)
        
        if estado:
            altas = Alta.objects.filter(estado=estado)
        else:
            altas = Alta.objects.all()
        
        # Generar archivo Excel
        response = exportar_altas_excel(altas)
        return response
    
    except Exception as e:
        messages.error(request, f'Error al exportar a Excel: {str(e)}')
        return redirect('altas:lista_altas')


@login_required
def descargar_certificado(request, pk):
    """
    Vista para descargar/visualizar el certificado PDF de un alta.
    """
    alta = get_object_or_404(Alta, pk=pk)
    
    if not alta.esta_completada():
        messages.error(request, 'El alta debe estar completada para generar el certificado.')
        return redirect('altas:detalle_alta', pk=pk)
    
    try:
        response = generar_certificado_pdf(alta)
        return response
    except Exception as e:
        messages.error(request, f'Error al generar certificado: {str(e)}')
        return redirect('altas:detalle_alta', pk=pk)