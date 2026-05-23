from __future__ import annotations



from datetime import datetime

from pathlib import Path



from .records import *  # noqa: F403

from .shared_utils import (

    json_list as _json_list,

    json_object as _json_object,

    json_objects as _json_objects,

    now as _now,

    parse_json_list as _parse_json_list,

    parse_json_object as _parse_json_object,

    parse_json_objects as _parse_json_objects,

)



from ..sqlite import connect, ensure_operations_db



from .arcs import _ArcMixin
from .braindump import _BraindumpMixin
from .brainstorm import _BrainstormMixin
from .branching import (
    _BranchComparisonMixin,
    _BranchMergeDecisionMixin,
    _BranchPointMixin,
    _BranchStateRefMixin,
    _DecisionNodeMixin,
    _StoryBranchMixin,
)
from .canon import _CanonAnnotationMixin, _CanonProfileMixin
from .characters import _CharacterMixin, _RelationshipMixin
from .continuity import (
    _ContinuityFindingMixin,
    _ContinuityStateMixin,
    _ContinuityThreadMixin,
    _DraftBriefMixin,
    _DraftingContextMixin,
)
from .drafting import (
    _DraftArtifactMixin,
    _ManuscriptDocumentMixin,
    _RevisionSuggestionMixin,
)
from .flow import _FlowMixin
from .foundation import _FoundationMixin
from .generation import _GenerationPacketMixin, _GenerationRunMixin, _GateResultMixin
from .libraries import _MythosMixin, _PatternMixin
from .manuscript_assist import (
    _AssistGateMixin,
    _AssistRunMixin,
    _AssistSuggestionMixin,
)
from .planning import (
    _PlanningBeatPlanMixin,
    _PlanningChapterPacketMixin,
    _PlanningChapterPlanMixin,
    _PlanningDependencyMixin,
    _PlanningScenePlanMixin,
    _PlanningSequencePlanMixin,
)
from .review import _CheckerFindingMixin, _InspectLinkMixin, _ReviewDecisionMixin
from .storyboard import _StoryboardMixin
from .world_bible import _WorldBibleMixin





class StoryDevelopmentRepository(

    _ArcMixin,
    _BraindumpMixin,
    _BrainstormMixin,
    _BranchComparisonMixin,

    _BranchMergeDecisionMixin,
    _BranchPointMixin,
    _BranchStateRefMixin,
    _DecisionNodeMixin,

    _StoryBranchMixin,
    _CanonAnnotationMixin,
    _CanonProfileMixin,
    _CharacterMixin,

    _RelationshipMixin,
    _ContinuityFindingMixin,
    _ContinuityStateMixin,
    _ContinuityThreadMixin,

    _DraftBriefMixin,
    _DraftingContextMixin,
    _DraftArtifactMixin,
    _ManuscriptDocumentMixin,

    _RevisionSuggestionMixin,
    _FlowMixin,
    _FoundationMixin,
    _GenerationPacketMixin,

    _GenerationRunMixin,
    _GateResultMixin,
    _MythosMixin,
    _PatternMixin,

    _AssistGateMixin,
    _AssistRunMixin,
    _AssistSuggestionMixin,
    _PlanningBeatPlanMixin,

    _PlanningChapterPacketMixin,
    _PlanningChapterPlanMixin,
    _PlanningDependencyMixin,
    _PlanningScenePlanMixin,

    _PlanningSequencePlanMixin,
    _CheckerFindingMixin,
    _InspectLinkMixin,
    _ReviewDecisionMixin,

    _StoryboardMixin,
    _WorldBibleMixin,

):

    def __init__(self, db_path: Path) -> None:

        self.db_path = ensure_operations_db(db_path)

        _ArcMixin.__init__(self, db_path)
        _BraindumpMixin.__init__(self, db_path)
        _BrainstormMixin.__init__(self, db_path)
        _BranchComparisonMixin.__init__(self, db_path)
        _BranchMergeDecisionMixin.__init__(self, db_path)
        _BranchPointMixin.__init__(self, db_path)
        _BranchStateRefMixin.__init__(self, db_path)
        _DecisionNodeMixin.__init__(self, db_path)
        _StoryBranchMixin.__init__(self, db_path)
        _CanonAnnotationMixin.__init__(self, db_path)
        _CanonProfileMixin.__init__(self, db_path)
        _CharacterMixin.__init__(self, db_path)
        _RelationshipMixin.__init__(self, db_path)
        _ContinuityFindingMixin.__init__(self, db_path)
        _ContinuityStateMixin.__init__(self, db_path)
        _ContinuityThreadMixin.__init__(self, db_path)
        _DraftBriefMixin.__init__(self, db_path)
        _DraftingContextMixin.__init__(self, db_path)
        _DraftArtifactMixin.__init__(self, db_path)
        _ManuscriptDocumentMixin.__init__(self, db_path)
        _RevisionSuggestionMixin.__init__(self, db_path)
        _FlowMixin.__init__(self, db_path)
        _FoundationMixin.__init__(self, db_path)
        _GenerationPacketMixin.__init__(self, db_path)
        _GenerationRunMixin.__init__(self, db_path)
        _GateResultMixin.__init__(self, db_path)
        _MythosMixin.__init__(self, db_path)
        _PatternMixin.__init__(self, db_path)
        _AssistGateMixin.__init__(self, db_path)
        _AssistRunMixin.__init__(self, db_path)
        _AssistSuggestionMixin.__init__(self, db_path)
        _PlanningBeatPlanMixin.__init__(self, db_path)
        _PlanningChapterPacketMixin.__init__(self, db_path)
        _PlanningChapterPlanMixin.__init__(self, db_path)
        _PlanningDependencyMixin.__init__(self, db_path)
        _PlanningScenePlanMixin.__init__(self, db_path)
        _PlanningSequencePlanMixin.__init__(self, db_path)
        _CheckerFindingMixin.__init__(self, db_path)
        _InspectLinkMixin.__init__(self, db_path)
        _ReviewDecisionMixin.__init__(self, db_path)
        _StoryboardMixin.__init__(self, db_path)
        _WorldBibleMixin.__init__(self, db_path)



    def _normalize_branch_state(self, branch_state: StoryBranchState | str) -> StoryBranchState:
        if isinstance(branch_state, StoryBranchState):
            return branch_state
        normalized = str(branch_state).strip().upper()
        if not normalized:
            raise ValueError("branch_state must not be blank")
        try:
            return StoryBranchState[normalized]
        except KeyError as exc:
            allowed = ", ".join(state.value for state in StoryBranchState)
            raise ValueError(f"branch_state must be one of: {allowed}") from exc

    def _normalize_text(self, value: object, *, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field_name} must not be blank")
        return normalized

    def _normalize_optional_text(self, value: object | None, *, field_name: str) -> str | None:
        if value is None:
            return None
        return self._normalize_text(value, field_name=field_name)

    def _normalize_story_object_type(self, state_object_type: StoryObjectType | str, *, field_name: str) -> StoryObjectType:
        if isinstance(state_object_type, StoryObjectType):
            return state_object_type
        normalized = self._normalize_text(state_object_type, field_name=field_name).upper()
        try:
            return StoryObjectType[normalized]
        except KeyError as exc:
            allowed = ", ".join(item.value for item in StoryObjectType)
            raise ValueError(f"{field_name} must be one of: {allowed}") from exc



from .converters import *  # noqa: F403
