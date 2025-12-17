# hospital/recien_nacidos/views.py
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
    """
    Vista principal para el ingreso del Recién Nacido (Matrona).
    Guarda los datos clínicos, calcula Apgar y asigna el código único.
    """
    if request.method == 'POST':
        form = RecienNacidoForm(request.POST)
        if form.is_valid():
            rn = form.save(commit=False)
            rn.creado_por = request.user # Auditoría
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
    Buscador administrativo para gestión de identificación.
    Permite encontrar un RN por su código único, o por el nombre/rut de la madre.
    Utilizado para reimprimir brazaletes o verificar identidades.
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
    """
    Vista previa de impresión del brazalete de identificación del bebé.
    Muestra datos críticos: Nombre Madre, Fecha Nacimiento, Sexo, Código Único.
    """
    rn = get_object_or_404(RecienNacido, pk=pk)
    return render(request, 'recien_nacidos/brazalete_rn.html', {'rn': rn})

@login_required
def ficha_qr(request, pk):
    """
    Ficha Digital Móvil (Destino del escaneo QR).
    Muestra un resumen clínico rápido del binomio Madre-Hijo.
    Requiere autenticación para proteger la privacidad del paciente.
    """
    rn = get_object_or_404(RecienNacido, pk=pk)
    # Se accede a los datos de la madre a través de la relación: rn.parto.madre
    
    return render(request, 'recien_nacidos/ficha_qr.html', {'rn': rn})


# ==========================================
# GENERADOR QR DINÁMICO
# ==========================================
@login_required
def generar_qr_rn(request, pk):
    """
    Genera una imagen PNG con un código QR al vuelo.
    Este QR contiene la URL única que dirige a la 'ficha_qr' del bebé.
    """
    rn = get_object_or_404(RecienNacido, pk=pk)
    
    # 1. Construir la URL absoluta
    # reverse() obtiene la ruta relativa (/ficha/123/)
    # request.build_absolute_uri() le agrega el dominio (http://dominio.com/ficha/123/)
    path_relativo = reverse('recien_nacidos:ficha_qr', args=[pk])
    url_completa = request.build_absolute_uri(path_relativo)
    
    # 2. Configurar y generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M, # M = Nivel medio, robusto a daños
        box_size=10,
        border=4,
    )
    qr.add_data(url_completa)
    qr.make(fit=True)

    # 3. Renderizar imagen en memoria (Buffer) para enviar como respuesta HTTP
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer)
    return HttpResponse(buffer.getvalue(), content_type="image/png")