"""Tests for scene context injection robustness."""
import pytest
from app.schemas.inference import InferenceMessage, InferenceRequest


class TestSceneContextInjectionRobustness:
    """Verify scene context injection uses role-based lookup, not index-based."""

    def test_find_user_message_by_role(self) -> None:
        from app.services.local_executor import find_user_message_index

        messages = [
            InferenceMessage(role="system", content="System prompt"),
            InferenceMessage(role="user", content="User prompt"),
        ]
        idx = find_user_message_index(messages)
        assert idx == 1

    def test_find_user_message_with_extra_messages(self) -> None:
        from app.services.local_executor import find_user_message_index

        messages = [
            InferenceMessage(role="system", content="System prompt"),
            InferenceMessage(role="assistant", content="Assistant reply"),
            InferenceMessage(role="user", content="User prompt"),
        ]
        idx = find_user_message_index(messages)
        assert idx == 2

    def test_find_user_message_returns_none_when_missing(self) -> None:
        from app.services.local_executor import find_user_message_index

        messages = [
            InferenceMessage(role="system", content="System prompt"),
        ]
        idx = find_user_message_index(messages)
        assert idx is None

    def test_inject_context_uses_role_based_lookup(self) -> None:
        from app.services.local_executor import inject_scene_context

        request = InferenceRequest(
            model="test",
            messages=[
                InferenceMessage(role="system", content="System"),
                InferenceMessage(role="user", content="Original user content"),
            ],
        )
        new_request = inject_scene_context(request, "Injected context")

        user_msg = [m for m in new_request.messages if m.role == "user"][0]
        assert "Original user content" in user_msg.content
        assert "Injected context" in user_msg.content

    def test_inject_context_skips_when_no_user_message(self) -> None:
        from app.services.local_executor import inject_scene_context

        request = InferenceRequest(
            model="test",
            messages=[
                InferenceMessage(role="system", content="System"),
            ],
        )
        new_request = inject_scene_context(request, "Injected context")
        # Should return original request unchanged when no user message
        assert len(new_request.messages) == 1
