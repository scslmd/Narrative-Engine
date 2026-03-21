from __future__ import annotations

from enum import Enum


class PovMode(str, Enum):
    FIRST = "First"
    THIRD_LIMITED = "Third_Limited"
    THIRD_OMNI = "Third_Omni"


class StoryStructure(str, Enum):
    SAVE_THE_CAT = "SAVE_THE_CAT"
    THREE_ACT = "THREE_ACT"


class JobPhase(str, Enum):
    P_100 = "P-100"
    P_200 = "P-200"
    P_300 = "P-300"
    P_400 = "P-400"


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StoryFlowStageConfigurationState(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    OPTIONAL = "OPTIONAL"
    ARCHIVED = "ARCHIVED"


class StoryFlowStageProgressState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    COMPLETE = "COMPLETE"
    SUPERSEDED = "SUPERSEDED"


class StoryArtifactLifecycleState(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    CANONICAL = "CANONICAL"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class StorySuggestionLifecycleState(str, Enum):
    REQUESTED = "REQUESTED"
    READY = "READY"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REFINE_REQUESTED = "REFINE_REQUESTED"
    EXPIRED = "EXPIRED"
