# usuarios/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import RegistroUsuarioForm

def registro_view(request):
    """Vista de auto-registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('altas:lista_altas')
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Cuenta creada exitosamente. Bienvenido {user.get_full_name()} como {user.get_rol_display()}'
            )
            # Iniciar sesión automáticamente después del registro
            login(request, user)
            return redirect('altas:lista_altas')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('altas:lista_altas')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.get_full_name()} ({user.get_rol_display()})')
            
            # Redirigir según el parámetro 'next' o a la página principal
            next_url = request.GET.get('next', 'altas:lista_altas')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'usuarios/login.html')

@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente')
    return redirect('usuarios:login')

@login_required
def perfil_view(request):
    """Vista del perfil del usuario"""
    context = {
        'usuario': request.user
    }
    return render(request, 'usuarios/perfil.html', context)