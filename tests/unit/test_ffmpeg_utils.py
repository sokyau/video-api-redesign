# tests/unit/test_ffmpeg_utils.py
import pytest
import os
from unittest.mock import patch, MagicMock
from src.services.ffmpeg_service import run_ffmpeg_command, get_media_info
from src.api.middlewares.error_handler import ProcessingError

@pytest.fixture
def test_video_path():
    return '/tmp/test_video.mp4'

@pytest.fixture
def media_info_sample():
    return {
        'format': 'mp4',
        'duration': 10.5,
        'width': 1280,
        'height': 720,
        'video_codec': 'h264',
        'audio_codec': 'aac'
    }

@patch('subprocess.run')
def test_run_ffmpeg_command_success(mock_subprocess_run, test_video_path):
    mock_process = MagicMock()
    mock_process.stdout = "Dummy output"
    mock_process.stderr = ""
    mock_subprocess_run.return_value = mock_process
    
    result = run_ffmpeg_command(['ffmpeg', '-i', test_video_path, test_video_path])
    
    assert result['success'] is True
    assert mock_subprocess_run.call_count == 1
    
@patch('subprocess.run')
def test_run_ffmpeg_command_error(mock_subprocess_run, test_video_path):
    mock_subprocess_run.side_effect = Exception("Command failed")
    
    with pytest.raises(ProcessingError):
        run_ffmpeg_command(['ffmpeg', '-i', test_video_path, test_video_path])
    
    assert mock_subprocess_run.call_count == 1

@patch('subprocess.run')
@patch('json.loads')
def test_get_media_info(mock_json_loads, mock_subprocess_run, test_video_path, media_info_sample):
    mock_process = MagicMock()
    mock_process.stdout = '{}'
    mock_subprocess_run.return_value = mock_process
    
    mock_json_loads.return_value = {
        "format": {
            "format_name": "mp4",
            "duration": "10.5",
            "size": "1048576",
            "bit_rate": "800000"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1280,
                "height": 720,
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "channels": 2,
                "sample_rate": "44100"
            }
        ]
    }
    
    result = get_media_info(test_video_path)
    
    assert result['format'] == 'mp4'
    assert result['duration'] == 10.5
    assert result['width'] == 1280
    assert result['height'] == 720
    assert result['video_codec'] == 'h264'
    assert result['audio_codec'] == 'aac'
