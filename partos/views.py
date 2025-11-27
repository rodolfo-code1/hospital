# partos/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Parto
from usuarios.decorators import rol_requerido

@login_required
@rol_requerido('matrona')
def mis_registros_clinicos(request):
    """
    Vista exclusiva para Matronas.
    Muestra SOLO los partos registrados por el usuario actual.
    Permite filtrar por fecha.
    """
    # 1. Filtro Base: Solo registros creados por MI (request.user)
    registros = Parto.objects.filter(creado_por=request.user).select_related('madre').order_by('-fecha_registro')

    # 2. Filtro por Fecha (Opcional)
    fecha_busqueda = request.GET.get('fecha')
    if fecha_busqueda:
        registros = registros.filter(fecha_registro__date=fecha_busqueda)

    context = {
        'registros': registros,
        'fecha_busqueda': fecha_busqueda
    }
    return render(request, 'partos/mis_registros.html', context)