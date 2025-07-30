from pydantic import BaseModel
from pydantic_settings import BaseSettings 


class AgentConfig(BaseModel):
    name: str
    role: str = "default"
    goal: str = "default goal"

class Settings(BaseSettings):
    agent_name: str = "TestAgent"
    agent_role: str = "default"
    agent_goal: str = "default goal"

    class Config:
        env_file = ".env"  # Optional, if using environment files
