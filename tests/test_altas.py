"""
Pruebas unitarias para el modelo Alta.
"""
import pytest
from django.utils import timezone
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido
from altas.models import Alta

@pytest.fixture
def madre_completa():
    return Madre.objects.create(
        rut="12121212-1",
        nombre="Sofía Reyes",
        edad=25,
        direccion="...",
        telefono="...",
        comuna="Ñuñoa",
        controles_prenatales=7,
    )


@pytest.fixture
def parto_completo(madre_completa):
    return Parto.objects.create(
        madre=madre_completa,
        tipo="eutocico",
        fecha_hora_inicio=timezone.now(),
        fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. House",
        matrona_responsable="Mat. Cuddy",
    )


@pytest.fixture
def recien_nacido_completo(parto_completo):
    return RecienNacido.objects.create(
        parto=parto_completo,
        sexo="F",
        peso=3.2,
        talla=49,
        apgar_1_min=0,
        apgar_5_min=0,
    )

@pytest.mark.django_db
def test_creacion_alta(madre_completa, parto_completo, recien_nacido_completo):
    """Verifica que se pueda crear un registro de alta y que se valide correctamente."""
    alta = Alta.objects.create(
        madre=madre_completa,
        parto=parto_completo,
        recien_nacido=recien_nacido_completo,
    )
    assert alta.id is not None
    assert alta.estado == "pendiente"

    alta.validar_registros()
    alta.refresh_from_db()
    assert alta.registros_completos is True
    assert alta.estado == "validada"
    assert alta.observaciones_validacion == "Registros completos"


@pytest.mark.django_db
def test_validacion_incompleta(madre_completa):
    """Comprueba que la validación falle cuando faltan datos críticos."""
    madre_completa.comuna = ""
    madre_completa.save()
    alta = Alta.objects.create(madre=madre_completa)

    resultado = alta.validar_registros()
    alta.refresh_from_db()

    assert resultado is False
    assert alta.estado == "pendiente"
    assert "Madre: Faltan datos" in alta.observaciones_validacion


@pytest.mark.django_db
def test_flujo_completo_alta(madre_completa, parto_completo, recien_nacido_completo):
    """Simula un flujo completo de alta clínica y administrativa."""
    alta = Alta.objects.create(
        madre=madre_completa,
        parto=parto_completo,
        recien_nacido=recien_nacido_completo,
    )
    alta.validar_registros()
    alta.confirmar_alta_clinica("Dr. Validado")
    alta.confirmar_alta_administrativa("Admin Responsable")
    alta.refresh_from_db()
    madre_completa.refresh_from_db()
    parto_completo.refresh_from_db()
    recien_nacido_completo.refresh_from_db()

    assert alta.esta_completada() is True
    assert alta.fecha_alta is not None
    assert madre_completa.estado_alta == "alta_administrativa"
    assert parto_completo.estado_alta == "alta_administrativa"
    assert recien_nacido_completo.estado_alta == "alta_administrativa"