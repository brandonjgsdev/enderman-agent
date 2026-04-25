from datetime import datetime
from app.schemas.conversations import MessageCreate

def send_new_message(conversation_id: int, message: MessageCreate):
    # aquí va tu lógica de negocio
    return {
        "dateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "httpCode": 200,
        "alert": "success",
        "title": "",
        "message": "",
        "data": {
            "id": conversation_id,
            "message": 'Hola, soy el asistente de Enderman. ¿En qué puedo ayudarte?'
        }
    }
