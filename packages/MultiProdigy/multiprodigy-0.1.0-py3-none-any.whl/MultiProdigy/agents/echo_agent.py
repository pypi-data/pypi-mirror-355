from MultiProdigy.agents.agent_base import BaseAgent
from MultiProdigy.schemas.message import Message

class EchoAgent(BaseAgent):
    def on_message(self, message: Message) -> None:
        print(f"[{self.name}] Received: {message.content}")
        # reply back:
        reply = message.copy_with_new_content(f"Echo: {message.content}")
        reply.sender = self.name
        reply.receiver = message.sender
        self.bus.publish(reply)
