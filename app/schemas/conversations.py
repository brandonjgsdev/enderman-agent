from pydantic import BaseModel

class MessageCreate(BaseModel):
    message: str

class MessageResponse(BaseModel):
    dateTime: str
    httpCode: int
    alert: str
    title: str
    message: str
    data: dict
