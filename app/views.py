from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from altas.models import Alta
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from .models import Notificacion

@login_required
def home(request):
    """
    Dashboard principal del sistema.
    Centraliza el acceso según el rol del usuario.
    """
    user = request.user
    context = {}

    # --- CARGAR NOTIFICACIONES ---
    notificaciones = Notificacion.objects.filter(usuario=user, leido=False)[:5]
    context['notificaciones'] = notificaciones
    context['cant_notificaciones'] = notificaciones.count()

    # ==========================================
    # LÓGICA PARA MÉDICOS (CORREGIDA)
    # ==========================================
    if user.rol == 'medico' or user.rol == 'jefatura':
        # 1. Altas por Firmar (Sin cambios)
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()
        
        # 2. Alertas Clínicas (CORREGIDO: SOLO LAS NO REVISADAS)
        # Antes contábamos todo. Ahora filtramos por alerta_revisada=False
        alertas_rn = RecienNacido.objects.filter(
            alerta_revisada=False  # <--- FILTRO CLAVE
        ).filter(
            Q(apgar_1_min__lt=7) | 
            Q(apgar_5_min__lt=7) | 
            Q(peso__lt=2.5) | 
            Q(peso__gt=4.0)
        ).count()
        
        alertas_parto = Parto.objects.filter(
            tuvo_complicaciones=True,
            alerta_revisada=False  # <--- FILTRO CLAVE
        ).count()
        
        context['total_alertas'] = alertas_rn + alertas_parto

        # 3. Pendientes IVE / Aborto
        context['pendientes_ive'] = Aborto.objects.filter(estado='derivado').count()

    # ==========================================
    # LÓGICA PARA ADMINISTRATIVOS
    # ==========================================
    if user.rol == 'administrativo' or user.rol == 'jefatura':
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    
    # ==========================================
    # LÓGICA PARA MATRONAS
    # ==========================================
    if user.rol == 'matrona' or user.rol == 'jefatura':
        hoy = timezone.now().date()
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user
        ).count()

    return render(request, 'home.html', context)


def marcar_leida(request, pk):
    """Marca una notificación como leída y redirige"""
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    
    if noti.link:
        return redirect(noti.link)
    
    return redirect('app:home')