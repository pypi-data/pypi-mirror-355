from collections import deque
from MultiProdigy.schemas.message import Message

class MessageBus:
    """Manages agent registration and in-memory message delivery."""
    def __init__(self):
        self.queue = deque()
        self.agents: dict[str, "BaseAgent"] = {}

    def register(self, agent: "BaseAgent") -> None:
        """Register an agent by its .name so it can receive messages."""
        self.agents[agent.name] = agent
        print(f"[bus] registered agent {agent.name}")

    def publish(self, message: Message) -> None:
        """Enqueue a Message for delivery."""
        print(f"[bus] publishing ▶ {message.sender} → {message.receiver}: {message.content}")
        self.queue.append(message)
        self._dispatch()

    def _dispatch(self) -> None:
        """Deliver all queued messages to their recipients."""
        while self.queue:
            msg = self.queue.popleft()
            print(f"[bus] dequeued ▶ {msg.sender} → {msg.receiver}: {msg.content}")

            recipient = self.agents.get(msg.receiver)
            if not recipient:
                print(f"[bus] no agent named {msg.receiver}")
                continue

            print(f"[bus] delivering to {msg.receiver}")
            recipient.on_message(msg)
