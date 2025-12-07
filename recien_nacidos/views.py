from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RecienNacidoForm
import qrcode
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Q
from usuarios.decorators import rol_requerido
from .models import RecienNacido
from django.urls import reverse

@login_required
def registrar_recien_nacido(request):
    """Vista para registrar un recién nacido"""
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST)
        if form.is_valid():
            rn = form.save(commit=False)
            rn.creado_por = request.user
            rn.save()
            
            messages.success(
                request,
                f'Recién nacido registrado exitosamente. Código: {rn.codigo_unico}'
            )
            return redirect('app:home')
    else:
        form = RecienNacidoForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Recién Nacido',
        'subtitulo': 'Registro inicial del RN'
    }
    return render(request, 'recien_nacidos/registrar_recien_nacido.html', context)

@login_required
@rol_requerido('administrativo', 'jefatura')
def admin_buscar_rn(request):
    """
    Buscador de Recién Nacidos para generar brazaletes.
    """
    query = request.GET.get('q')
    rns = RecienNacido.objects.all().select_related('parto__madre').order_by('-fecha_registro')
    
    if query:
        rns = rns.filter(
            Q(codigo_unico__icontains=query) | 
            Q(parto__madre__rut__icontains=query) |
            Q(parto__madre__nombre__icontains=query)
        )

    return render(request, 'recien_nacidos/admin_buscar_rn.html', {
        'rns': rns,
        'query': query
    })

@login_required
@rol_requerido('administrativo', 'jefatura')
def ver_brazalete_rn(request, pk):
    """Vista previa del brazalete del bebé"""
    rn = get_object_or_404(RecienNacido, pk=pk)
    return render(request, 'recien_nacidos/brazalete_rn.html', {'rn': rn})

@login_required
def ficha_qr(request, pk):
    """
    Vista optimizada para móviles. Muestra el resumen clínico Madre-Hijo.
    Requiere login por seguridad (Ley de derechos del paciente).
    """
    rn = get_object_or_404(RecienNacido, pk=pk)
    # No necesitamos buscar a la madre aparte, accedemos por rn.parto.madre
    
    return render(request, 'recien_nacidos/ficha_qr.html', {'rn': rn})


# ==========================================
# GENERADOR QR ACTUALIZADO (AHORA GUARDA URL)
# ==========================================
@login_required
def generar_qr_rn(request, pk):
    """
    Genera QR que apunta a la URL de la ficha digital.
    """
    rn = get_object_or_404(RecienNacido, pk=pk)
    
    # 1. Construir la URL completa (ej: http://192.168.1.5:8000/recien-nacidos/ficha-qr/15/)
    # request.build_absolute_uri convierte la ruta relativa en una URL completa con dominio/IP
    path_relativo = reverse('recien_nacidos:ficha_qr', args=[pk])
    url_completa = request.build_absolute_uri(path_relativo)
    
    # 2. Crear QR con la URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M, # M = 15% error correction (mejor para escaneo rápido)
        box_size=10,
        border=4,
    )
    qr.add_data(url_completa)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    return HttpResponse(buffer.getvalue(), content_type="image/png")