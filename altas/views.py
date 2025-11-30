from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Alta
from .forms import (
    CrearAltaForm,
    ConfirmarAltaClinicaForm,
    ConfirmarAltaAdministrativaForm,
    BuscarAltaForm
)
from .utils import generar_certificado_pdf, exportar_altas_excel
from usuarios.decorators import rol_requerido

# ==========================================
# GESTIÓN DE ALTAS (CRUD y Flujo)
# ==========================================

@login_required
def lista_altas(request):
    altas = Alta.objects.all().select_related('madre', 'parto', 'recien_nacido')
    form_buscar = BuscarAltaForm(request.GET or None)
    
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
    if request.method == 'POST':
        form = CrearAltaForm(request.POST)
        if form.is_valid():
            alta = form.save()
            alta.validar_registros()
            messages.success(request, f'Alta creada exitosamente para {alta.madre.nombre}.')
            return redirect('altas:detalle_alta', pk=alta.pk)
    else:
        form = CrearAltaForm()
    
    return render(request, 'altas/crear_alta.html', {'form': form, 'titulo': 'Crear Nueva Alta'})

@login_required
def detalle_alta(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if request.method == 'POST' and 'validar' in request.POST:
        if alta.validar_registros():
            messages.success(request, 'Registros validados correctamente.')
        else:
            messages.warning(request, f'Registros incompletos. {alta.observaciones_validacion}')
        return redirect('altas:detalle_alta', pk=pk)
    
    context = {
        'alta': alta,
        'puede_confirmar_clinica': alta.puede_confirmar_alta_clinica(),
        'puede_confirmar_administrativa': alta.puede_confirmar_alta_administrativa(),
    }
    return render(request, 'altas/detalle_alta.html', context)

@login_required
@rol_requerido('medico')
def confirmar_alta_clinica(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if not alta.puede_confirmar_alta_clinica():
        messages.error(request, 'No se puede confirmar. Verifique registros.')
        return redirect('altas:detalle_alta', pk=pk)
    
    if request.method == 'POST':
        form = ConfirmarAltaClinicaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_clinica(form.cleaned_data['medico_nombre'])
            if form.cleaned_data.get('observaciones_clinicas'):
                alta.observaciones += f"\n[Alta Clínica] {form.cleaned_data['observaciones_clinicas']}"
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
    if not alta.puede_confirmar_alta_administrativa():
        messages.error(request, 'No se puede confirmar. Falta alta clínica.')
        return redirect('altas:detalle_alta', pk=pk)
    
    if request.method == 'POST':
        form = ConfirmarAltaAdministrativaForm(request.POST)
        if form.is_valid():
            alta.confirmar_alta_administrativa(form.cleaned_data['administrativo_nombre'])
            if form.cleaned_data.get('observaciones_administrativas'):
                alta.observaciones += f"\n[Alta Admin] {form.cleaned_data['observaciones_administrativas']}"
                alta.save()
            
            try:
                generar_certificado_pdf(alta)
                messages.info(request, 'Alta completada y certificado generado.')
            except Exception:
                pass
                
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
    try:
        estado = request.GET.get('estado')
        altas = Alta.objects.filter(estado=estado) if estado else Alta.objects.all()
        return exportar_altas_excel(altas)
    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('altas:lista_altas')

@login_required
def descargar_certificado(request, pk):
    alta = get_object_or_404(Alta, pk=pk)
    if not alta.esta_completada():
        messages.error(request, 'El alta debe estar completada.')
        return redirect('altas:detalle_alta', pk=pk)
    return generar_certificado_pdf(alta)