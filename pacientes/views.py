from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from .models import Madre
from .forms import MadreForm, MadreRecepcionForm
from usuarios.decorators import rol_requerido
from usuarios.models import Usuario
from app.models import Notificacion

@login_required
def registrar_madre_recepcion(request):
    if request.user.rol not in ['recepcionista', 'jefatura', 'encargado_ti']:
         messages.error(request, "No tienes permiso para acceder a Admisión.")
         return redirect('app:home')

    if request.method == 'POST':
        # Obtenemos el RUT crudo para buscar
        rut_raw = request.POST.get('rut', '').replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_raw[:-1]}-{rut_raw[-1]}" if len(rut_raw) > 1 else rut_raw
        
        # Buscamos si ya existe
        madre_existente = Madre.objects.filter(rut=rut_formateado).first()
        
        if madre_existente:
            # --- CASO A: YA EXISTE ---
            if madre_existente.estado_alta == 'hospitalizado':
                messages.warning(request, f'La paciente {madre_existente.nombre} ya está activa en el sistema.')
                return redirect('app:home')
            else:
                # --- REINGRESO (Estaba de alta) ---
                form = MadreRecepcionForm(request.POST, instance=madre_existente)
                if form.is_valid():
                    madre = form.save(commit=False)
                    
                    # ACTUALIZACIÓN CLAVE PARA PERMITIR NUEVO PARTO
                    madre.estado_alta = 'hospitalizado'
                    madre.fecha_ingreso = timezone.now() # <--- ¡Importante! Reinicia el ciclo
                    madre.estado_salud = 'observacion'
                    madre.save()
                    
                    # Notificar Reingreso
                    crear_notificacion(madre, reingreso=True)
                    
                    messages.success(request, f'REINGRESO EXITOSO: Paciente {madre.nombre} activada para nuevo proceso.')
                    return redirect('app:home')
        else:
            # --- CASO B: NUEVA ---
            form = MadreRecepcionForm(request.POST)
            if form.is_valid():
                madre = form.save(commit=False)
                madre.creado_por = request.user
                madre.save()
                
                # Notificar Nuevo Ingreso
                crear_notificacion(madre, reingreso=False)
                
                messages.success(request, f'Paciente {madre.nombre} registrada exitosamente.')
                return redirect('app:home')
    else:
        form = MadreRecepcionForm()
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form,
        'titulo': 'Admisión y Reingreso',
        'subtitulo': 'Ingrese RUT para registrar nueva o reingresar antigua.'
    })

def crear_notificacion(madre, reingreso=False):
    """Función auxiliar para notificar a las matronas"""
    tiene_alerta = bool(madre.alerta_recepcion)
    tipo_noti = 'urgente' if tiene_alerta else 'info'
    titulo_pre = "🚨 ALERTA" if tiene_alerta else ("🔄 REINGRESO" if reingreso else "Nuevo Ingreso")
    
    mensaje = f"Paciente: {madre.nombre}\nRUT: {madre.rut}"
    if tiene_alerta: mensaje += f"\n⚠️: {madre.alerta_recepcion}"
    
    matronas = Usuario.objects.filter(rol='matrona')
    objs = [Notificacion(usuario=m, titulo=titulo_pre, mensaje=mensaje, tipo=tipo_noti, link=f"/pacientes/completar/{madre.pk}/") for m in matronas]
    Notificacion.objects.bulk_create(objs)

# ... (Resto de vistas: lista_pacientes, ver_ficha, editar, etc. se mantienen igual)
@login_required
def lista_pacientes(request):
    # Mostrar solo las que están HOSPITALIZADAS para no llenar la lista de antiguas
    madres = Madre.objects.filter(estado_alta='hospitalizado').order_by('-fecha_ingreso')
    query = request.GET.get('q')
    if query:
        madres = madres.filter(Q(rut__icontains=query) | Q(nombre__icontains=query))
    return render(request, 'pacientes/lista_pacientes.html', {'madres': madres, 'query': query})

@login_required
def ver_ficha_clinica(request, pk):
    madre = get_object_or_404(Madre, pk=pk)
    form = MadreForm(instance=madre)
    for field in form.fields.values(): field.widget.attrs['disabled'] = True
    return render(request, 'pacientes/ver_ficha.html', {'form': form, 'madre': madre, 'titulo': 'Ficha Clínica'})

@login_required
def editar_ficha_clinica(request, pk):
    madre = get_object_or_404(Madre, pk=pk)
    if request.method == 'POST':
        form = MadreForm(request.POST, instance=madre)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ficha actualizada.')
            return redirect('pacientes:ver_ficha', pk=madre.pk)
    else:
        form = MadreForm(instance=madre)
    return render(request, 'pacientes/registrar_madre.html', {'form': form, 'titulo': 'Editar Ficha', 'subtitulo': f'{madre.nombre}'})

# Redirecciones compatibilidad
@login_required
def registrar_madre(request): return redirect('pacientes:admision_madre')
@login_required
def buscar_madre(request): return redirect('pacientes:lista_pacientes')
@login_required
def completar_madre(request, pk): return redirect('pacientes:ver_ficha', pk=pk)