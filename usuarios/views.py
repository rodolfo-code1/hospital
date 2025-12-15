# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
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
from .models import Usuario, AuditoriaLogin
from .decorators import encargado_ti_requerido
from django.http import HttpRequest

def get_client_ip(request: HttpRequest):
    """Obtiene la IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def registrar_login(request, usuario, exitoso=True, razon_fallo=''):
    """Registra el intento de login en la auditoría"""
    try:
        # Asegurar que la sesión tenga session_key (si ya existe)
        session_key = None
        try:
            session_key = request.session.session_key
        except Exception:
            session_key = None

        AuditoriaLogin.objects.create(
            usuario=usuario,
            tipo_evento='login' if exitoso else 'login_fallido',
            direccion_ip=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            session_key=session_key,
            nombre_usuario=usuario.username if usuario else request.POST.get('username', ''),
            exitoso=exitoso,
            razon_fallo=razon_fallo
        )
    except Exception as e:
        print(f"Error registrando login: {e}")

def registrar_logout(request):
    """Registra el logout en la auditoría"""
    try:
        if request.user.is_authenticated:
            session_key = None
            try:
                session_key = request.session.session_key
            except Exception:
                session_key = None

            AuditoriaLogin.objects.create(
                usuario=request.user,
                tipo_evento='logout',
                direccion_ip=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                session_key=session_key,
                exitoso=True
            )
    except Exception as e:
        print(f"Error registrando logout: {e}")

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
            return redirect('app:home')
    else:
        form = RegistroUsuarioForm()
    
    return render(request, 'usuarios/registro.html', {'form': form})

from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Usuario
from django.contrib.auth import get_user_model
from .models import CodigoLogin
import random

Usuario = get_user_model()

# hospital/usuarios/views.py

def login_view(request):
    # ... (validaciones de usuario y contraseña anteriores se mantienen igual) ...
    # ... if not user.check_password ... etc ...

    if not user.is_active:
        messages.error(request, 'Cuenta desactivada.')
        return render(request, 'usuarios/login.html')

    # === INICIO DE LA LÓGICA DE EXCEPCIÓN QR ===
    
    # 1. Detectamos a dónde quiere ir el usuario
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    
    # 2. Definimos las rutas "seguras" que no piden 2FA (Las del QR)
    # Estas palabras deben coincidir con tus URLs de fichas
    rutas_exentas_2fa = ['/ficha-qr/', '/ficha-digital/']
    
    # 3. Verificamos si el destino contiene alguna ruta exenta
    es_acceso_qr = any(ruta in next_url for ruta in rutas_exentas_2fa)

    if es_acceso_qr:
        # --> CASO QR: Login directo (Saltar 2FA)
        login(request, user)
        registrar_login(request, user, exitoso=True)
        messages.success(request, f'Bienvenido(a) {user.first_name}')
        return redirect(next_url)
        
    # === FIN DE LA LÓGICA QR ===

    # --> CASO NORMAL: Flujo de 2FA (Correo)
    enviar_codigo_login(user)
    request.session['2fa_user_id'] = user.id

    messages.info(request, 'Te enviamos un código a tu correo.')
    
    # Mantenemos el 'next' para que funcione el arreglo anterior
    response = redirect('usuarios:verificar_codigo')
    if next_url:
        response['Location'] += f'?next={next_url}'
        
    return response

def enviar_codigo_login(usuario):
    codigo = str(random.randint(100000, 999999))

    CodigoLogin.objects.create(
        usuario=usuario,
        codigo=codigo
    )

    send_mail(
        subject="Código de acceso - Sistema de Trazabilidad",
        message=(
            f"Hola {usuario.get_full_name()},\n\n"
            f"Tu código de acceso es:\n\n"
            f"{codigo}\n\n"
            f"Este código es válido por 5 minutos."
        ),
        from_email=settings.EMAIL_FROM,
        recipient_list=[usuario.email],
        fail_silently=False,
    )

def verificar_codigo(request):
    user_id = request.session.get('2fa_user_id')

    if not user_id:
        return redirect('usuarios:login')

    user = Usuario.objects.get(id=user_id)
    
    # --- CAMBIO 1: Capturar el next de la URL o del formulario ---
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo')

        try:
            codigo = CodigoLogin.objects.filter(
                usuario=user,
                codigo=codigo_ingresado,
                usado=False
            ).latest('creado')
        except CodigoLogin.DoesNotExist:
            # ... (tus mensajes de error) ...
            # Importante: Pasar next de vuelta en el redirect de error si quieres persistencia total
            return redirect('usuarios:verificar_codigo') 
        
        if not codigo.es_valido():
            # ... (tus mensajes de error) ...
            return redirect('usuarios:verificar_codigo')

        # Código válido
        codigo.usado = True
        codigo.save()

        login(request, user)
        registrar_login(request, user, exitoso=True)

        del request.session['2fa_user_id']

        messages.success(request, f'Bienvenido {user.get_full_name()}')
        
        # --- CAMBIO 2: Redirigir a la ficha QR si existe next ---
        if next_url:
            return redirect(next_url)
        return redirect('app:home')

    # --- CAMBIO 3: Pasar la variable 'next' al template HTML ---
    return render(request, 'usuarios/verificar_codigo.html', {'next': next_url})
 
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
    registrar_logout(request)
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

    usuarios = Usuario.objects.filter(
        is_superuser=False
    ).order_by('-date_joined')

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

    usuarios = Usuario.objects.filter(is_superuser=False)

    if q:
        usuarios = usuarios.filter(
            Q(rut__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(rol__icontains=q)
        )

    tabla_html = render_to_string(
        'usuarios/partials/obtener_usuarios.html',
        {'usuarios': usuarios}
    )

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
        except Exception:
            user = None

        # Token inválido
        if not user or not default_token_generator.check_token(user, token):
            messages.error(request, "El enlace ya expiró o no es válido.")
            return redirect('usuarios:login')

        # Contraseñas distintas
        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "usuarios/crear_password.html", {
                "uidb64": uidb64,
                "token": token
            })

        # Contraseña muy corta
        if len(password1) < 8:
            messages.error(request, "La contraseña debe tener mínimo 8 caracteres.")
            return render(request, "usuarios/crear_password.html", {
                "uidb64": uidb64,
                "token": token
            })

        # ✅ Activar usuario y guardar contraseña
        user.set_password(password1)
        user.is_active = True
        user.save()

        messages.success(
            request,
            "Contraseña creada exitosamente. Ahora puedes iniciar sesión."
        )
        return redirect('usuarios:login')

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
