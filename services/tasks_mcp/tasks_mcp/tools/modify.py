import json

from mcp.types import ToolAnnotations

from tasks_mcp.errors import handle_api_error
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import update


@mcp.tool(
    name="tasks_modify",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_modify(
    user_id: str,
    item_id: str,
    title: str | None = None,
    description: str | None = None,
    priority: int | None = None,
    due_date: str | None = None,
    reminder_at: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    participants: list[str] | None = None,
    idempotency_key: str | None = None,
) -> str:
    '''Update any field(s) on an existing work item.

    Send only the fields you want to change. Unset fields are preserved.

    Args:
        user_id: User identifier for data scoping
        item_id: ID of the work item to modify
        title: New title
        description: New description
        priority: New priority (1-5)
        due_date: New ISO 8601 UTC due date
        reminder_at: New ISO 8601 UTC reminder time
        start_time: New ISO 8601 UTC start time
        end_time: New ISO 8601 UTC end time
        location: New location
        participants: New participant list
        idempotency_key: UUID for deduplication

    Returns:
        JSON string of the updated work item.
    '''
    try:
        body: dict = {}
        if title is not None:
            body["title"] = title
        if description is not None:
            body["description"] = description
        if priority is not None:
            body["priority"] = priority
        if due_date is not None:
            body["due_date"] = due_date
        if reminder_at is not None:
            body["reminder_at"] = reminder_at
        if start_time is not None:
            body["start_time"] = start_time
        if end_time is not None:
            body["end_time"] = end_time
        if location is not None:
            body["location"] = location
        if participants is not None:
            body["participants"] = participants

        result = update(item_id, user_id, body, idempotency_key)
        if result is None:
            return "Error: Item not found. Check the item_id and try again."
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return handle_api_error(e)
