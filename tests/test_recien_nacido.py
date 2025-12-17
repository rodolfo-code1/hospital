"""Pruebas unitarias para el modelo RecienNacido."""

import pytest
from django.utils import timezone
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

@pytest.fixture
def parto_rn():
    """Crea un parto para asociarlo al recién nacido."""
    madre = Madre.objects.create(
        rut="99887766-5",
        nombre="Laura Soto",
        edad=32,
        direccion="...",
        telefono="...",
        comuna="La Florida",
        controles_prenatales=6,
    )
    return Parto.objects.create(
        madre=madre,
        tipo="eutocico",
        fecha_hora_inicio=timezone.now(),
        fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. Strange",
        matrona_responsable="Mat. Palmer",
    )

@pytest.mark.django_db
def test_creacion_recien_nacido(parto_rn):
    """Verifica la creación de un recién nacido y la generación del código único."""
    rn = RecienNacido.objects.create(
        parto=parto_rn,
        sexo="M",
        peso=3.5,
        talla=50,  # <--- AGREGAR ESTA LÍNEA
        apgar_1_min=0,
        apgar_5_min=0,
        ap1_latidos=2,
        ap1_respiracion=2,
        ap1_tono=2,
        ap1_reflejos=2,
        ap1_color=2,
        ap5_latidos=2,
        ap5_respiracion=2,
        ap5_tono=2,
        ap5_reflejos=2,
        ap5_color=2,
    )
    assert rn.id is not None
    assert rn.codigo_unico.startswith("RN-")
    assert rn.apgar_1_min == 10
    assert rn.apgar_5_min == 10

@pytest.mark.django_db
def test_registros_completos(parto_rn):
    """Comprueba la lógica de registros completos del RN."""
    rn = RecienNacido.objects.create(
        parto=parto_rn,
        sexo="F",
        peso=2.9,
        talla=48,
        apgar_1_min=0,
        apgar_5_min=0,
    )
    assert rn.tiene_registros_completos() is True