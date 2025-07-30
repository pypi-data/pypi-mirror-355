
from abc import ABC, abstractmethod
from MultiProdigy.bus.bus import MessageBus
from MultiProdigy.schemas.message import Message

class BaseAgent(ABC):
    def __init__(self, name: str, bus: MessageBus):
        self.name = name
        self.bus = bus

    def send(self, content: str, to: str) -> None:
        """Helper to publish a Message to another agent."""
        msg = Message(sender=self.name, receiver=to, content=content)
        self.bus.publish(msg)

    @abstractmethod
    def on_message(self, message: Message) -> None:
        """Called by the bus when a message arrives."""
        ...