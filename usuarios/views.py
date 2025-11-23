# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistroUsuarioForm,EditarUsuarioForm
from .models import Usuario
from .decorators import encargado_ti_requerido

def registro_view(request):
    """Vista de auto-registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('app:home')  
    
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Cuenta creada exitosamente. Bienvenido {user.get_full_name()} como {user.get_rol_display()}'
            )
            login(request, user)
            return redirect('app:home')  # <--- CAMBIO AQUÍ
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    """Vista de inicio de sesión"""
    if request.user.is_authenticated:
        return redirect('app:home')  # <--- CAMBIO AQUÍ
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.get_full_name()} ({user.get_rol_display()})')
            
            # CAMBIO IMPORTANTE AQUÍ ABAJO:
            # Redirigir al 'next' si existe, si no al dashboard 'altas:home'
            next_url = request.GET.get('next', 'app:home') 
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

# ==========================================
# GESTIÓN DE USUARIOS (ENCARGADO TI)
# ==========================================

@login_required
@encargado_ti_requerido
def gestion_usuarios(request):
    """Lista todos los usuarios del sistema"""
    usuarios = Usuario.objects.all().order_by('-date_joined')
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@login_required
@encargado_ti_requerido
def crear_usuario_interno(request):
    """Permite al TI crear un usuario manualmente"""
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.get_full_name()} creado correctamente.')
            return redirect('usuarios:gestion_usuarios')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/form_usuario.html', {
        'form': form,
        'titulo': 'Crear Nuevo Usuario',
        'btn_texto': 'Crear Usuario'
    })

@login_required
@encargado_ti_requerido
def editar_usuario(request, pk):
    """Permite editar un usuario existente"""
    usuario = get_object_or_404(Usuario, pk=pk)
    
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.rut} actualizado correctamente.')
            return redirect('usuarios:gestion_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)
    
    return render(request, 'usuarios/form_usuario.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario.rut}',
        'btn_texto': 'Guardar Cambios'
    })