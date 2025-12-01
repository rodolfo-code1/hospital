# app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from altas.models import Alta
from partos.models import Parto
from .models import Notificacion

@login_required
def home(request):
    """
    Dashboard principal con sistema de notificaciones.
    """
    user = request.user
    context = {}

    # --- CARGAR NOTIFICACIONES NO LEÍDAS ---
    notificaciones = Notificacion.objects.filter(usuario=user, leido=False)[:5]
    context['notificaciones'] = notificaciones
    context['cant_notificaciones'] = notificaciones.count()

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

def marcar_leida(request, pk):
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    # Si tiene link, vamos allá, si no, recargamos el home
    if noti.link:
        return redirect(noti.link)
    return redirect('app:home')