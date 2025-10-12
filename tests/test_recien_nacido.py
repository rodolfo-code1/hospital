"""
Pruebas unitarias para el modelo RecienNacido.
"""
import pytest
from datetime import datetime
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

@pytest.fixture
def parto_rn():
    """Crea un parto para asociarlo al recién nacido."""
    madre = Madre.objects.create(rut='99887766-5', nombre='Laura Soto', edad=32, direccion='...', telefono='...', controles_prenatales=6)
    return Parto.objects.create(
        madre=madre,
        tipo='cesarea',
        fecha_hora_inicio=datetime.now(),
        medico_responsable='Dr. Strange',
        matrona_responsable='Mat. Palmer'
    )

@pytest.mark.django_db
def test_creacion_recien_nacido(parto_rn):
    """Verifica la creación de un recién nacido y la generación del código único."""
    rn = RecienNacido.objects.create(
        parto=parto_rn,
        sexo='M',
        peso=3.5,
        talla=50,
        apgar_1_min=9,
        apgar_5_min=10
    )
    assert rn.id is not None
    assert rn.codigo_unico.startswith('RN-')