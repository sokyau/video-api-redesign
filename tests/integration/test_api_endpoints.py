# tests/integration/test_api_endpoints.py
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
def valid_api_key():
    return settings.API_KEY

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_index_endpoint(client):
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['service'] == 'Video Processing API'
    assert 'status' in data
    assert 'version' in data

def test_auth_required(client):
    response = client.post('/api/v1/video/caption', 
                          json={'video_url': 'http://example.com/video.mp4',
                                'subtitles_url': 'http://example.com/subs.srt'})
    assert response.status_code == 401

def test_auth_valid(client, valid_api_key):
    response = client.post('/api/v1/video/caption', 
                          headers={'X-API-Key': valid_api_key},
                          json={'video_url': 'http://example.com/video.mp4',
                                'subtitles_url': 'http://example.com/subs.srt'})
    assert response.status_code != 401

def test_validation_error(client, valid_api_key):
    response = client.post('/api/v1/video/caption', 
                          headers={'X-API-Key': valid_api_key},
                          json={'invalid_field': 'value'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'validation_error' in data['error']
