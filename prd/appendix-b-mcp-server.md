# Appendix B: Model Context Protocol (MCP) Server

## B.1 Overview

GrocyScan exposes an MCP server that enables AI assistants (Claude, Cursor, custom agents) to:
- Look up product information by barcode
- Add products to inventory
- Search products by name
- Manage locations

## B.2 MCP Server Implementation

```python
# app/mcp/server.py
from mcp.server.fastmcp import FastMCP
from typing import Optional

mcp = FastMCP("GrocyScan MCP Server", json_response=True, version="1.0.0")


@mcp.tool()
async def lookup_barcode(barcode: str, include_nutrition: bool = True) -> dict:
    """
    Look up product information by barcode.
    
    Args:
        barcode: The barcode to look up (UPC, EAN, etc.)
        include_nutrition: Whether to include nutrition information
    
    Returns:
        Product details including name, category, brand, image URL
    """
    pass


@mcp.tool()
async def add_product_to_inventory(
    barcode: str,
    location_code: Optional[str] = None,
    best_before: Optional[str] = None,
    quantity: int = 1
) -> dict:
    """
    Add a product to the Grocy inventory.
    
    Args:
        barcode: The barcode of the product to add
        location_code: Storage location code (e.g., "LOC-PANTRY-01")
        best_before: Expiration date in ISO format (YYYY-MM-DD)
        quantity: Number of units to add (default: 1)
    """
    pass


@mcp.tool()
async def search_products(query: str, limit: int = 10) -> list[dict]:
    """Search for products by name."""
    pass


@mcp.tool()
async def get_expiring_products(days: int = 7) -> list[dict]:
    """Get products expiring within the specified number of days."""
    pass


@mcp.tool()
async def list_locations() -> list[dict]:
    """List all storage locations."""
    pass


@mcp.resource("grocyscan://inventory/summary")
async def get_inventory_summary() -> str:
    """Get a summary of the current inventory."""
    pass


@mcp.prompt()
def inventory_check_prompt(focus_area: str = "expiring") -> str:
    """Generate a prompt for inventory checking tasks."""
    pass


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=3335)
```

## B.3 MCP Skills Summary

| Skill | Type | Description | Approval |
|-------|------|-------------|----------|
| `lookup_barcode` | Tool | Look up product by barcode | Never |
| `add_product_to_inventory` | Tool | Add product to Grocy | Always |
| `search_products` | Tool | Search products by name | Never |
| `get_expiring_products` | Tool | List expiring items | Never |
| `list_locations` | Tool | List storage locations | Never |
| `grocyscan://inventory/summary` | Resource | Inventory overview | N/A |
| `inventory_check_prompt` | Prompt | Template for checks | N/A |

## B.4 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "grocyscan": {
      "url": "http://localhost:3335",
      "transport": "streamable-http",
      "headers": {
        "X-API-Key": "your-mcp-api-key"
      }
    }
  }
}
```

## B.5 LangChain Integration

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

client = MultiServerMCPClient({
    "grocyscan": {
        "url": "http://localhost:3335",
        "transport": "streamable-http"
    }
})

async with client.session("grocyscan") as session:
    tools = await load_mcp_tools(session)
    result = await session.call_tool("lookup_barcode", {"barcode": "012345678901"})
```

---

## Navigation

- **Previous:** [Appendix A - API Documentation](appendix-a-api-documentation.md)
- **Next:** [Appendix C - Environment Variables](appendix-c-environment-variables.md)
- **Back to:** [README](README.md)
