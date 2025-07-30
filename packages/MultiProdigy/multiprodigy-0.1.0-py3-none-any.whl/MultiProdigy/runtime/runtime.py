from MultiProdigy.bus.message_bus import MessageBus
from MultiProdigy.agents.ollama_agent import OllamaAgent
from MultiProdigy.agents.task_manager_agent import TaskManagerAgent

class Runtime:
    def __init__(self):
        self.bus = MessageBus()
        # Create agents
        self.ollama_agent = OllamaAgent()
        self.task_manager_agent = TaskManagerAgent(runtime=self)
        # Register agents with the bus
        self.bus.register_agent("OllamaAgent", self.ollama_agent)
        self.bus.register_agent("TaskManagerAgent", self.task_manager_agent)
