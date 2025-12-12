from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from django.db.models import Q
from django.http import JsonResponse

# Importación de modelos
from altas.models import Alta
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from .models import Notificacion

@login_required
def home(request):
    """
    Dashboard principal del sistema.
    Centraliza el acceso y las alertas según el rol del usuario.
    """
    user = request.user
    context = {}

    # =========================================================
    # 1. SISTEMA DE NOTIFICACIONES (PARA TODOS LOS ROLES)
    # =========================================================
    notificaciones_qs = Notificacion.objects.filter(usuario=user, leido=False).order_by('-fecha_creacion')
    
    context['cant_notificaciones'] = notificaciones_qs.count()
    context['notificaciones'] = notificaciones_qs[:5]

    # =========================================================
    # 2. LÓGICA PARA MÉDICOS 
    # =========================================================
    if user.rol in ['medico', 'encargado_ti']:
        
        # A. Altas Clínicas pendientes de firma
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()
        
        # B. Pendientes IVE / Aborto
        context['pendientes_ive'] = Aborto.objects.filter(estado='derivado').count()
        
        # C. Alertas Clínicas (RN)
        alertas_rn = RecienNacido.objects.filter(
            alerta_revisada=False 
        ).filter(
            Q(apgar_1_min__lt=7) | 
            Q(apgar_5_min__lt=7) | 
            Q(peso__lt=2500) |      
            Q(peso__gt=4000)
        ).count()
        
        # D. Alertas de Partos
        alertas_parto = Parto.objects.filter(
            tuvo_complicaciones=True,
            alerta_revisada=False
        ).count()
        
        context['total_alertas'] = alertas_rn + alertas_parto


    # =========================================================
    # 3. LÓGICA PARA ADMINISTRATIVOS
    # =========================================================
    if user.rol in ['administrativo', 'encargado_ti']:
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    

    # =========================================================
    # 4. LÓGICA PARA MATRONAS
    # =========================================================
    if user.rol in ['matrona', 'encargado_ti']:
        hoy = timezone.now().date()
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user
        ).count()

    return render(request, 'home.html', context)


@login_required
def marcar_leida(request, pk):
    """
    ACCIÓN: REVISAR
    Marca como leída y REDIRIGE al enlace (Botón Azul).
    """
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    
    if noti.link:
        return redirect(noti.link)
    return redirect('app:home')


@login_required
def ocultar_notificacion(request, pk):
    """
    ACCIÓN: CERRAR / DESCARTAR
    Marca como leída y SE QUEDA en el home (Botón X).
    """
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    # Redirige al mismo home para recargar la página limpia
    return redirect('app:home')


@login_required
def api_notificaciones(request):
    """
    API JSON para actualización automática (AJAX).
    Devuelve la hora corregida a la zona horaria local.
    """
    notis = Notificacion.objects.filter(
        usuario=request.user, 
        leido=False
    ).order_by('-fecha_creacion')[:5]
    
    data = []
    for n in notis:
        # CORRECCIÓN DE HORA: Convertimos UTC a Local antes de formatear
        fecha_local = timezone.localtime(n.fecha_creacion)
        
        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'fecha': fecha_local.strftime("%H:%M"), # Hora corregida
            'link': n.link if n.link else None
        })
    
    return JsonResponse({
        'cantidad': notis.count(),
        'notificaciones': data
    })
