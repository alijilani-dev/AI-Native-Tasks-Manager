import pytest

from tasks_mcp.storage import clear, create, delete, get, list_items, resolve, update


@pytest.fixture(autouse=True)
def reset_storage():
    clear()
    yield


class TestCreate:
    def test_create_task(self):
        item = create("user1", {"title": "Buy milk", "type": "task"})
        assert item["title"] == "Buy milk"
        assert item["user_id"] == "user1"
        assert item["status"] == "pending"
        assert "id" in item

    def test_create_appointment(self):
        item = create("user1", {
            "title": "Dentist", "type": "appointment",
            "start_time": "2026-05-10T14:00:00Z",
        })
        assert item["type"] == "appointment"
        assert item["start_time"] == "2026-05-10T14:00:00Z"

    def test_idempotency_returns_same(self):
        item1 = create("user1", {"title": "Dup"}, idempotency_key="abc")
        item2 = create("user1", {"title": "Dup"}, idempotency_key="abc")
        assert item1["id"] == item2["id"]


class TestGet:
    def test_get_existing(self):
        item = create("user1", {"title": "Test"})
        found = get(item["id"])
        assert found is not None
        assert found["title"] == "Test"

    def test_get_missing(self):
        assert get("nonexistent") is None


class TestList:
    def test_list_by_user(self):
        create("user1", {"title": "A"})
        create("user1", {"title": "B"})
        create("user2", {"title": "C"})
        result = list_items("user1")
        assert result["total"] == 2

    def test_list_by_status(self):
        create("user1", {"title": "A"})
        item2 = create("user1", {"title": "B"})
        resolve(item2["id"], "user1", "completed")
        result = list_items("user1", status="completed")
        assert result["total"] == 1

    def test_list_pagination(self):
        for i in range(25):
            create("user1", {"title": f"Item {i}"})
        result = list_items("user1", limit=10, offset=0)
        assert result["total"] == 25
        assert len(result["items"]) == 10

    def test_list_by_type(self):
        create("user1", {"title": "Task", "type": "task"})
        create("user1", {"title": "Appt", "type": "appointment"})
        result = list_items("user1", item_type="appointment")
        assert result["total"] == 1

    def test_list_search_text_title(self):
        create("user1", {"title": "Buy milk"})
        create("user1", {"title": "Call mom"})
        result = list_items("user1", search_text="milk")
        assert result["total"] == 1

    def test_list_search_text_description(self):
        create("user1", {"title": "Task", "description": "Important meeting notes"})
        create("user1", {"title": "Other"})
        result = list_items("user1", search_text="meeting")
        assert result["total"] == 1

    def test_list_date_from(self):
        create("user1", {"title": "Old", "due_date": "2025-01-01T00:00:00Z"})
        create("user1", {"title": "New", "due_date": "2026-06-01T00:00:00Z"})
        result = list_items("user1", date_from="2026-01-01T00:00:00Z")
        assert result["total"] == 1
        assert result["items"][0]["title"] == "New"

    def test_list_date_to(self):
        create("user1", {"title": "Old", "due_date": "2025-01-01T00:00:00Z"})
        create("user1", {"title": "New", "due_date": "2026-06-01T00:00:00Z"})
        result = list_items("user1", date_to="2026-01-01T00:00:00Z")
        assert result["total"] == 1
        assert result["items"][0]["title"] == "Old"

    def test_list_is_overdue(self):
        create("user1", {"title": "Past due", "due_date": "2020-01-01T00:00:00Z"})
        create("user1", {"title": "Future", "due_date": "2099-01-01T00:00:00Z"})
        result = list_items("user1", is_overdue=True)
        assert result["total"] == 1
        assert result["items"][0]["title"] == "Past due"

    def test_list_priority(self):
        create("user1", {"title": "High", "priority": 1})
        create("user1", {"title": "Low", "priority": 5})
        result = list_items("user1", priority=1)
        assert result["total"] == 1


class TestUpdate:
    def test_update_title(self):
        item = create("user1", {"title": "Old"})
        updated = update(item["id"], "user1", {"title": "New"})
        assert updated["title"] == "New"

    def test_update_nonexistent(self):
        assert update("bad_id", "user1", {"title": "X"}) is None

    def test_update_wrong_user(self):
        item = create("user1", {"title": "X"})
        assert update(item["id"], "user2", {"title": "Y"}) is None


class TestResolve:
    def test_resolve_completed(self):
        item = create("user1", {"title": "X"})
        resolved = resolve(item["id"], "user1", "completed")
        assert resolved["status"] == "completed"

    def test_resolve_nonexistent(self):
        assert resolve("bad", "user1", "completed") is None


class TestDelete:
    def test_delete_existing(self):
        item = create("user1", {"title": "X"})
        assert delete(item["id"], "user1") is True
        assert get(item["id"]) is None

    def test_delete_nonexistent(self):
        assert delete("bad", "user1") is False

    def test_delete_wrong_user(self):
        item = create("user1", {"title": "X"})
        assert delete(item["id"], "user2") is False

    def test_delete_idempotency(self):
        item = create("user1", {"title": "Dup"})
        assert delete(item["id"], "user1", idempotency_key="del-1") is True
        assert get(item["id"]) is None
        assert delete(item["id"], "user1", idempotency_key="del-1") is True


class TestResolveWithNote:
    def test_resolve_with_note(self):
        item = create("user1", {"title": "X"})
        resolved = resolve(item["id"], "user1", "completed", note="All done")
        assert resolved["status"] == "completed"
        assert resolved["resolution_note"] == "All done"


class TestUpdateIdempotency:
    def test_update_idempotency(self):
        item = create("user1", {"title": "X"})
        updated1 = update(item["id"], "user1", {"title": "Y"}, idempotency_key="up-1")
        updated2 = update(item["id"], "user1", {"title": "Z"}, idempotency_key="up-1")
        assert updated1["title"] == "Y"
        assert updated2["title"] == "Y"
