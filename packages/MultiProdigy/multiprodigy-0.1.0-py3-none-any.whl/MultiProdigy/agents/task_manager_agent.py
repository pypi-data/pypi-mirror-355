from MultiProdigy.agents.agent_base import BaseAgent
from MultiProdigy.schemas.agent_config import AgentConfig

class TaskManagerAgent(BaseAgent):
    def __init__(self, config: AgentConfig, bus):
        super().__init__(name=config.name, bus=bus)
        self.config = config

    def on_message(self, message):
        raise NotImplementedError
