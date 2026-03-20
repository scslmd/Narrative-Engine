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