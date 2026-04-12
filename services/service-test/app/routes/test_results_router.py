"""
Router para consultar resultados de pruebas AWS.
"""
from fastapi import APIRouter
from typing import List
from datetime import datetime

from app.kafka.consumer import results

router = APIRouter(prefix="/test-results", tags=["AWS Test Results"])


@router.get("/aws-messages")
async def get_aws_test_messages():
    """
    Obtiene el historial de mensajes de prueba AWS recibidos.
    """
    # Filtrar solo mensajes de tipo aws_test_response
    aws_messages = [
        r for r in results 
        if r.get("event_type") == "aws_test_response"
    ]
    
    return {
        "total_messages": len(aws_messages),
        "messages": aws_messages[-20:]  # Últimos 20 mensajes
    }


@router.get("/aws-messages/{correlation_id}")
async def get_aws_test_message_by_id(correlation_id: str):
    """
    Busca un mensaje de prueba específico por correlation_id.
    """
    for msg in results:
        if msg.get("correlation_id") == correlation_id:
            return msg
    
    return {"error": "Mensaje no encontrado", "correlation_id": correlation_id}


@router.get("/stats")
async def get_test_stats():
    """
    Estadísticas de mensajes de prueba.
    """
    aws_messages = [r for r in results if r.get("event_type") == "aws_test_response"]
    
    priorities = {}
    for msg in aws_messages:
        prio = msg.get("priority", "unknown")
        priorities[prio] = priorities.get(prio, 0) + 1
    
    return {
        "total_aws_messages": len(aws_messages),
        "total_all_messages": len(results),
        "by_priority": priorities,
        "last_updated": datetime.utcnow().isoformat()
    }


@router.delete("/clear")
async def clear_test_results():
    """
    Limpia el historial de mensajes de prueba.
    """
    global results
    count = len(results)
    results.clear()
    
    return {
        "cleared": True,
        "messages_removed": count
    }
