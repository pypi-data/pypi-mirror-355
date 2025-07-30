from MultiProdigy.schemas.message import Message
from MultiProdigy.agents.agent_base import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self, name: str, runtime):
        super().__init__(name, runtime)
        self.memory = []

    def handle_message(self, message: Message) -> Message:
        print(f"[MemoryAgent] Received: {message.content}")
        self.memory.append(message.content)
        return message.copy_with_new_content("Memory stored.")
