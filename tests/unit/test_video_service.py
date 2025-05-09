import pytest
import os
import shutil
from unittest.mock import patch, MagicMock
from src.services.video_service import add_captions_to_video, process_meme_overlay
from src.api.middlewares.error_handler import ProcessingError

# Configuración del entorno de pruebas
@pytest.fixture
def setup_temp_dir():
    """Fixture para crear y limpiar directorios temporales para pruebas"""
    # Crear directorio temporal para pruebas
    temp_dir = os.path.join('tests', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    # Devolver directorio
    yield temp_dir
    
    # Limpiar después de la prueba
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

@pytest.fixture
def mock_file_paths(setup_temp_dir):
    """Fixture que proporciona rutas a archivos mockeados"""
    video_path = os.path.join(setup_temp_dir, 'test_video.mp4')
    subtitles_path = os.path.join(setup_temp_dir, 'test_subs.srt')
    meme_path = os.path.join(setup_temp_dir, 'test_meme.png')
    output_path = os.path.join(setup_temp_dir, 'output.mp4')
    
    # Crear archivos vacíos para simular existencia
    for path in [video_path, subtitles_path, meme_path]:
        with open(path, 'w') as f:
            f.write('dummy content')
    
    return {
        'video_path': video_path,
        'subtitles_path': subtitles_path,
        'meme_path': meme_path,
        'output_path': output_path,
        'temp_dir': setup_temp_dir
    }

# Tests para add_captions_to_video
@patch('src.services.video_service.download_file')
@patch('src.services.video_service.generate_temp_filename')
@patch('src.services.video_service.run_ffmpeg_command')
@patch('src.services.video_service.store_file')
def test_add_captions_to_video_success(
    mock_store_file, mock_run_ffmpeg, mock_generate_temp_filename, 
    mock_download_file, mock_file_paths
):
    """Test para verificar que add_captions_to_video funciona correctamente"""
    # Configurar mocks
    mock_download_file.side_effect = [
        mock_file_paths['video_path'], 
        mock_file_paths['subtitles_path']
    ]
    mock_generate_temp_filename.return_value = mock_file_paths['output_path']
    mock_run_ffmpeg.return_value = {'success': True}
    mock_store_file.return_value = 'https://example.com/storage/output.mp4'
    
    # Ejecutar función
    result = add_captions_to_video(
        video_url='https://example.com/video.mp4',
        subtitles_url='https://example.com/subtitles.srt',
        font='Arial',
        font_size=24,
        font_color='white',
        background=True,
        position='bottom',
        job_id='test_job_id'
    )
    
    # Verificar resultados
    assert result == 'https://example.com/storage/output.mp4'
    assert mock_download_file.call_count == 2
    assert mock_run_ffmpeg.call_count == 1
    assert mock_store_file.call_count == 1
    
    # Verificar llamada a FFmpeg
    ffmpeg_call_args = mock_run_ffmpeg.call_args[0][0]
    assert 'ffmpeg' in ffmpeg_call_args
    assert mock_file_paths['video_path'] in ffmpeg_call_args
    assert 'subtitles=' in ffmpeg_call_args[ffmpeg_call_args.index('-vf') + 1]

@patch('src.services.video_service.download_file')
def test_add_captions_to_video_invalid_subtitle_format(mock_download_file, mock_file_paths):
    """Test para verificar que se maneja correctamente un formato de subtítulos no válido"""
    # Configurar mock para devolver un archivo con extensión no soportada
    invalid_subs_path = os.path.join(mock_file_paths['temp_dir'], 'test_subs.xyz')
    with open(invalid_subs_path, 'w') as f:
        f.write('dummy content')
    
    mock_download_file.side_effect = [
        mock_file_paths['video_path'], 
        invalid_subs_path
    ]
    
    # Verificar que levanta error
    with pytest.raises(ValueError) as excinfo:
        add_captions_to_video(
            video_url='https://example.com/video.mp4',
            subtitles_url='https://example.com/subtitles.xyz',
            job_id='test_job_id'
        )
    
    # Verificar mensaje de error
    assert "Formato de subtítulos no soportado" in str(excinfo.value)

# Tests para process_meme_overlay
@patch('src.services.video_service.download_file')
@patch('src.services.video_service.generate_temp_filename')
@patch('src.services.video_service.run_ffmpeg_command')
@patch('src.services.video_service.store_file')
def test_process_meme_overlay_success(
    mock_store_file, mock_run_ffmpeg, mock_generate_temp_filename, 
    mock_download_file, mock_file_paths
):
    """Test para verificar que process_meme_overlay funciona correctamente"""
    # Configurar mocks
    mock_download_file.side_effect = [
        mock_file_paths['video_path'], 
        mock_file_paths['meme_path']
    ]
    mock_generate_temp_filename.return_value = mock_file_paths['output_path']
    mock_run_ffmpeg.return_value = {'success': True}
    mock_store_file.return_value = 'https://example.com/storage/output.mp4'
    
    # Ejecutar función
    result = process_meme_overlay(
        video_url='https://example.com/video.mp4',
        meme_url='https://example.com/meme.png',
        position='bottom',
        scale=0.3,
        job_id='test_job_id'
    )
    
    # Verificar resultados
    assert result == 'https://example.com/storage/output.mp4'
    assert mock_download_file.call_count == 2
    assert mock_run_ffmpeg.call_count == 1
    assert mock_store_file.call_count == 1
    
    # Verificar llamada a FFmpeg
    ffmpeg_call_args = mock_run_ffmpeg.call_args[0][0]
    assert 'ffmpeg' in ffmpeg_call_args
    assert mock_file_paths['video_path'] in ffmpeg_call_args
    assert mock_file_paths['meme_path'] in ffmpeg_call_args
    assert '-filter_complex' in ffmpeg_call_args

def test_process_meme_overlay_invalid_position():
    """Test para verificar que se maneja correctamente una posición no válida"""
    with pytest.raises(ValueError) as excinfo:
        process_meme_overlay(
            video_url='https://example.com/video.mp4',
            meme_url='https://example.com/meme.png',
            position='invalid_position',
            job_id='test_job_id'
        )
    
    assert "Posición no válida" in str(excinfo.value)

def test_process_meme_overlay_invalid_scale():
    """Test para verificar que se maneja correctamente una escala no válida"""
    with pytest.raises(ValueError) as excinfo:
        process_meme_overlay(
            video_url='https://example.com/video.mp4',
            meme_url='https://example.com/meme.png',
            scale=2.5,  # Fuera del rango válido
            job_id='test_job_id'
        )
    
    assert "Escala no válida" in str(excinfo.value)
