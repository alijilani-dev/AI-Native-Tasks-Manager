import json

from mcp.types import ToolAnnotations

from tasks_mcp.errors import handle_api_error
from tasks_mcp.mcp_instance import mcp
from tasks_mcp.storage import delete


@mcp.tool(
    name="tasks_remove",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
async def tasks_remove(
    user_id: str,
    item_id: str,
    idempotency_key: str | None = None,
) -> str:
    '''Permanently delete a work item. Requires user confirmation.

    Args:
        user_id: User identifier for data scoping
        item_id: ID of the work item to delete
        idempotency_key: UUID for deduplication

    Returns:
        Confirmation message in JSON format.
    '''
    try:
        success = delete(item_id, user_id, idempotency_key)
        if not success:
            return "Error: Item not found. Check the item_id and try again."
        return json.dumps({"deleted": True, "id": item_id}, indent=2)
    except Exception as e:
        return handle_api_error(e)
