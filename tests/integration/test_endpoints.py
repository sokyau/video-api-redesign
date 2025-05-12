# tests/integration/test_endpoints.py
import pytest
import json
from src.app import create_app
from src.config import settings

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def api_key():
    return settings.API_KEY

def test_info_endpoints(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service'] == 'Video Processing API'
    
    response = client.get('/api/v1/system/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    
    response = client.get('/api/v1/system/version')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'version' in data

def test_protected_endpoint(client, api_key):
    response = client.post('/api/v1/video/caption',
                          json={'video_url': 'https://example.com/video.mp4',
                                'subtitles_url': 'https://example.com/subtitles.srt'})
    assert response.status_code == 401
    
    response = client.post('/api/v1/video/caption',
                          headers={'X-API-Key': api_key},
                          json={'video_url': 'https://example.com/video.mp4',
                                'subtitles_url': 'https://example.com/subtitles.srt'})
    assert response.status_code != 401

def test_input_validation(client, api_key):
    response = client.post('/api/v1/video/caption',
                          headers={'X-API-Key': api_key},
                          json={'invalid_field': 'value'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
