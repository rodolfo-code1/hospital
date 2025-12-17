# hospital/tests/test_reportes.py
import pytest
from django.urls import reverse
from django.utils import timezone
from usuarios.models import Usuario
from partos.models import Parto
from pacientes.models import Madre

@pytest.fixture
def usuario_supervisor(db):
    """Crea un usuario con rol Supervisor."""
    return Usuario.objects.create_user(
        username="supervisor1",
        password="password123",
        rut="11111111-1",
        rol="supervisor"
    )

@pytest.fixture
def usuario_normal(db):
    """Crea un usuario sin permisos de supervisor (ej. administrativo)."""
    return Usuario.objects.create_user(
        username="admin1",
        password="password123",
        rut="22222222-2",
        rol="administrativo"
    )

@pytest.fixture
def datos_reporte(db):
    """Crea datos ficticios para probar el reporte."""
    # SOLUCIÓN INTEGRITY ERROR: Se agrega 'edad' que es obligatorio
    madre = Madre.objects.create(rut="12345678-9", nombre="Madre Test", edad=30)
    
    # Crear 3 partos: 2 cesáreas y 1 normal
    Parto.objects.create(
        madre=madre, tipo="cesarea", 
        fecha_hora_inicio=timezone.now(), fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. X", matrona_responsable="Mat. Y"
    )
    Parto.objects.create(
        madre=madre, tipo="cesarea", 
        fecha_hora_inicio=timezone.now(), fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. X", matrona_responsable="Mat. Y"
    )
    Parto.objects.create(
        madre=madre, tipo="normal", 
        fecha_hora_inicio=timezone.now(), fecha_hora_termino=timezone.now(),
        medico_responsable="Dr. X", matrona_responsable="Mat. Y"
    )

@pytest.mark.django_db
class TestReportes:
    
    def test_acceso_denegado_no_supervisor(self, client, usuario_normal):
        """Un administrativo NO debería poder ver el reporte."""
        client.force_login(usuario_normal)
        # SOLUCIÓN URL: namespace 'reportes' en lugar de 'app'
        url = reverse('reportes:seccion_a')  
        response = client.get(url)
        # Esperamos redirección (302) o acceso prohibido (403)
        assert response.status_code in [302, 403] 

    def test_acceso_permitido_supervisor(self, client, usuario_supervisor):
        """Un supervisor SÍ debería ver el reporte."""
        client.force_login(usuario_supervisor)
        # SOLUCIÓN URL: namespace 'reportes' en lugar de 'app'
        url = reverse('reportes:seccion_a')
        response = client.get(url)
        assert response.status_code == 200

    def test_calculo_datos_seccion_a(self, client, usuario_supervisor, datos_reporte):
        """Verifica que el reporte cuente correctamente los partos."""
        client.force_login(usuario_supervisor)
        url = reverse('reportes:seccion_a')
        response = client.get(url)
        
        assert response.status_code == 200
        # Verificar que en el contexto vienen los 3 partos creados
        assert response.context['total_partos'] == 3
        
        # Verificar conteo por tipo
        tipos = response.context['partos_por_tipo']
        
        # Buscamos en la lista de dicts (puede variar según tu implementación de view)
        cesareas = next((item for item in tipos if item['tipo'] == 'cesarea'), None)
        normales = next((item for item in tipos if item['tipo'] == 'normal'), None)
        
        if cesareas:
            assert cesareas['count'] == 2
        if normales:
            assert normales['count'] == 1