from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PartoForm
from .models import Parto
from usuarios.decorators import rol_requerido

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