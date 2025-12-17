# hospital/tests/test_respaldos.py
import pytest
from django.urls import reverse
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from usuarios.models import Usuario
from respaldos.views import generar_respaldo

@pytest.fixture
def encargado_ti(db):
    """Crea un usuario encargado de TI."""
    return Usuario.objects.create_user(
        username="ti_user",
        password="password123",
        rut="33333333-3",
        # CORRECCIÓN 1: El rol correcto según models.py es 'encargado_ti'
        rol="encargado_ti" 
    )

@pytest.fixture
def medico_hackerman(db):
    """Un médico que intenta descargar la base de datos."""
    return Usuario.objects.create_user(
        username="medico_hacker",
        password="password123",
        rut="44444444-4",
        rol="medico"
    )

@pytest.mark.django_db
class TestRespaldos:

    def test_acceso_denegado_no_ti(self, client, medico_hackerman):
        """Un médico NO debe poder descargar el respaldo."""
        client.force_login(medico_hackerman)
        url = reverse('respaldos:generar_respaldo')
        response = client.get(url)
        
        # Debe ser redirigido (302)
        assert response.status_code == 302
        
        # CORRECCIÓN 2: El decorador redirige al login, no al home
        assert response.url == reverse('usuarios:login')

    def test_acceso_permitido_ti(self, encargado_ti, monkeypatch):
        """
        El encargado de TI SÍ debe poder descargar el respaldo.
        Usamos RequestFactory para evitar conflictos con la sesión en el Mock.
        """
        
        # 1. Configurar el Mock de la Base de Datos
        from django.db import connection
        class MockCursor:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def execute(self, sql, params=None): pass
            def fetchall(self): 
                # Simulamos que hay 2 tablas en la BD
                return [('tabla_1',), ('tabla_2',)] 
            def fetchone(self): 
                # Simulamos el CREATE TABLE
                return [None, "CREATE TABLE `mock` (...)"]
            def close(self): pass
        
        def mock_cursor():
            return MockCursor()
            
        # Aplicamos el parche
        monkeypatch.setattr(connection, 'cursor', mock_cursor)

        # 2. Crear una solicitud manual (RequestFactory)
        factory = RequestFactory()
        request = factory.get(reverse('respaldos:generar_respaldo'))
        
        # 3. Asignar el usuario y mensajes manualmente al request
        request.user = encargado_ti
        # Necesario para que messages.success funcione sin middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        # 4. Llamar a la vista directamente
        response = generar_respaldo(request)
        
        # 5. Verificaciones
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/sql'
        assert 'attachment; filename="respaldo_' in response.headers['Content-Disposition']
        
        # Verificamos que el contenido del dump tenga lo que simulamos
        content = response.content.decode('utf-8')
        assert "DROP TABLE IF EXISTS `tabla_1`" in content
        assert "DROP TABLE IF EXISTS `tabla_2`" in content