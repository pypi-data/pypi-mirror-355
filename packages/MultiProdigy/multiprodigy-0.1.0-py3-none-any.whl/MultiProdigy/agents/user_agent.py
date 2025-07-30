from MultiProdigy.agents.agent_base import BaseAgent
from MultiProdigy.schemas.message import Message

class UserAgent(BaseAgent):
    def on_message(self, message: Message) -> None:
        print(f"[{self.name}] Got reply: {message.content}")

    def send_hello(self, to: str) -> None:
        self.send("Hello, MultiProdigy!", to)