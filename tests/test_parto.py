"""Pruebas unitarias para el modelo Parto."""
import pytest
from django.utils import timezone
from pacientes.models import Madre
from partos.models import Parto

@pytest.fixture
def madre_parto():
    """Crea una madre para asociarla al parto."""
    return Madre.objects.create(
        rut="55667788-9",
        nombre="Carla López",
        edad=28,
        direccion="Av. Siempreviva 742",
        telefono="555-1234",
        comuna="Providencia",
        controles_prenatales=8,
    )

@pytest.mark.django_db
def test_creacion_parto(madre_parto):
    """Verifica que se pueda crear y guardar un parto."""
    parto = Parto.objects.create(
        madre=madre_parto,
        tipo="eutocico",
        fecha_hora_inicio=timezone.now(),
        fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. House",
        matrona_responsable="Mat. Cameron",
    )
    assert parto.id is not None
    assert parto.madre.nombre == "Carla López"
    assert parto.tiene_registros_completos() is True

@pytest.mark.django_db
def test_parto_incompleto(madre_parto):
    """Valida que se detecten partos con información faltante."""
    parto = Parto.objects.create(
        madre=madre_parto,
        tipo="eutocico",
        fecha_hora_inicio=timezone.now(),
        medico_responsable="Dr. House",
        matrona_responsable="Mat. Cameron",
    )
    assert parto.tiene_registros_completos() is False

    parto.fecha_hora_termino = timezone.now()
    parto.save()
    assert parto.tiene_registros_completos() is True