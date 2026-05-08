from datetime import datetime, timezone
from uuid import uuid4

from tasks_mcp.models.work_item import ItemStatus

_store: dict[str, dict] = {}
_idempotency: dict[str, dict] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _make_item(user_id: str, data: dict) -> dict:
    item_id = str(uuid4())
    now = _now()
    return {
        "id": item_id,
        "user_id": user_id,
        "title": data.get("title", ""),
        "type": data.get("type", "task"),
        "status": ItemStatus.PENDING.value,
        "description": data.get("description"),
        "priority": data.get("priority"),
        "due_date": data.get("due_date"),
        "reminder_at": data.get("reminder_at"),
        "start_time": data.get("start_time"),
        "end_time": data.get("end_time"),
        "location": data.get("location"),
        "participants": data.get("participants"),
        "created_at": now,
        "updated_at": now,
    }


def create(user_id: str, data: dict, idempotency_key: str | None = None) -> dict:
    if idempotency_key and idempotency_key in _idempotency:
        return dict(_idempotency[idempotency_key])

    item = _make_item(user_id, data)
    _store[item["id"]] = item

    if idempotency_key:
        _idempotency[idempotency_key] = dict(item)

    return item


def get(item_id: str) -> dict | None:
    item = _store.get(item_id)
    return dict(item) if item else None


def list_items(
    user_id: str,
    status: str | None = None,
    item_type: str | None = None,
    search_text: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    is_overdue: bool | None = None,
    priority: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    items = [v for v in _store.values() if v["user_id"] == user_id]

    if status:
        items = [v for v in items if v["status"] == status]
    if item_type:
        items = [v for v in items if v["type"] == item_type]
    if search_text:
        st = search_text.lower()
        items = [
            v for v in items
            if (v.get("title") and st in v["title"].lower())
            or (v.get("description") and st in v["description"].lower())
        ]
    if date_from:
        items = [v for v in items if v.get("due_date") and v["due_date"] >= date_from]
    if date_to:
        items = [v for v in items if v.get("due_date") and v["due_date"] <= date_to]
    if is_overdue:
        now = _now()
        items = [
            v for v in items
            if v.get("due_date") and v["due_date"] < now and v["status"] == ItemStatus.PENDING.value
        ]
    if priority is not None:
        items = [v for v in items if v.get("priority") == priority]

    items.sort(key=lambda x: x["created_at"], reverse=True)
    total = len(items)
    page = items[offset:offset + limit]
    return {
        "items": page,
        "total": total,
        "offset": offset,
    }


def update(item_id: str, user_id: str, data: dict, idempotency_key: str | None = None) -> dict | None:
    if idempotency_key and idempotency_key in _idempotency:
        return dict(_idempotency[idempotency_key])

    item = _store.get(item_id)
    if not item or item["user_id"] != user_id:
        return None

    for key in ("title", "description", "priority", "due_date", "reminder_at",
                 "start_time", "end_time", "location", "participants"):
        if key in data:
            item[key] = data[key]
    item["updated_at"] = _now()
    _store[item_id] = item

    if idempotency_key:
        _idempotency[idempotency_key] = dict(item)

    return dict(item)


def resolve(item_id: str, user_id: str, status: str, note: str | None = None,
            idempotency_key: str | None = None) -> dict | None:
    if idempotency_key and idempotency_key in _idempotency:
        return dict(_idempotency[idempotency_key])

    item = _store.get(item_id)
    if not item or item["user_id"] != user_id:
        return None

    new_status = status
    item["status"] = new_status
    if note:
        item["resolution_note"] = note
    item["updated_at"] = _now()
    _store[item_id] = item

    if idempotency_key:
        _idempotency[idempotency_key] = dict(item)

    return dict(item)


def delete(item_id: str, user_id: str, idempotency_key: str | None = None) -> bool:
    if idempotency_key and idempotency_key in _idempotency:
        return True

    item = _store.get(item_id)
    if not item or item["user_id"] != user_id:
        return False
    del _store[item_id]

    if idempotency_key:
        _idempotency[idempotency_key] = {"deleted": True, "id": item_id}

    return True


def clear():
    _store.clear()
    _idempotency.clear()
