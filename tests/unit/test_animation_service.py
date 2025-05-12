# tests/unit/test_animation_service.py
import pytest
import os
from unittest.mock import patch, MagicMock
from src.services.animation_service import animated_text_service, build_animation_filter
from src.api.middlewares.error_handler import ProcessingError

@pytest.fixture
def mock_paths():
    return {
        'video_path': '/tmp/test_video.mp4',
        'output_path': '/tmp/output.mp4'
    }

@patch('src.services.animation_service.download_file')
@patch('src.services.animation_service.generate_temp_filename')
@patch('src.services.animation_service.get_media_info')
@patch('src.services.animation_service.run_ffmpeg_command')
@patch('src.services.animation_service.store_file')
def test_animated_text_service_success(
    mock_store_file, mock_run_ffmpeg, mock_get_media_info, mock_gen_temp, mock_download, mock_paths
):
    mock_download.return_value = mock_paths['video_path']
    mock_gen_temp.return_value = mock_paths['output_path']
    mock_get_media_info.return_value = {'duration': 10.0, 'width': 1280, 'height': 720}
    mock_run_ffmpeg.return_value = {'success': True}
    mock_store_file.return_value = 'https://example.com/storage/output.mp4'
    
    with open(mock_paths['video_path'], 'w') as f:
        f.write('test')
    
    result = animated_text_service(
        video_url='https://example.com/video.mp4',
        text='Test Text',
        animation='fade'
    )
    
    assert result == 'https://example.com/storage/output.mp4'
    assert mock_download.call_count == 1
    assert mock_get_media_info.call_count == 1
    assert mock_run_ffmpeg.call_count == 1
    assert mock_store_file.call_count == 1
    
    if os.path.exists(mock_paths['video_path']):
        os.remove(mock_paths['video_path'])

def test_build_animation_filter():
    filter_fade = build_animation_filter(
        text='Test', animation='fade', position='bottom', 
        font='Arial', font_size=36, color='white', 
        duration=3.0, video_width=1280, video_height=720
    )
    assert 'drawtext=text' in filter_fade
    assert 'alpha=' in filter_fade
    
    filter_slide = build_animation_filter(
        text='Test', animation='slide', position='bottom', 
        font='Arial', font_size=36, color='white', 
        duration=3.0, video_width=1280, video_height=720
    )
    assert 'drawtext=text' in filter_slide
    assert 'x=' in filter_slide
