class MessageBus:
    def __init__(self):
        self.agents = {}

    def register(self, agent):
        """Register an agent so it can receive messages."""
        self.agents[agent.name] = agent

    def send(self, message):
        """Deliver a message to the correct agent."""
        receiver = message.receiver
        if receiver in self.agents:
            self.agents[receiver].handle_message(message)
        else:
            print(f"[Bus] No agent found with name: {receiver}")

class MessageBus:
    def __init__(self):
        self.agents = []

    def register_agent(self, agent):
        self.agents.append(agent)
        print(f"Agent registered: {agent}")
