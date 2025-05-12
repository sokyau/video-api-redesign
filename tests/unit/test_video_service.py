# tests/unit/test_video_service.py
import pytest
import os
from unittest.mock import patch, MagicMock
from src.services.video_service import add_captions_to_video, process_meme_overlay
from src.api.middlewares.error_handler import ProcessingError

@pytest.fixture
def mock_paths():
    return {
        'video_path': '/tmp/test_video.mp4',
        'subtitles_path': '/tmp/test_subtitles.srt',
        'meme_path': '/tmp/test_meme.png',
        'output_path': '/tmp/output.mp4'
    }

@patch('src.services.video_service.download_file')
@patch('src.services.video_service.generate_temp_filename')
@patch('src.services.video_service.run_ffmpeg_command')
@patch('src.services.video_service.store_file')
def test_add_captions_to_video_success(
    mock_store_file, mock_run_ffmpeg, mock_gen_temp, mock_download, mock_paths
):
    mock_download.side_effect = [mock_paths['video_path'], mock_paths['subtitles_path']]
    mock_gen_temp.return_value = mock_paths['output_path']
    mock_run_ffmpeg.return_value = {'success': True}
    mock_store_file.return_value = 'https://example.com/storage/output.mp4'
    
    for path in [mock_paths['video_path'], mock_paths['subtitles_path']]:
        with open(path, 'w') as f:
            f.write('test')
    
    result = add_captions_to_video(
        video_url='https://example.com/video.mp4',
        subtitles_url='https://example.com/subtitles.srt'
    )
    
    assert result == 'https://example.com/storage/output.mp4'
    assert mock_download.call_count == 2
    assert mock_run_ffmpeg.call_count == 1
    assert mock_store_file.call_count == 1
    
    for path in [mock_paths['video_path'], mock_paths['subtitles_path']]:
        if os.path.exists(path):
            os.remove(path)

@patch('src.services.video_service.download_file')
def test_add_captions_to_video_download_error(mock_download):
    mock_download.side_effect = ProcessingError("Error de descarga")
    
    with pytest.raises(ProcessingError) as excinfo:
        add_captions_to_video(
            video_url='https://example.com/video.mp4',
            subtitles_url='https://example.com/subtitles.srt'
        )
    
    assert "Error de descarga" in str(excinfo.value)
