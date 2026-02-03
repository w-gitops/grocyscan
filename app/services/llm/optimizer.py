"""LLM-powered product name optimization and category inference."""

import json
from typing import Any

from app.core.logging import get_logger
from app.services.llm.client import llm_client

logger = get_logger(__name__)


OPTIMIZE_SYSTEM_PROMPT = """You are a product data formatter for a grocery inventory system (Grocy).
Your job is to turn raw barcode/lookup data into clean, consistent product records: standard title, short description, brand, and category.

Rules for the product name (title):
1. Use Title Case. Keep concise but descriptive (e.g. "Milk Chocolate Bar 100g").
2. Put brand at the start only if it is a well-known brand (e.g. "Lindt Dark Chocolate Bar").
3. Include size/quantity when present (e.g. "500 ml", "12 oz").
4. Remove filler (organic, natural, etc.) unless it defines the product.
5. Fix typos. Prefer English if the input was mixed language.

Rules for the description:
1. One or two short sentences: what the product is and key info (e.g. ingredients, use).
2. No marketing fluff. Useful for someone scanning the pantry later.
3. If no good description is available, leave as empty string.

Rules for brand:
1. Only set if clearly a brand name (e.g. Nestlé, Coca-Cola, store brand). Otherwise empty string.
2. Use standard spelling and capitalization.

Output JSON only, no markdown:
{
    "name": "Clean product title",
    "description": "Short product description or empty string",
    "brand": "Brand name or empty string",
    "category": "One of: Dairy, Produce, Bakery, Frozen, Beverages, Snacks, Condiments, Canned, Meat, Seafood, Household, Personal Care, Baby, Pets, Other",
    "quantity_unit": "pieces, g, ml, oz, lb, etc. or null if unknown"
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

    if raw_data:
        prompt_parts.append(f"Raw context: {str(raw_data)[:300]}")
    prompt = "\n".join(prompt_parts)
    prompt += "\n\nReturn optimized product name, description, brand, and category as JSON."

    try:
        response = await llm_client.complete(
            prompt=prompt,
            system_prompt=OPTIMIZE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=400,
        )

        # Parse JSON response (handle markdown code blocks)
        response = response.strip()
        if "```" in response:
            parts = response.split("```")
            for p in parts:
                p = p.strip()
                if p.startswith("json"):
                    p = p[4:].strip()
                if p.startswith("{"):
                    response = p
                    break

        result = json.loads(response)
        # Normalize keys and ensure required fields
        out = {
            "name": (result.get("name") or name).strip() or name,
            "description": (result.get("description") or "").strip(),
            "brand": (result.get("brand") or "").strip() or (brand or ""),
            "category": (result.get("category") or "").strip() or None,
            "quantity_unit": result.get("quantity_unit") or None,
        }
        logger.info(
            "Product data optimized",
            original=name,
            title=out["name"],
            has_description=bool(out["description"]),
            brand=out["brand"] or None,
        )
        return out

    except json.JSONDecodeError as e:
        logger.warning(
            "Failed to parse LLM response",
            name=name,
            error=str(e),
        )
        return {
            "name": name,
            "description": (description or "")[:500] if description else "",
            "brand": brand or "",
            "category": None,
            "quantity_unit": None,
        }
    except Exception as e:
        logger.error("LLM optimization failed", name=name, error=str(e))
        return {
            "name": name,
            "description": (description or "")[:500] if description else "",
            "brand": brand or "",
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
