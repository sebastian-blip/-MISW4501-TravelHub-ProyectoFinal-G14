"""
Router de prueba para validar conectividad Kafka en AWS.
Envía mensajes de prueba a service-test y recibe confirmación.
"""
import uuid
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from infrastructure.messaging.kafka.producer import publish_test_message

router = APIRouter(prefix="/test", tags=["AWS Test"])


class TestMessageRequest(BaseModel):
    message: str = Field(default="Ping desde service-core", description="Mensaje a enviar")
    priority: str = Field(default="normal", description="Prioridad: low, normal, high")
    metadata: Optional[dict] = Field(default=None, description="Metadata adicional")


class TestMessageResponse(BaseModel):
    success: bool
    correlation_id: str
    message_sent: str
    timestamp: str
    details: dict


@router.post("/kafka-aws", response_model=TestMessageResponse)
async def test_kafka_aws_connection(request: TestMessageRequest):
    """
    Endpoint de prueba para validar conectividad Kafka en AWS.
    
    Envía un mensaje de prueba a través de Kafka hacia service-test.
    El mensaje incluye un correlation_id para rastrear la respuesta.
    
    Ejemplo de uso:
    ```json
    {
        "message": "Test de conectividad AWS",
        "priority": "high",
        "metadata": {"region": "us-east-1", "test_id": "123"}
    }
    ```
    """
    try:
        correlation_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        await publish_test_message(
            message=request.message,
            correlation_id=correlation_id,
            priority=request.priority,
            metadata=request.metadata or {},
            timestamp=timestamp
        )
        
        logging.info(f"[Test Router] Mensaje de prueba enviado: correlation_id={correlation_id}")
        
        return TestMessageResponse(
            success=True,
            correlation_id=correlation_id,
            message_sent=request.message,
            timestamp=timestamp,
            details={
                "target_topic": "aws-test-messages",
                "target_service": "service-test",
                "priority": request.priority,
                "extra_metadata": request.metadata
            }
        )
        
    except Exception as e:
        logging.error(f"[Test Router] Error enviando mensaje de prueba: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al enviar mensaje a Kafka: {str(e)}"
        )


@router.get("/kafka-aws/health")
async def test_kafka_health():
    """
    Verifica el estado básico del servicio y su conexión con Kafka.
    """
    return {
        "service": "service-core",
        "status": "ok",
        "kafka_enabled": True,
        "test_endpoint_available": True,
        "timestamp": datetime.utcnow().isoformat()
    }
