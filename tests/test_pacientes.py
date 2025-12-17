
"""Pruebas unitarias para el modelo Madre."""
import pytest
from django.core.exceptions import ValidationError
from pacientes.models import Madre


@pytest.fixture
def madre_base():
    """Crea una Madre base para las pruebas."""
    return Madre(
        rut="11223344-5",
        nombre="Ana González",
        edad=30,
        direccion="Calle Falsa 123",
        telefono="+56912345678",
        comuna="Santiago",
        controles_prenatales=5,
    )

@pytest.mark.django_db
def test_creacion_madre(madre_base):
    """Verifica que se pueda crear y guardar una madre."""
    madre_base.save()
    assert madre_base.id is not None
    assert madre_base.nombre == "Ana González"
    assert madre_base.estado_alta == "hospitalizado"

@pytest.mark.django_db
def test_str_representation(madre_base):
    """Comprueba la representación en cadena de la madre."""
    madre_base.save()
    assert str(madre_base) == "Ana González (11223344-5)"

@pytest.mark.django_db
def test_edad_invalida():
    """Verifica que la edad de la madre esté dentro del rango permitido."""
    with pytest.raises(ValidationError):
        madre = Madre(rut="123", nombre="Joven", edad=9)
        madre.full_clean()

    with pytest.raises(ValidationError):
        madre = Madre(rut="123", nombre="Mayor", edad=61)
        madre.full_clean()

@pytest.mark.django_db
def test_tiene_registros_completos():
    """Evalúa la validación de registros completos de la madre."""
    madre = Madre.objects.create(
        rut="12345678-9",
        nombre="María Test",
        edad=27,
        direccion="Calle 1",
        telefono="1111",
        controles_prenatales=3,
    )
    assert madre.tiene_registros_completos() is False

    madre.comuna = "Providencia"
    madre.save()
    assert madre.tiene_registros_completos() is True