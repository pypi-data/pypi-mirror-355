from pydantic import BaseModel

class AgentConfig(BaseModel):
    name: str
    description: str = None

class Message(BaseModel):
    sender: str
    receiver: str
    content: str

class BusPayload(BaseModel):
    message: Message

 