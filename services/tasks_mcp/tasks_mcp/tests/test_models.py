import pytest
from pydantic import ValidationError

from tasks_mcp.models.work_item import (
    ItemType,
    WorkItemCreateInput,
    WorkItemUpdateInput,
)


class TestWorkItemCreateInput:
    def test_valid_task(self):
        data = WorkItemCreateInput(title="Call mom", type="task")
        assert data.title == "Call mom"
        assert data.type == ItemType.TASK

    def test_valid_appointment(self):
        data = WorkItemCreateInput(
            title="Dentist",
            type="appointment",
            start_time="2026-05-10T14:00:00Z",
            end_time="2026-05-10T15:00:00Z",
        )
        assert data.type == ItemType.APPOINTMENT
        assert data.start_time == "2026-05-10T14:00:00Z"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="Bad", type="invalid_type")

    def test_strips_whitespace(self):
        data = WorkItemCreateInput(title="  hello  ", type="task")
        assert data.title == "hello"

    def test_forbids_extra_fields(self):
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="Test", type="task", unknown_field="x")

    def test_title_min_length(self):
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="", type="task")

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="x" * 501, type="task")

    def test_priority_range(self):
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="Test", type="task", priority=0)
        with pytest.raises(ValidationError):
            WorkItemCreateInput(title="Test", type="task", priority=6)

    def test_all_fields_optional_except_title_and_type(self):
        data = WorkItemCreateInput(title="Minimal", type="task")
        assert data.description is None
        assert data.priority is None
        assert data.due_date is None
        assert data.idempotency_key is None


class TestWorkItemUpdateInput:
    def test_all_fields_optional(self):
        data = WorkItemUpdateInput()
        assert data.model_dump(exclude_none=True) == {}

    def test_partial_update(self):
        data = WorkItemUpdateInput(title="New title")
        assert data.title == "New title"
        assert data.description is None
        assert data.priority is None
