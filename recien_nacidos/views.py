from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import RecienNacidoForm

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