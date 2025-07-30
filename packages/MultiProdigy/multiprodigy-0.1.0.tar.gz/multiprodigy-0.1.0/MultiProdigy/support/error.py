class AgentError(Exception):
    """Base class for all agent-related errors."""
    pass

class MessageValidationError(AgentError):
    """Raised when a message fails schema validation."""
    pass

class AgentNotFoundError(AgentError):
    """Raised when an agent is not registered in the system."""
    pass
