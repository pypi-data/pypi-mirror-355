from datetime import datetime
from enum import StrEnum, auto
from uuid import UUID

from pydantic import BaseModel, JsonValue


class FinalEnvironmentRequest(BaseModel):
    status: str


class StoreAgentStatePostRequest(BaseModel):
    agent_id: str
    step: str
    state: JsonValue
    trajectory_timestep: int


class StoreEnvironmentFrameRequest(BaseModel):
    agent_state_point_in_time: str
    current_agent_step: str
    state: JsonValue
    trajectory_timestep: int


class ExecutionStatus(StrEnum):
    QUEUED = auto()
    IN_PROGRESS = "in progress"
    FAIL = auto()
    SUCCESS = auto()
    CANCELLED = auto()

    def is_terminal_state(self) -> bool:
        return self in self.terminal_states()

    @classmethod
    def terminal_states(cls) -> set["ExecutionStatus"]:
        return {cls.SUCCESS, cls.FAIL, cls.CANCELLED}


class WorldModel(BaseModel):
    """
    Payload for creating a new world model snapshot.

    This model is sent to the API.
    """

    content: str
    prior: UUID | str | None = None
    name: str | None = None
    description: str | None = None
    trajectory_id: UUID | str | None = None
    model_metadata: JsonValue | None = None


class WorldModelResponse(BaseModel):
    """
    Response model for a world model snapshot.

    This model is received from the API.
    """

    id: UUID | str
    prior: UUID | str | None
    name: str
    description: str | None
    content: str
    trajectory_id: UUID | str | None
    email: str | None
    model_metadata: JsonValue | None
    enabled: bool
    created_at: datetime
