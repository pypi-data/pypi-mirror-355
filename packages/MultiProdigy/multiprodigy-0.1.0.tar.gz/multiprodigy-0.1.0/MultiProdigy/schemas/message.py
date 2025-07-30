from pydantic import BaseModel, Field

class Message(BaseModel):
    sender: str
    receiver: str
    content: str
    metadata: dict = Field(default_factory=dict)

    def copy_with_new_content(self, new_content: str):
        return Message(
            sender=self.sender,
            receiver=self.receiver,
            content=new_content,
            metadata=self.metadata.copy()
        )