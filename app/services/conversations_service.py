from app.schemas.conversations import MessageCreate    

def send_new_message(conversation_id: int, message: MessageCreate):
    # aquí va tu lógica de negocio
    return {"id": conversation_id, "message": 'SI DESDE FASTAPI'}
