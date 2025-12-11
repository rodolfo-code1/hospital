from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q

# Importación de modelos
from altas.models import Alta
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from .models import Notificacion

@login_required
def home(request):
    """
    Dashboard principal del sistema.
    Centraliza el acceso y métricas según el rol del usuario.
    """
    user = request.user
    context = {}

    # ---------------------------------------------------------
    # 1. SISTEMA DE NOTIFICACIONES (MEJORADO)
    # ---------------------------------------------------------
    # Primero obtenemos el QuerySet base de lo no leído
    notificaciones_qs = Notificacion.objects.filter(usuario=user, leido=False).order_by('-fecha_creacion')
    
    # Contamos el TOTAL real antes de recortar la lista (ej: tienes 20, muestras 5)
    context['cant_notificaciones'] = notificaciones_qs.count()
    
    # Ahora sí recortamos para mostrar solo las últimas 5 en el panel
    context['notificaciones'] = notificaciones_qs[:5]


    # ---------------------------------------------------------
    # 2. LÓGICA PARA MÉDICOS 
    # ---------------------------------------------------------
    if user.rol in ['medico', 'encargado_ti']:
        # A. Altas Clínicas pendientes de firma
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()
        
        # B. Alertas Clínicas (Recién Nacidos)
        # Filtramos por criterios médicos Y que no hayan sido revisadas
        # NOTA: Asegúrate de haber agregado 'alerta_revisada' a tus modelos
        alertas_rn = RecienNacido.objects.filter(
            alerta_revisada=False
        ).filter(
            Q(apgar_1_min__lt=7) | 
            Q(apgar_5_min__lt=7) | 
            Q(peso__lt=2500) |      # Usar gramos o kg según tu modelo (2.5 vs 2500)
            Q(peso__gt=4000)
        ).count()
        
        # C. Alertas de Partos (Complicaciones)
        alertas_parto = Parto.objects.filter(
            tuvo_complicaciones=True,
            alerta_revisada=False
        ).count()
        
        context['total_alertas'] = alertas_rn + alertas_parto

        # D. Pendientes IVE / Aborto
        context['pendientes_ive'] = Aborto.objects.filter(estado='derivado').count()


    # ---------------------------------------------------------
    # 3. LÓGICA PARA ADMINISTRATIVOS
    # ---------------------------------------------------------
    if user.rol in ['administrativo', 'jefatura', 'encargado_ti']:
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    

    # ---------------------------------------------------------
    # 4. LÓGICA PARA MATRONAS
    # ---------------------------------------------------------
    if user.rol in ['matrona', 'jefatura', 'encargado_ti']:
        hoy = timezone.now().date()
        # Contamos partos registrados HOY por este usuario
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user
        ).count()

    return render(request, 'home.html', context)


@login_required
def marcar_leida(request, pk):
    """
    Marca una notificación como leída y redirige al enlace correspondiente.
    """
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    
    if noti.link:
        return redirect(noti.link)
        
    return redirect('app:home')
