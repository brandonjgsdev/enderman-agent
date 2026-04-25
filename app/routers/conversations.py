from fastapi import APIRouter, HTTPException
from app.schemas.conversations import MessageCreate, MessageResponse
from app.services import conversations_service

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_new_message(conversation_id: int, message: MessageCreate):
    # FastAPI valida automáticamente el request con ItemCreate
    result = conversations_service.send_new_message(conversation_id, message)
    return result