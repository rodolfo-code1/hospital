# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .forms import RegistroUsuarioForm,EditarUsuarioForm, ResetPasswordRUTForm
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

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Usuario

def login_view(request):
    """Vista de inicio de sesión robusta"""
    if request.user.is_authenticated:
        return redirect('app:home')
    
    if request.method == 'POST':
        raw_username = request.POST.get('username', '')
        password = request.POST.get('password')
        
        # Limpieza del RUT: eliminar puntos y guiones
        username_limpio = raw_username.replace('.', '').replace('-', '')
        
        
        user = authenticate(request, username=username_limpio, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenido {user.get_full_name()}')
            next_url = request.GET.get('next', 'app:home')
            return redirect(next_url)
        else:
            messages.error(request, 'RUT o contraseña incorrectos.')
    
    return render(request, 'usuarios/login.html')

  
def solicitar_reset_pw(request):
    if request.method == 'POST':
        form = ResetPasswordRUTForm(request.POST)
        if form.is_valid():
            rut = form.cleaned_data['rut'].replace(".", "").upper()

            try:
                user = Usuario.objects.get(rut=rut)
            except Usuario.DoesNotExist:
                user = None

            # No revelar información (seguridad)
            if user and user.email and user.is_active:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                reset_link = f"http://{request.get_host()}/usuarios/reset/{uid}/{token}/"

                mensaje = (
                    f"Hola {user.get_full_name()},\n\n"
                    f"Has solicitado restablecer tu contraseña.\n"
                    f"Ingrese al siguiente enlace (válido solo una vez):\n\n"
                    f"{reset_link}\n\n"
                    f"Si no solicitaste este cambio, ignora este correo."
                )

                send_mail(
                    "Restablecimiento de Contraseña",
                    mensaje,
                    settings.EMAIL_FROM,
                    [user.email],
                )

            # Mensaje neutro SIEMPRE, aunque esté inactivo, no tenga correo o no exista
            messages.info(
                request,
                "Si el RUT está registrado y activo, recibirás un correo con instrucciones."
            )
            return redirect('usuarios:login')

    else:
        form = ResetPasswordRUTForm()

    return render(request, 'usuarios/reset_password_rut.html', {'form': form})
  
def reset_password_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Usuario.objects.get(pk=uid)
    except:
        user = None

    # Verifica token válido y 1 solo uso
    if user is None or not default_token_generator.check_token(user, token):
        messages.error(request, "El enlace no es válido o ha expirado.")
        return redirect('usuarios:login')

    if request.method == "POST":
        nueva = request.POST.get("password1")
        repetir = request.POST.get("password2")

        if not nueva or not repetir:
            messages.error(request, "Debes completar ambos campos.")
            return redirect(request.path)

        if nueva != repetir:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(request.path)

        if len(nueva) < 6:
            messages.error(request, "La contraseña debe tener mínimo 6 caracteres.")
            return redirect(request.path)

        # Guardar contraseña nueva
        user.password = make_password(nueva)
        user.save()

        messages.success(request, "Contraseña restablecida correctamente.")
        return redirect("usuarios:login")

    return render(request, "usuarios/reset_password_confirm.html", {"user": user})

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
    q = request.GET.get('q', '').strip()
    usuarios = Usuario.objects.all().order_by('-date_joined')

    if q:
        usuarios = usuarios.filter(
            Q(rut__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(rol__icontains=q)
        )

    return render(request, 'usuarios/lista_usuarios.html', {
        'usuarios': usuarios,
        'q': q
    })

@login_required
@encargado_ti_requerido
def obtener_usuarios(request):
    q = request.GET.get('q', '').strip()
    usuarios = Usuario.objects.all()

    if q:
        usuarios = usuarios.filter(
            Q(rut__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(rol__icontains=q)
        )

    tabla_html = render_to_string('usuarios/partials/obtener_usuarios.html', {
        'usuarios': usuarios
    })

    return JsonResponse({'tabla': tabla_html})

@login_required
@encargado_ti_requerido
def crear_usuario_interno(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()

            # ================================
            # Generar token de activación
            # ================================
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            domain = get_current_site(request).domain
            activation_link = f"http://{domain}/usuarios/activar/{uid}/{token}/"

            asunto = "Activación de Cuenta - Sistema de Trazabilidad"
            mensaje = (
                f"Hola {user.get_full_name()},\n\n"
                f"Has sido registrado en el sistema.\n"
                f"Para activar tu cuenta y crear tu contraseña, ingresa al siguiente enlace:\n\n"
                f"{activation_link}\n\n"
                f"⚠️ Este enlace caduca en 24 horas.\n\n"
                f"Si no solicitaste esta cuenta, ignora este mensaje."
            )

            send_mail(
                subject=asunto,
                message=mensaje,
                from_email=settings.EMAIL_FROM,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(request, "Usuario creado y correo de activación enviado correctamente.")
            return redirect('usuarios:gestion_usuarios')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'usuarios/form_usuario.html', {
        'form': form,
        'titulo': 'Crear Nuevo Usuario',
        'btn_texto': 'Crear Usuario',
        'es_edicion': False
    })

def activar_usuario(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Usuario.objects.get(pk=uid)
    except:
        user = None

    if user and default_token_generator.check_token(user, token):
        # 🔥 No activamos aquí, solo mostramos el form para crear clave
        return render(request, "usuarios/crear_password.html", {
            "uidb64": uidb64,
            "token": token
        })
    else:
        messages.error(request, "El enlace de activación no es válido o ha expirado.")
        return redirect('usuarios:login')
      
def crear_password_activacion(request):
    if request.method == "POST":
        uidb64 = request.POST.get("uidb64")
        token = request.POST.get("token")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Usuario.objects.get(pk=uid)
        except:
            user = None

        if not user or not default_token_generator.check_token(user, token):
            messages.error(request, "El enlace ya expiró o no es válido.")
            return redirect('usuarios:login')

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect(request.path)

        if len(password1) < 8:
            messages.error(request, "La contraseña debe tener mínimo 8 caracteres.")
            return redirect(request.path)

        # activar y guardar contraseña
        user.set_password(password1)
        user.is_active = True
        user.save()

        messages.success(request, "Contraseña creada exitosamente. Ahora puedes iniciar sesión.")
        return redirect('usuarios:login')

@login_required
@encargado_ti_requerido
def editar_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)

    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.get_full_name()} actualizado correctamente.')
            return redirect('usuarios:gestion_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario)

    return render(request, 'usuarios/form_usuario.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario.get_full_name()}',
        'btn_texto': 'Guardar Cambios',
        'es_edicion': True,
    })