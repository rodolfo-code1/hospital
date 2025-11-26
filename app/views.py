# app/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from altas.models import Alta
from partos.models import Parto

@login_required
def home(request):
    """
    Dashboard principal del sistema.
    """
    user = request.user
    context = {}

    # Lógica para MÉDICOS
    if user.rol == 'medico':
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()

    # Lógica para ADMINISTRATIVOS
    if user.rol == 'administrativo':
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    
    # Lógica para MATRONAS
    if user.rol == 'matrona':
        hoy = timezone.now().date()
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user  
        ).count()

    return render(request, 'home.html', context)