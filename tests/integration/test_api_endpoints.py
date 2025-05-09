import pytest
import os
import json
from src.app import create_app
from src.config import settings

@pytest.fixture
def client():
    """Fixture para crear un cliente de prueba Flask"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def valid_api_key():
    """Fixture para proporcionar una API key válida para pruebas"""
    return settings.API_KEY

def test_health_endpoint(client):
    """Test para verificar que el endpoint /health responde correctamente"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_index_endpoint(client):
    """Test para verificar que el endpoint / responde correctamente"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service'] == 'Video Processing API'
    assert 'status' in data
    assert 'version' in data

def test_auth_required(client):
    """Test para verificar que los endpoints protegidos requieren API key"""
    # Suponiendo que ya hayamos registrado las rutas
    # Nota: Este test podría fallar si las rutas no están registradas
    response = client.post('/api/v1/video/caption', 
                          json={'video_url': 'http://example.com/video.mp4',
                                'subtitles_url': 'http://example.com/subs.srt'})
    assert response.status_code == 401  # Sin API key debería dar Unauthorized

def test_auth_valid(client, valid_api_key):
    """Test para verificar que los endpoints aceptan una API key válida"""
    # Este test podría necesitar mocks adicionales para que funcione completamente
    response = client.post('/api/v1/video/caption', 
                          headers={'X-API-Key': valid_api_key},
                          json={'video_url': 'http://example.com/video.mp4',
                                'subtitles_url': 'http://example.com/subs.srt'})
    
    # Verificar que no es un error de autenticación (podría ser otro error por falta de mocks)
    assert response.status_code != 401

def test_validation_error(client, valid_api_key):
    """Test para verificar que la validación de JSON funciona"""
    response = client.post('/api/v1/video/caption', 
                          headers={'X-API-Key': valid_api_key},
                          json={'invalid_field': 'value'})  # Falta video_url y subtitles_url
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'validation_error' in data['error']
