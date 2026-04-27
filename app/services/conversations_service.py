from datetime import datetime
from app.schemas.conversations import MessageCreate
from app.services.agent_service import agent_instance

async def send_new_message(conversation_id: int, message: MessageCreate):

    answer = await agent_instance.chat(
        message.message, session_id=f"conv-{conversation_id}"
    )
    # aquí va tu lógica de negocio
    return {
        "dateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "httpCode": 200,
        "alert": "success",
        "title": "",
        "message": "",
        "data": {
            "id": conversation_id,
            "message": answer
        }
    }
