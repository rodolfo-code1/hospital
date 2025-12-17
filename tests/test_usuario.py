"""
Pruebas unitarias para el modelo Usuario.
"""
from datetime import datetime, timedelta
import pytest
from django.core.exceptions import ValidationError
from usuarios.models import Usuario
from django.utils import timezone

from usuarios.models import AuditoriaLogin, AuditoriaModificacion, CodigoLogin, Usuario

@pytest.fixture
def usuario_base():
    """Crea un Usuario base para las pruebas."""
    return Usuario(
        username="12345678-9",
        rut="12345678-9",
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@example.com",
        rol="medico",
    )

@pytest.fixture
def usuario_guardado(db):
    """Usuario persistido para probar relaciones."""
    return Usuario.objects.create_user(
        username="98765432-1",
        password="dummy-pass",
        rut="98765432-1",
        first_name="Ana",
        last_name="López",
        email="ana.lopez@example.com",
        rol="administrativo",
    )

@pytest.mark.django_db
def test_creacion_usuario(usuario_base):
    """Verifica que se pueda crear y guardar un usuario."""
    usuario_base.save()
    assert usuario_base.id is not None
    assert usuario_base.get_full_name() == "Juan Pérez"
    assert usuario_base.get_rol_display() == "Médico"

@pytest.mark.django_db
def test_str_representation(usuario_base):
    """Comprueba la representación en cadena del usuario."""
    assert str(usuario_base) == "Juan Pérez - Médico"

@pytest.mark.django_db
def test_rut_obligatorio():
    """Verifica que el campo RUT es obligatorio."""
    with pytest.raises(ValidationError):
        usuario = Usuario(first_name='Incompleto')
        usuario.full_clean()

@pytest.mark.django_db
def test_rol_por_defecto(usuario_guardado):
    """Verifica que el rol por defecto sea 'administrativo'."""
    # Usamos un RUT diferente al del fixture (que es 98765432-1)
    usuario = Usuario.objects.create(
        username="11223344-5", 
        rut="11223344-5"
    )
    assert usuario.rol == "administrativo"
    
    # También puedes verificar el del fixture si lo deseas
    assert usuario_guardado.es_administrativo()
@pytest.mark.django_db
def test_flags_de_roles(usuario_base):
    """Valida los helpers para roles específicos."""
    usuario_base.save()
    assert usuario_base.es_medico()
    assert not usuario_base.es_administrativo()
    assert not usuario_base.es_supervisor()
    assert not usuario_base.es_encargado_ti()
    assert not usuario_base.es_recepcionista()


@pytest.mark.django_db
def test_auditoria_login_str(usuario_guardado):
    """La representación incluye el usuario, tipo de evento y fecha."""
    fecha = timezone.make_aware(datetime(2024, 5, 15, 12, 0, 0))
    audit = AuditoriaLogin.objects.create(
        usuario=usuario_guardado,
        tipo_evento="login",
        direccion_ip="127.0.0.1",
        exitoso=True,
    )
    audit.fecha_evento = fecha
    audit.save(update_fields=["fecha_evento"])

    assert (
        str(audit)
        == "Ana López - Inicio de Sesión - 15/05/2024 12:00"
    )

@pytest.mark.django_db
def test_auditoria_login_nombre_fallback():
    """Cuando no hay usuario, se usa el nombre ingresado."""
    fecha = timezone.make_aware(datetime(2024, 6, 1, 9, 30, 0))
    audit = AuditoriaLogin.objects.create(
        usuario=None,
        nombre_usuario="usuario_invitado",
        tipo_evento="login_fallido",
        exitoso=False,
    )
    audit.fecha_evento = fecha
    audit.save(update_fields=["fecha_evento"])

    assert (
        str(audit)
        == "usuario_invitado - Login Fallido - 01/06/2024 09:30"
    )


@pytest.mark.django_db
def test_auditoria_modificacion_str(usuario_guardado):
    """La representación de AuditoriaModificacion incluye modelo y operación."""
    fecha = timezone.make_aware(datetime(2024, 7, 10, 18, 45, 0))
    auditoria = AuditoriaModificacion.objects.create(
        usuario=usuario_guardado,
        tipo_operacion="update",
        modelo="Paciente",
        id_objeto=42,
        descripcion="Actualización de domicilio",
    )
    auditoria.fecha_evento = fecha
    auditoria.save(update_fields=["fecha_evento"])

    assert (
        str(auditoria)
        == "Modificación - Paciente (ID: 42) - 10/07/2024 18:45"
    )


@pytest.mark.django_db
def test_codigo_login_validaciones(usuario_guardado, monkeypatch):
    """Comprueba la validez del código dentro y fuera de la ventana permitida."""
    base_time = timezone.make_aware(datetime(2024, 8, 20, 10, 0, 0))
    monkeypatch.setattr(timezone, "now", lambda: base_time)

    codigo = CodigoLogin.objects.create(usuario=usuario_guardado, codigo="123456")

    assert codigo.es_valido()

    codigo.usado = True
    codigo.save(update_fields=["usado"])
    assert not codigo.es_valido()


    # Simula paso del tiempo más allá de la ventana de 5 minutos
    monkeypatch.setattr(
        timezone, "now", lambda: base_time + timedelta(minutes=6)
    )
    codigo.usado = False
    codigo.creado = base_time
    codigo.save(update_fields=["usado", "creado"])

    assert not codigo.es_valido()