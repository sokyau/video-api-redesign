# tests/integration/test_endpoints.py
import pytest
import json
import os
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
def api_key():
    """Fixture para proporcionar una API key válida"""
    return settings.API_KEY

# Test para endpoints de información
def test_info_endpoints(client):
    """Test para verificar endpoints de información"""
    # Comprobar endpoint principal
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service'] == 'Video Processing API'
    
    # Comprobar health
    response = client.get('/api/v1/system/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    
    # Comprobar versión
    response = client.get('/api/v1/system/version')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'version' in data

# Test para endpoint protegido
def test_protected_endpoint(client, api_key):
    """Test para verificar protección de endpoints"""
    # Sin API key
    response = client.post('/api/v1/video/caption',
                          json={'video_url': 'https://example.com/video.mp4',
                                'subtitles_url': 'https://example.com/subtitles.srt'})
    assert response.status_code == 401
    
    # Con API key
    response = client.post('/api/v1/video/caption',
                          headers={'X-API-Key': api_key},
                          json={'video_url': 'https://example.com/video.mp4',
                                'subtitles_url': 'https://example.com/subtitles.srt'})
    # Nota: Para que este test pase completamente, necesitaríamos mockear los 
    # servicios subyacentes. Aquí solo verificamos que no da 401.
    assert response.status_code != 401

# Test de validación de entrada
def test_input_validation(client, api_key):
    """Test para verificar validación de entrada"""
    response = client.post('/api/v1/video/caption',
                          headers={'X-API-Key': api_key},
                          json={'invalid_field': 'value'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
