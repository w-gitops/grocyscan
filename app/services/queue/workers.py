"""Job queue workers for background tasks."""

from typing import Any

from app.core.logging import get_logger
from app.services.grocy import grocy_client
from app.services.llm import optimize_product_name
from app.services.queue.manager import JobType, job_queue

logger = get_logger(__name__)


async def llm_optimize_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle LLM optimization jobs.

    Args:
        payload: Job payload with product info

    Returns:
        dict: Optimized product data
    """
    name = payload.get("name", "")
    brand = payload.get("brand")
    description = payload.get("description")

    result = await optimize_product_name(
        name=name,
        brand=brand,
        description=description,
    )

    return result


async def grocy_sync_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle Grocy sync jobs.

    Args:
        payload: Job payload with product/stock info

    Returns:
        dict: Sync result
    """
    action = payload.get("action")

    if action == "add_stock":
        product_id = payload.get("product_id")
        amount = payload.get("amount", 1)
        best_before = payload.get("best_before")
        price = payload.get("price")

        result = await grocy_client.add_to_stock(
            product_id=product_id,
            amount=amount,
            best_before_date=best_before,
            price=price,
        )
        return {"status": "synced", "result": result}

    elif action == "create_product":
        name = payload.get("name")
        result = await grocy_client.create_product(name=name)
        return {"status": "created", "product_id": result.get("created_object_id")}

    return {"status": "unknown_action"}


async def image_download_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle image download jobs.

    Args:
        payload: Job payload with image URL

    Returns:
        dict: Download result with local path
    """
    import httpx

    url = payload.get("url")
    barcode = payload.get("barcode")

    if not url:
        return {"status": "error", "message": "No URL provided"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

            # Save to local storage
            # For now, just return success
            return {
                "status": "downloaded",
                "content_type": response.headers.get("content-type"),
                "size": len(response.content),
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}


async def offline_sync_handler(payload: dict[str, Any]) -> dict[str, Any]:
    """Handle offline sync jobs.

    Processes queued operations from offline mode.

    Args:
        payload: Job payload with offline operations

    Returns:
        dict: Sync results
    """
    operations = payload.get("operations", [])
    results = []

    for op in operations:
        op_type = op.get("type")
        op_data = op.get("data", {})

        try:
            if op_type == "add_stock":
                result = await grocy_client.add_to_stock(
                    product_id=op_data.get("product_id"),
                    amount=op_data.get("amount", 1),
                    best_before_date=op_data.get("best_before"),
                )
                results.append({"status": "success", "result": result})
            else:
                results.append({"status": "unknown_type", "type": op_type})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})

    return {"synced": len([r for r in results if r["status"] == "success"]), "results": results}


def register_workers() -> None:
    """Register all worker handlers with the job queue."""
    job_queue.register_handler(JobType.LLM_OPTIMIZE, llm_optimize_handler)
    job_queue.register_handler(JobType.GROCY_SYNC, grocy_sync_handler)
    job_queue.register_handler(JobType.IMAGE_DOWNLOAD, image_download_handler)
    job_queue.register_handler(JobType.OFFLINE_SYNC, offline_sync_handler)

    logger.info("Job queue workers registered")
