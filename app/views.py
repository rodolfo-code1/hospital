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
    Centraliza el acceso y las alertas según el rol del usuario.
    """
    user = request.user
    context = {}

    # =========================================================
    # 1. SISTEMA DE NOTIFICACIONES (PARA TODOS LOS ROLES)
    # =========================================================
    # Aquí es donde la Matrona recibe la alerta de la Recepcionista
    # y el Médico recibe la alerta de la Matrona.
    
    # Obtenemos todas las no leídas
    notificaciones_qs = Notificacion.objects.filter(usuario=user, leido=False).order_by('-fecha_creacion')
    
    # Contamos el TOTAL real (Ej: Tienes 20 alertas)
    context['cant_notificaciones'] = notificaciones_qs.count()
    
    # Solo enviamos las últimas 5 para no saturar el diseño
    context['notificaciones'] = notificaciones_qs[:5]

    # =========================================================
    # 2. LÓGICA PARA MÉDICOS Y JEFATURA
    # =========================================================
    if user.rol in ['medico', 'jefatura', 'encargado_ti']:
        
        # A. Altas Clínicas pendientes de firma
        context['pendientes_clinica'] = Alta.objects.filter(
            registros_completos=True, 
            alta_clinica_confirmada=False
        ).count()
        
        # B. Pendientes IVE / Aborto (Alerta Matrona -> Médico)
        # Cuenta los casos derivados que el médico debe resolver
        context['pendientes_ive'] = Aborto.objects.filter(estado='derivado').count()
        
        # C. Alertas Clínicas (Recién Nacidos con problemas)
        # Filtramos solo las que NO han sido revisadas (alerta_revisada=False)
        alertas_rn = RecienNacido.objects.filter(
            alerta_revisada=False 
        ).filter(
            Q(apgar_1_min__lt=7) | 
            Q(apgar_5_min__lt=7) | 
            Q(peso__lt=2500) |      # Asumiendo peso en gramos
            Q(peso__gt=4000)
        ).count()
        
        # D. Alertas de Partos (Con complicaciones)
        alertas_parto = Parto.objects.filter(
            tuvo_complicaciones=True,
            alerta_revisada=False
        ).count()
        
        # Total de alertas críticas para mostrar en rojo en el dashboard
        context['total_alertas'] = alertas_rn + alertas_parto


    # =========================================================
    # 3. LÓGICA PARA ADMINISTRATIVOS
    # =========================================================
    if user.rol in ['administrativo', 'jefatura', 'encargado_ti']:
        # Altas que ya firmó el médico pero falta el cierre administrativo
        context['pendientes_administrativa'] = Alta.objects.filter(
            alta_clinica_confirmada=True, 
            alta_administrativa_confirmada=False
        ).count()
    

    # =========================================================
    # 4. LÓGICA PARA MATRONAS
    # =========================================================
    if user.rol in ['matrona', 'jefatura', 'encargado_ti']:
        hoy = timezone.now().date()
        # Contador de productividad diaria
        context['registros_hoy'] = Parto.objects.filter(
            fecha_registro__date=hoy,
            creado_por=user
        ).count()

    return render(request, 'home.html', context)


@login_required
def marcar_leida(request, pk):
    """
    Marca una notificación como leída y redirige al enlace de la tarea.
    """
    noti = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    noti.leido = True
    noti.save()
    
    # Si la alerta tiene un link (ej: ir a ficha paciente), vamos allá.
    if noti.link:
        return redirect(noti.link)
        
    # Si no, volvemos al home
    return redirect('app:home')
