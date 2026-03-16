from enum import Enum


class ExecutionMode(str, Enum):
    SIMULATED = "simulated"
    LIVE = "live"
