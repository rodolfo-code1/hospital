# pégalo en pacientes/tests.py

"""
Pruebas unitarias para el modelo Madre.
"""
import pytest
from django.core.exceptions import ValidationError
from pacientes.models import Madre


@pytest.fixture
def madre_base():
    """Crea una Madre base para las pruebas."""
    return Madre(
        rut='11223344-5',
        nombre='Ana González',
        edad=30,
        direccion='Calle Falsa 123',
        telefono='+56912345678',
        controles_prenatales=5
    )

@pytest.mark.django_db
def test_creacion_madre(madre_base):
    """Verifica que se pueda crear y guardar una madre."""
    madre_base.save()
    assert madre_base.id is not None
    assert madre_base.nombre == 'Ana González'

@pytest.mark.django_db
def test_str_representation(madre_base):
    """Comprueba la representación en cadena de la madre."""
    assert str(madre_base) == "Ana González (11223344-5)"

@pytest.mark.django_db
def test_edad_invalida():
    """Verifica que la edad de la madre esté dentro del rango permitido."""
    with pytest.raises(ValidationError):
        madre = Madre(rut='123', nombre='Joven', edad=10)
        madre.full_clean()

    with pytest.raises(ValidationError):
        madre = Madre(rut='123', nombre='Mayor', edad=70)
        madre.full_clean()