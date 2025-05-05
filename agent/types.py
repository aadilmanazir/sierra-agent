from enum import Enum, auto

class AgentState(Enum):
    """Enum to represent the different states of the agent."""
    WELCOME = auto()  # Initial welcome state
    INTENT_DETECTION = auto()  # Detecting user intent
    INFO_GATHERING = auto()  # Gathering info
    DATA_RETRIEVAL = auto()  # Retrieving data based on gathered info
