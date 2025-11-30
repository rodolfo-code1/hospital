from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Madre
from .forms import MadreForm, MadreRecepcionForm
from usuarios.decorators import rol_requerido

# --- VISTA RECEPCIONISTA: Ingreso Total ---
@login_required
def registrar_madre_recepcion(request):
    if request.user.rol not in ['recepcionista', 'jefatura', 'encargado_ti']:
         messages.error(request, "No tienes permiso para acceder a Admisión.")
         return redirect('app:home')

    if request.method == 'POST':
        form = MadreRecepcionForm(request.POST)
        if form.is_valid():
            madre = form.save(commit=False)
            madre.creado_por = request.user
            madre.save()
            messages.success(request, f'Paciente {madre.nombre} registrada exitosamente.')
            return redirect('app:home')
    else:
        form = MadreRecepcionForm()
    
    context = {
        'form': form,
        'titulo': 'Admisión e Ingreso Clínico',
        'subtitulo': 'Registro completo de paciente (Recepción)'
    }
    return render(request, 'pacientes/registrar_madre.html', context)

# --- VISTA MATRONA: Listado ---
@login_required
def lista_pacientes(request):
    madres = Madre.objects.all().order_by('-fecha_ingreso')
    query = request.GET.get('q')
    if query:
        madres = madres.filter(Q(rut__icontains=query) | Q(nombre__icontains=query))
    return render(request, 'pacientes/lista_pacientes.html', {'madres': madres, 'query': query})

# --- VISTA MATRONA: Ver Ficha (Solo Lectura) ---
@login_required
def ver_ficha_clinica(request, pk):
    """
    Muestra los datos bloqueados. 
    Si quiere editar, debe presionar el botón 'Editar'.
    """
    madre = get_object_or_404(Madre, pk=pk)
    form = MadreForm(instance=madre)
    
    # Bloquear todos los campos para que sea "Solo Lectura"
    for field in form.fields.values():
        field.widget.attrs['disabled'] = True

    return render(request, 'pacientes/ver_ficha.html', {
        'form': form,
        'madre': madre, # Pasamos el objeto para sacar el ID en el botón editar
        'titulo': 'Ficha Clínica (Vista Previa)'
    })

# --- VISTA MATRONA: Editar Ficha (Edición Real) ---
@login_required
def editar_ficha_clinica(request, pk):
    madre = get_object_or_404(Madre, pk=pk)
    
    if request.method == 'POST':
        form = MadreForm(request.POST, instance=madre)
        if form.is_valid():
            form.save()
            messages.success(request, f'Ficha de {madre.nombre} actualizada.')
            return redirect('pacientes:ver_ficha', pk=madre.pk) # Vuelve a la vista de lectura
    else:
        form = MadreForm(instance=madre)
    
    return render(request, 'pacientes/registrar_madre.html', {
        'form': form,
        'titulo': 'Editar Ficha Clínica',
        'subtitulo': f'Modificando datos de: {madre.nombre}'
    })

# (Mantenemos estas por compatibilidad si se usan en otro lado, o se pueden borrar)
@login_required
def registrar_madre(request):
    return redirect('pacientes:admision_madre')

@login_required
def buscar_madre(request):
    return redirect('pacientes:lista_pacientes')

@login_required
def completar_madre(request, pk):
    return redirect('pacientes:ver_ficha', pk=pk)