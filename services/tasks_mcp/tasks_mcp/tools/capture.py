import json

from mcp.types import ToolAnnotations

from tasks_mcp.errors import handle_api_error
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import create


@mcp.tool(
    name="tasks_capture",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_capture(
    title: str,
    type: str,
    user_id: str = "default",
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
    '''Create any work item — task, appointment, or reminder — in one call.

    Accepts all fields for all item types. The `type` field determines which
    fields are relevant. Returns the created item with its assigned ID.

    Args:
        title: Item title (e.g. 'Call mom', 'Dentist appointment')
        type: "task", "appointment", or "reminder"
        user_id: User identifier for data scoping (default: "default")
        description: Optional detailed notes
        priority: 1 (highest) to 5 (lowest)
        due_date: ISO 8601 UTC due date
        reminder_at: ISO 8601 UTC reminder trigger time
        start_time: ISO 8601 UTC start time (appointments)
        end_time: ISO 8601 UTC end time (appointments)
        location: Physical or virtual location
        participants: List of participant identifiers
        idempotency_key: UUID for deduplication

    Returns:
        JSON string of the created work item.
    '''
    try:
        data = create(user_id, {
            "title": title,
            "type": type,
            "description": description,
            "priority": priority,
            "due_date": due_date,
            "reminder_at": reminder_at,
            "start_time": start_time,
            "end_time": end_time,
            "location": location,
            "participants": participants,
        }, idempotency_key)
        return json.dumps(data, indent=2, default=str)
    except Exception as e:
        return handle_api_error(e)
