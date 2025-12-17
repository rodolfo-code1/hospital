# hospital/app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone 
from django.db.models import Q
from django.http import JsonResponse

# Importación de modelos de otros módulos para generar estadísticas
from altas.models import Alta
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from .models import Notificacion

@login_required
def home(request):
    """
    Vista del Dashboard Principal (Home).
    
    Esta función actúa como un 'hub' central. Detecta el rol del usuario
    y carga widgets/estadísticas personalizadas para su trabajo diario.
    
    Lógica por Roles:
    - Todos: Ven sus notificaciones no leídas.
    - Médicos: Ven altas pendientes de firma, casos IVE y alertas de riesgo (RN/Parto).
    - Administrativos: Ven altas médicas listas para cierre administrativo.
    - Matronas: Ven el resumen de partos registrados en su turno.
    """
    user = request.user
    context = {}

    # =========================================================
    # 1. SISTEMA DE NOTIFICACIONES (COMÚN PARA TODOS)
    # =========================================================
    # Recuperamos solo las alertas activas (no leídas) para la barra superior o modal
    notificaciones_qs = Notificacion.objects.filter(usuario=user, leido=False).order_by('-fecha_creacion')
    
    context['cant_notificaciones'] = notificaciones_qs.count()
    context['notificaciones'] = notificaciones_qs[:5] # Solo mostramos las 5 más recientes

    # =========================================================
    # 2. LÓGICA EXCLUSIVA PARA MÉDICOS (Y TI para debug)
    # =========================================================
    if user.rol in ['medico', 'encargado_ti']:
        
        # A. Altas Clínicas: Pacientes con datos completos esperando firma médica
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()
        
        # B. Ley IVE: Casos derivados que requieren confirmación o resolución
        context['pendientes_ive'] = Aborto.objects.filter(estado='derivado').count()
        
        # C. Alertas de Neonatología (Criterios de riesgo automático)
        alertas_rn = RecienNacido.objects.filter(
            alerta_revisada=False # Solo las no gestionadas
        ).filter(
            Q(apgar_1_min__lt=7) |  # Apgar bajo
            Q(apgar_5_min__lt=7) | 
            Q(peso__lt=2500) |      # Bajo peso
            Q(peso__gt=4000)        # Macrosomía
        ).count()
        
        # D. Alertas de Obstetricia (Partos con complicaciones)
        alertas_parto = Parto.objects.filter(
            tuvo_complicaciones=True,
            alerta_revisada=False
        ).count()
        
        # Sumatoria total para el "semáforo" de alertas en el dashboard
        context['total_alertas'] = alertas_rn + alertas_parto


    # =========================================================
    # 3. LÓGICA PARA ADMINISTRATIVOS (Oficina/Admisión)
    # =========================================================
    if user.rol in ['administrativo', 'encargado_ti']:
        # Buscan altas que YA firmó el médico pero falta cerrar cuenta/liberar cama
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    

    # =========================================================
    # 4. LÓGICA PARA MATRONAS (Turno)
    # =========================================================
    if user.rol in ['matrona', 'encargado_ti']:
        # Indicador de productividad diaria: Cuántos partos ha ingresado hoy este usuario
        hoy = timezone.now().date()
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user
        ).count()

    return render(request, 'home.html', context)


@login_required
def marcar_leida(request, pk):
    """
    Acción: 'REVISAR' Notificación.
    
    Flujo:
    1. Marca la notificación como leída en la BD.
    2. Si la notificación tiene un link adjunto (ej: ir a ficha clínica), redirige allá.
    3. Si no, vuelve al dashboard.
    
    Se usa típicamente en el botón azul "Ver" de la alerta.
    """
    # get_object_or_404 asegura que solo el dueño de la noti pueda marcarla
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    
    if noti.link:
        return redirect(noti.link)
    return redirect('app:home')


@login_required
def ocultar_notificacion(request, pk):
    """
    Acción: 'CERRAR' o 'DESCARTAR' Notificación.
    
    Flujo:
    1. Marca la notificación como leída (desaparece de la lista).
    2. Recarga la página actual (Home) para refrescar la vista.
    
    Se usa en el botón "X" o "Cerrar" de la alerta.
    """
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    return redirect('app:home')


@login_required
def api_notificaciones(request):
    """
    API REST (JSON) para consumo AJAX desde el Frontend.
    
    Permite que la campana de notificaciones se actualice dinámicamente sin recargar
    la página (polling o actualización en tiempo real).
    
    Corrección de Hora:
    Es crítico convertir la fecha UTC de la base de datos a la hora local del usuario
    antes de enviarla al JavaScript, para mostrar "Hace 5 min" correctamente.
    """
    notis = Notificacion.objects.filter(
        usuario=request.user, 
        leido=False
    ).order_by('-fecha_creacion')[:5]
    
    data = []
    for n in notis:
        # Convertimos a hora local (Chile)
        fecha_local = timezone.localtime(n.fecha_creacion)
        
        data.append({
            'id': n.id,
            'titulo': n.titulo,
            'mensaje': n.mensaje,
            'tipo': n.tipo,
            'fecha': fecha_local.strftime("%H:%M"), # Formato 24hrs legible
            'link': n.link if n.link else None
        })
    
    return JsonResponse({
        'cantidad': notis.count(),
        'notificaciones': data
    })