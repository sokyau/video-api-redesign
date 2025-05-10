# tests/integration/test_video_endpoints.py
import pytest
import json
from unittest.mock import patch
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

@patch('src.services.video_service.concatenate_videos_service')
def test_concatenate_videos(mock_concatenate, client, api_key):
    """Test para el endpoint de concatenación de videos"""
    # Simular retorno del servicio
    mock_concatenate.return_value = 'https://example.com/storage/output.mp4'
    
    # Datos de prueba
    test_data = {
        "video_urls": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ]
    }
    
    # Probar endpoint
    response = client.post(
        '/api/v1/video/concatenate',
        headers={'X-API-Key': api_key},
        json=test_data
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['result'] == 'https://example.com/storage/output.mp4'
    mock_concatenate.assert_called_once()

@patch('src.services.animation_service.animated_text_service')
def test_animated_text(mock_animated_text, client, api_key):
    """Test para el endpoint de texto animado"""
    # Simular retorno del servicio
    mock_animated_text.return_value = 'https://example.com/storage/output.mp4'
    
    # Datos de prueba
    test_data = {
        "video_url": "https://example.com/video.mp4",
        "text": "Test Animation",
        "animation": "fade"
    }
    
    # Probar endpoint
    response = client.post(
        '/api/v1/video/animated-text',
        headers={'X-API-Key': api_key},
        json=test_data
    )
    
    # Verificar respuesta
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert data['result'] == 'https://example.com/storage/output.mp4'
    mock_animated_text.assert_called_once()

