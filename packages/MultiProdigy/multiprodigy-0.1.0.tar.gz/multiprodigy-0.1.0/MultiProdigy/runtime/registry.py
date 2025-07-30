# prodigal_agent/runtime/registry.py

class AgentRegistry:
    agents = {}

    @staticmethod
    def register(agent):
        print(f"[registry] registering agent {agent.name}")
        AgentRegistry.agents[agent.name] = agent

    @staticmethod
    def get(name):
        return AgentRegistry.agents.get(name)
