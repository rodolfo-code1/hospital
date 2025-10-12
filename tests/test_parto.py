"""
Pruebas unitarias para el modelo Parto.
"""
import pytest
from datetime import datetime
from pacientes.models import Madre
from partos.models import Parto

@pytest.fixture
def madre_parto():
    """Crea una madre para asociarla al parto."""
    return Madre.objects.create(
        rut='55667788-9',
        nombre='Carla López',
        edad=28,
        direccion='Av. Siempreviva 742',
        telefono='555-1234',
        controles_prenatales=8
    )

@pytest.mark.django_db
def test_creacion_parto(madre_parto):
    """Verifica que se pueda crear y guardar un parto."""
    parto = Parto.objects.create(
        madre=madre_parto,
        tipo='natural',
        fecha_hora_inicio=datetime.now(),
        medico_responsable='Dr. House',
        matrona_responsable='Mat. Cameron'
    )
    assert parto.id is not None
    assert parto.madre.nombre == 'Carla López'