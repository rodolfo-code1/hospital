"""
Pruebas unitarias para el modelo Usuario.
"""
import pytest
from django.core.exceptions import ValidationError
from usuarios.models import Usuario

@pytest.fixture
def usuario_base():
    """Crea un Usuario base para las pruebas."""
    return Usuario(
        username='12345678-9',
        rut='12345678-9',
        first_name='Juan',
        last_name='Pérez',
        email='juan.perez@example.com',
        rol='medico'
    )

@pytest.mark.django_db
def test_creacion_usuario(usuario_base):
    """Verifica que se pueda crear y guardar un usuario."""
    usuario_base.save()
    assert usuario_base.id is not None
    assert usuario_base.get_full_name() == 'Juan Pérez'
    assert usuario_base.get_rol_display() == 'Médico'

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
def test_rol_por_defecto():
    """Verifica que el rol por defecto sea 'administrativo'."""
    usuario = Usuario.objects.create(
        username='98765432-1',
        rut='98765432-1'
    )
    assert usuario.rol == 'administrativo'