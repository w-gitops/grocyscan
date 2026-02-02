"""LLM-powered product name optimization and category inference."""

import json
from typing import Any

from app.core.logging import get_logger
from app.services.llm.client import llm_client

logger = get_logger(__name__)


OPTIMIZE_SYSTEM_PROMPT = """You are a product name optimizer for a grocery inventory system.
Your job is to clean and standardize product names from various barcode databases.

Rules:
1. Remove unnecessary qualifiers (organic, natural, etc.) unless part of brand
2. Standardize capitalization (Title Case)
3. Include brand name at start if known
4. Include size/quantity if present in original name
5. Keep names concise but descriptive
6. Fix obvious typos
7. Translate non-English names to English if possible

Output JSON format:
{
    "name": "Optimized product name",
    "brand": "Brand name if detected",
    "category": "Category (Dairy, Produce, Bakery, Frozen, Beverages, Snacks, Condiments, Canned, Meat, Seafood, Household, Personal Care, Baby, Pets, Other)",
    "quantity_unit": "Unit if detectable (pieces, g, ml, oz, lb, etc.)"
}"""


async def optimize_product_name(
    name: str,
    brand: str | None = None,
    description: str | None = None,
    raw_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Optimize a product name using LLM.

    Args:
        name: Original product name
        brand: Brand name if known
        description: Product description
        raw_data: Raw lookup data for additional context

    Returns:
        dict: Optimized product information
    """
    # Build prompt
    prompt_parts = [f"Product name: {name}"]

    if brand:
        prompt_parts.append(f"Brand: {brand}")
    if description:
        prompt_parts.append(f"Description: {description[:200]}")

    prompt = "\n".join(prompt_parts)
    prompt += "\n\nOptimize this product name and infer the category."

    try:
        response = await llm_client.complete(
            prompt=prompt,
            system_prompt=OPTIMIZE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=200,
        )

        # Parse JSON response
        # Handle potential markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        result = json.loads(response)
        logger.info(
            "Product name optimized",
            original=name,
            optimized=result.get("name"),
        )
        return result

    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse LLM response",
            name=name,
            error=str(e),
        )
        # Return original data on parse error
        return {
            "name": name,
            "brand": brand,
            "category": None,
            "quantity_unit": None,
        }
    except Exception as e:
        logger.error("LLM optimization failed", name=name, error=str(e))
        # Return original data on error
        return {
            "name": name,
            "brand": brand,
            "category": None,
            "quantity_unit": None,
        }


MERGE_SYSTEM_PROMPT = """You are a data reconciliation system for grocery products.
Multiple lookup providers returned different data for the same barcode.
Your job is to merge them into the best possible product record.

Rules:
1. Prefer more complete/detailed names
2. Prefer known brands over generic descriptions
3. Combine nutritional data if available from multiple sources
4. Pick the most specific category
5. Prefer higher quality images (prefer URLs from major sites)

Output JSON format:
{
    "name": "Best product name",
    "brand": "Brand name",
    "description": "Description",
    "category": "Category",
    "image_url": "Best image URL",
    "selected_source": "Provider name that contributed most data"
}"""


async def merge_lookup_results(
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge multiple lookup results using LLM.

    Args:
        results: List of lookup results from different providers

    Returns:
        dict: Merged product information
    """
    if len(results) == 1:
        return results[0]

    # Build prompt with all results
    prompt_parts = ["Multiple providers returned data for this barcode:\n"]

    for i, result in enumerate(results, 1):
        prompt_parts.append(f"Source {i} ({result.get('provider', 'unknown')}):")
        prompt_parts.append(f"  Name: {result.get('name', 'N/A')}")
        prompt_parts.append(f"  Brand: {result.get('brand', 'N/A')}")
        prompt_parts.append(f"  Category: {result.get('category', 'N/A')}")
        prompt_parts.append(f"  Image: {'Yes' if result.get('image_url') else 'No'}")
        prompt_parts.append("")

    prompt = "\n".join(prompt_parts)
    prompt += "\nMerge these into the best possible product record."

    try:
        response = await llm_client.complete(
            prompt=prompt,
            system_prompt=MERGE_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=300,
        )

        # Parse JSON response
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]

        merged = json.loads(response)

        # Get image URL from the selected source
        selected_source = merged.get("selected_source", "").lower()
        for result in results:
            if result.get("provider", "").lower() == selected_source:
                if result.get("image_url") and not merged.get("image_url"):
                    merged["image_url"] = result["image_url"]
                break

        logger.info(
            "Lookup results merged",
            sources=[r.get("provider") for r in results],
            selected=merged.get("selected_source"),
        )
        return merged

    except Exception as e:
        logger.error("LLM merge failed", error=str(e))
        # Fall back to first result with most data
        best = max(results, key=lambda r: sum(1 for v in r.values() if v))
        return best
