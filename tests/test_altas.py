"""
Pruebas unitarias para el modelo Alta.
"""
import pytest
from datetime import datetime
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from altas.models import Alta

@pytest.fixture
def alta_completa():
    """Crea una madre, parto y recién nacido para el alta."""
    madre = Madre.objects.create(rut='12121212-1', nombre='Sofía Reyes', edad=25, direccion='...', telefono='...', controles_prenatales=7)
    parto = Parto.objects.create(madre=madre, tipo='natural', fecha_hora_inicio=datetime.now(), fecha_hora_termino=datetime.now(), medico_responsable='...', matrona_responsable='...')
    rn = RecienNacido.objects.create(parto=parto, sexo='F', peso=3.2, talla=49, apgar_1_min=8, apgar_5_min=9)
    return {
        'madre': madre,
        'parto': parto,
        'recien_nacido': rn
    }

@pytest.mark.django_db
def test_creacion_alta(alta_completa):
    """Verifica que se pueda crear un registro de alta."""
    alta = Alta.objects.create(
        madre=alta_completa['madre'],
        parto=alta_completa['parto'],
        recien_nacido=alta_completa['recien_nacido']
    )
    assert alta.id is not None
    assert alta.estado == 'pendiente'