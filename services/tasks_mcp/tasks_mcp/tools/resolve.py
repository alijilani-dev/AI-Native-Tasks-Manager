import json

from mcp.types import ToolAnnotations

from tasks_mcp.errors import handle_api_error
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import resolve


@mcp.tool(
    name="tasks_resolve",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_resolve(
    user_id: str,
    item_id: str,
    status: str,
    note: str | None = None,
    idempotency_key: str | None = None,
) -> str:
    '''Set a terminal status on a work item: completed, cancelled, or skipped.

    Args:
        user_id: User identifier for data scoping
        item_id: ID of the work item to resolve
        status: "completed", "cancelled", or "skipped"
        note: Optional note about the resolution
        idempotency_key: UUID for deduplication

    Returns:
        JSON string of the resolved work item.
    '''
    try:
        result = resolve(item_id, user_id, status, note, idempotency_key)
        if result is None:
            return "Error: Item not found. Check the item_id and try again."
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return handle_api_error(e)
