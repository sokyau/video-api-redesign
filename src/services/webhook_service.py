# src/services/webhook_service.py
import json
import logging
import requests
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def send_webhook(url: str, data: Dict[str, Any], max_retries: int = 3) -> bool:
    """
    Envía notificación de webhook
    
    Args:
        url: URL del webhook
        data: Datos a enviar
        max_retries: Máximo número de reintentos
    
    Returns:
        bool: True si fue exitoso, False en caso contrario
    """
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'VideoAPI-Webhook/1.0'
    }
    
    retry_count = 0
    while retry_count < max_retries:
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(data),
                timeout=10  # 10 segundos de timeout
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Webhook enviado exitosamente a {url}")
                return True
            else:
                logger.warning(f"Webhook falló con estado {response.status_code}: {response.text}")
                retry_count += 1
                
                if retry_count < max_retries:
                    # Retroceso exponencial
                    wait_time = 2 ** retry_count
                    time.sleep(wait_time)
                
        except requests.RequestException as e:
            logger.error(f"Error enviando webhook a {url}: {str(e)}")
            retry_count += 1
            
            if retry_count < max_retries:
                wait_time = 2 ** retry_count
                time.sleep(wait_time)
    
    logger.error(f"Webhook a {url} falló después de {max_retries} intentos")
    return False

def create_job_notification(job_id: str, status: str, result: Optional[str] = None, error: Optional[str] = None) -> Dict[str, Any]:
    """
    Crea datos de notificación de trabajo
    
    Args:
        job_id: ID de trabajo
        status: Estado del trabajo
        result: URL de resultado opcional
        error: Mensaje de error opcional
    
    Returns:
        dict: Datos de notificación
    """
    notification = {
        "job_id": job_id,
        "status": status,
        "timestamp": time.time()
    }
    
    if result:
        notification["result"] = result
    
    if error:
        notification["error"] = error
    
    return notification

def notify_job_completed(job_id: str, webhook_url: str, result: str) -> bool:
    """Notifica que un trabajo ha sido completado"""
    if not webhook_url:
        return False
    
    notification = create_job_notification(
        job_id=job_id,
        status="completed",
        result=result
    )
    
    return send_webhook(webhook_url, notification)

def notify_job_failed(job_id: str, webhook_url: str, error: str) -> bool:
    """Notifica que un trabajo ha fallado"""
    if not webhook_url:
        return False
    
    notification = create_job_notification(
        job_id=job_id,
        status="failed",
        error=error
    )
    
    return send_webhook(webhook_url, notification)
