# Feature PRD: Product Name Search on Scan Page

**Version:** 1.0  
**Date:** February 2, 2026  
**Status:** Draft  
**Related User Story:** US-24 (Product Search by Name)

---

## 1. Overview

This feature adds the ability to search for products by name directly on the scan page, enabling users to add inventory for products without scanning a barcode. This is useful for items with damaged/missing barcodes, produce without barcodes, or when quickly adding known products.

### 1.1 Problem Statement

Currently, adding products to inventory requires scanning a barcode. This creates friction when:
1. A product's barcode is damaged, smudged, or missing
2. The product has no barcode (e.g., loose produce, bulk items)
3. The user knows exactly what product they want to add
4. The barcode scanner fails to read a code

### 1.2 Solution

Add a search interface to the scan page that allows users to:
- Search existing Grocy products by name
- Select a product from search results
- Proceed to the review popup to add quantity/location/date
- Maintain the same workflow as barcode scanning

---

## 2. User Story

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-PNS-1** | user | search for products by name on the scan page | I can add inventory without scanning | Search input visible, results show matching products, selecting opens review popup | P1 |
| **US-PNS-2** | user | see product images and details in search results | I can identify the correct product | Results show name, category, image thumbnail | P1 |
| **US-PNS-3** | user | search both local cache and Grocy products | I find products regardless of source | Combined results from database and Grocy API | P1 |

---

## 3. Functional Requirements

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-PNS-1** | Search toggle/tab | Add toggle or tab to switch between barcode input and name search |
| **FR-PNS-2** | Search input | Text input with debounced search (300ms delay) |
| **FR-PNS-3** | Search API | Implement `POST /api/products/search` endpoint |
| **FR-PNS-4** | Grocy integration | Search Grocy products via API (client-side filtering) |
| **FR-PNS-5** | Local database search | Search local products using `name_normalized` field |
| **FR-PNS-6** | Combined results | Merge and deduplicate results from Grocy and local DB |
| **FR-PNS-7** | Result display | Show product name, category, image, and source indicator |
| **FR-PNS-8** | Product selection | Clicking a result opens review popup with product pre-filled |
| **FR-PNS-9** | Empty state | Show helpful message when no results found |
| **FR-PNS-10** | Minimum query length | Require at least 2 characters before searching |

---

## 4. UI Specification

### 4.1 Mode Toggle

Add a toggle to switch between barcode scanning and name search modes:

```
┌─────────────────────────────────────────────────────────────────┐
│  GrocyScan                              [Location: PANTRY-01] ⚙️  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  [ 📷 Scan Barcode ]  [ 🔍 Search by Name ]                 ││
│  │        ^                      ^                              ││
│  │    (active)              (inactive)                          ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ... (mode-specific content below) ...                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Barcode Mode (Default)

Same as current implementation:

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Barcode                                                   │  │
│  │ [Scan or enter barcode...                              ]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  [📷 Camera]  [▣ Scanner Gun Mode]  [🔍 Search]                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Name Search Mode

```
┌─────────────────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Product Name                                              │  │
│  │ [Search products...                                    ]  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Search Results (3 found)                                 │  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────┐                                                  │  │
│  │  │ 🖼️  │  Chobani Strawberry Greek Yogurt                 │  │
│  │  │     │  Dairy / Yogurt  •  From: Grocy                  │  │
│  │  └─────┘                                           [Add →]│  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────┐                                                  │  │
│  │  │ 🖼️  │  Chobani Vanilla Greek Yogurt                    │  │
│  │  │     │  Dairy / Yogurt  •  From: Grocy                  │  │
│  │  └─────┘                                           [Add →]│  │
│  ├───────────────────────────────────────────────────────────┤  │
│  │  ┌─────┐                                                  │  │
│  │  │ 🖼️  │  Chobani Blueberry Greek Yogurt                  │  │
│  │  │     │  Dairy / Yogurt  •  From: Local                  │  │
│  │  └─────┘                                           [Add →]│  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Empty/Loading States

**Loading:**
```
┌───────────────────────────────────────────────────────────┐
│  ⟳ Searching...                                           │
└───────────────────────────────────────────────────────────┘
```

**No Results:**
```
┌───────────────────────────────────────────────────────────┐
│  No products found matching "xyz"                         │
│                                                           │
│  Try a different search term or scan the barcode instead. │
└───────────────────────────────────────────────────────────┘
```

**Minimum Characters:**
```
┌───────────────────────────────────────────────────────────┐
│  Type at least 2 characters to search                     │
└───────────────────────────────────────────────────────────┘
```

---

## 5. Technical Implementation

### 5.1 API Endpoint

**File: `app/api/routes/products.py`**

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ProductSearchRequest(BaseModel):
    """Search parameters for products."""
    query: str = Field(..., min_length=2, max_length=200)
    include_grocy: bool = True
    limit: int = Field(20, ge=1, le=100)

class ProductSearchResult(BaseModel):
    """Single product search result."""
    id: str  # UUID or Grocy ID
    name: str
    category: Optional[str] = None
    image_url: Optional[str] = None
    source: str  # "grocy" or "local"
    grocy_product_id: Optional[int] = None

class ProductSearchResponse(BaseModel):
    """Search response with results."""
    results: List[ProductSearchResult]
    total: int
    query: str

@router.post("/search", response_model=ProductSearchResponse)
async def search_products(
    request: ProductSearchRequest,
    db: AsyncSession = Depends(get_db),
    grocy: GrocyClient = Depends(get_grocy_client),
) -> ProductSearchResponse:
    """Search products by name.
    
    Searches both local database and Grocy API, merging results.
    """
    results = []
    query_lower = request.query.lower()
    
    # Search local database
    local_results = await db.execute(
        select(Product)
        .where(Product.name_normalized.ilike(f"%{query_lower}%"))
        .limit(request.limit)
    )
    for product in local_results.scalars():
        results.append(ProductSearchResult(
            id=str(product.id),
            name=product.name,
            category=product.category,
            image_url=product.image_path,
            source="local",
            grocy_product_id=product.grocy_product_id,
        ))
    
    # Search Grocy products
    if request.include_grocy:
        grocy_products = await grocy.get_products()
        for gp in grocy_products:
            if query_lower in gp.get("name", "").lower():
                # Skip if already in results (by grocy_product_id)
                if any(r.grocy_product_id == gp["id"] for r in results):
                    continue
                results.append(ProductSearchResult(
                    id=f"grocy-{gp['id']}",
                    name=gp["name"],
                    category=gp.get("product_group", {}).get("name"),
                    image_url=None,  # Grocy images need separate fetch
                    source="grocy",
                    grocy_product_id=gp["id"],
                ))
    
    # Sort by relevance (exact match first, then alphabetical)
    results.sort(key=lambda r: (
        0 if r.name.lower() == query_lower else 1,
        r.name.lower()
    ))
    
    return ProductSearchResponse(
        results=results[:request.limit],
        total=len(results),
        query=request.query,
    )
```

### 5.2 UI Component

**File: `app/ui/components/product_search.py`** (new file)

```python
"""Product name search component for NiceGUI."""

import asyncio
from typing import Callable, Coroutine, Any, Union, List
from nicegui import ui
from pydantic import BaseModel

class ProductSearchResult(BaseModel):
    id: str
    name: str
    category: str | None
    image_url: str | None
    source: str
    grocy_product_id: int | None

class ProductSearch:
    """Product search component with debounced input and results list."""
    
    def __init__(
        self,
        on_select: Callable[[ProductSearchResult], Union[None, Coroutine[Any, Any, None]]],
        debounce_ms: int = 300,
    ) -> None:
        self.on_select = on_select
        self.debounce_ms = debounce_ms
        self._input: ui.input | None = None
        self._results_container: ui.column | None = None
        self._search_task: asyncio.Task | None = None
        self._results: List[ProductSearchResult] = []

    def render(self) -> None:
        """Render the search component."""
        with ui.column().classes("w-full gap-2"):
            self._input = ui.input(
                label="Product Name",
                placeholder="Search products...",
                on_change=self._handle_input_change,
            ).classes("w-full").props('clearable prepend-icon="search"')
            
            self._results_container = ui.column().classes("w-full gap-1")
            
            with self._results_container:
                ui.label("Type at least 2 characters to search").classes(
                    "text-gray-500 text-sm"
                )

    async def _handle_input_change(self, e: Any) -> None:
        """Handle search input changes with debouncing."""
        # Cancel previous search task
        if self._search_task and not self._search_task.done():
            self._search_task.cancel()
        
        query = e.value.strip() if e.value else ""
        
        if len(query) < 2:
            self._show_minimum_chars_message()
            return
        
        # Debounce: wait before searching
        self._search_task = asyncio.create_task(
            self._debounced_search(query)
        )

    async def _debounced_search(self, query: str) -> None:
        """Execute search after debounce delay."""
        await asyncio.sleep(self.debounce_ms / 1000)
        await self._execute_search(query)

    async def _execute_search(self, query: str) -> None:
        """Execute the product search API call."""
        self._show_loading()
        
        try:
            # Call search API
            response = await self._call_search_api(query)
            self._results = response.get("results", [])
            self._display_results(query)
        except Exception as e:
            self._show_error(str(e))

    async def _call_search_api(self, query: str) -> dict:
        """Call the product search API endpoint."""
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "/api/products/search",
                json={"query": query, "include_grocy": True, "limit": 20},
            )
            response.raise_for_status()
            return response.json()

    def _display_results(self, query: str) -> None:
        """Display search results."""
        self._results_container.clear()
        
        if not self._results:
            with self._results_container:
                with ui.card().classes("w-full p-4"):
                    ui.label(f'No products found matching "{query}"').classes(
                        "text-gray-600"
                    )
                    ui.label(
                        "Try a different search term or scan the barcode instead."
                    ).classes("text-gray-500 text-sm")
            return
        
        with self._results_container:
            ui.label(f"Search Results ({len(self._results)} found)").classes(
                "text-sm text-gray-600 font-medium"
            )
            
            for result in self._results:
                self._render_result_card(result)

    def _render_result_card(self, result: dict) -> None:
        """Render a single search result card."""
        with ui.card().classes("w-full cursor-pointer hover:bg-gray-50").on(
            "click", lambda r=result: self._handle_select(r)
        ):
            with ui.row().classes("w-full items-center gap-3 p-2"):
                # Image thumbnail
                if result.get("image_url"):
                    ui.image(result["image_url"]).classes("w-12 h-12 object-cover rounded")
                else:
                    with ui.element("div").classes(
                        "w-12 h-12 bg-gray-200 rounded flex items-center justify-center"
                    ):
                        ui.icon("inventory_2").classes("text-gray-400")
                
                # Product info
                with ui.column().classes("flex-grow gap-0"):
                    ui.label(result["name"]).classes("font-medium")
                    with ui.row().classes("gap-2 text-sm text-gray-500"):
                        if result.get("category"):
                            ui.label(result["category"])
                            ui.label("•")
                        ui.label(f"From: {result['source'].title()}")
                
                # Add button
                ui.button(icon="add", on_click=lambda r=result: self._handle_select(r)).props(
                    "flat round color=primary"
                )

    async def _handle_select(self, result: dict) -> None:
        """Handle product selection."""
        import inspect
        product = ProductSearchResult(**result)
        callback_result = self.on_select(product)
        if inspect.iscoroutine(callback_result):
            await callback_result

    def _show_loading(self) -> None:
        """Show loading state."""
        self._results_container.clear()
        with self._results_container:
            with ui.row().classes("w-full justify-center p-4"):
                ui.spinner()
                ui.label("Searching...").classes("ml-2")

    def _show_minimum_chars_message(self) -> None:
        """Show minimum characters message."""
        self._results_container.clear()
        with self._results_container:
            ui.label("Type at least 2 characters to search").classes(
                "text-gray-500 text-sm"
            )

    def _show_error(self, message: str) -> None:
        """Show error message."""
        self._results_container.clear()
        with self._results_container:
            ui.label(f"Search error: {message}").classes("text-red-500")
```

### 5.3 Scan Page Integration

**File: `app/ui/pages/scan.py`**

```python
from app.ui.components.product_search import ProductSearch, ProductSearchResult

class ScanPage:
    def __init__(self):
        # ... existing code ...
        self._scan_mode: str = "barcode"  # "barcode" or "search"
        self._product_search: ProductSearch | None = None

    def render(self) -> None:
        # ... header code ...
        
        with ui.card().classes("w-full"):
            # Mode toggle
            with ui.row().classes("w-full gap-2 mb-4"):
                ui.button(
                    "Scan Barcode",
                    icon="qr_code_scanner",
                    on_click=lambda: self._set_mode("barcode"),
                ).props(
                    "color=primary" if self._scan_mode == "barcode" else "flat"
                )
                ui.button(
                    "Search by Name",
                    icon="search",
                    on_click=lambda: self._set_mode("search"),
                ).props(
                    "color=primary" if self._scan_mode == "search" else "flat"
                )
            
            # Mode-specific content
            self._mode_container = ui.column().classes("w-full")
            self._render_mode_content()

    def _set_mode(self, mode: str) -> None:
        """Switch between barcode and search modes."""
        self._scan_mode = mode
        self._render_mode_content()

    def _render_mode_content(self) -> None:
        """Render content for current mode."""
        self._mode_container.clear()
        
        with self._mode_container:
            if self._scan_mode == "barcode":
                self.scanner = BarcodeScanner(on_scan=self.handle_scan)
                self.scanner.render()
            else:
                self._product_search = ProductSearch(
                    on_select=self._handle_product_select
                )
                self._product_search.render()

    async def _handle_product_select(self, product: ProductSearchResult) -> None:
        """Handle product selection from search results."""
        # Create scan-like data structure for review popup
        scan_data = {
            "barcode": None,  # No barcode for name search
            "product": {
                "name": product.name,
                "category": product.category,
                "image_url": product.image_url,
                "grocy_product_id": product.grocy_product_id,
            },
            "source": product.source,
            "is_name_search": True,
        }
        
        # Open review popup
        self.review_popup.open(scan_data)
```

---

## 6. Acceptance Criteria

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Mode toggle visible on scan page | Visual inspection |
| 2 | "Search by Name" button switches to search mode | Click and verify UI change |
| 3 | Search input appears in search mode | Visual inspection |
| 4 | Typing shows "minimum 2 characters" message | Type 1 char, verify message |
| 5 | Search executes after 300ms debounce | Type query, verify delay |
| 6 | Results display with name, category, image | Search and verify result cards |
| 7 | Clicking result opens review popup | Click result, verify popup |
| 8 | Review popup pre-filled with product data | Verify name/category in popup |
| 9 | Grocy products appear in results | Search for known Grocy product |
| 10 | Local products appear in results | Search for cached product |
| 11 | No duplicate results for same product | Verify deduplication |
| 12 | "No results" message shows appropriately | Search for gibberish |
| 13 | Can switch back to barcode mode | Click "Scan Barcode", verify |

---

## 7. Testing Requirements

### 7.1 Unit Tests

```python
# tests/unit/api/test_products.py

async def test_product_search_local_db():
    """Test searching local products."""
    # Create test product
    product = Product(name="Test Yogurt", name_normalized="test yogurt")
    db.add(product)
    
    # Search
    response = await client.post("/api/products/search", json={
        "query": "yogurt",
        "include_grocy": False,
    })
    
    assert response.status_code == 200
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "Test Yogurt"

async def test_product_search_minimum_length():
    """Test minimum query length validation."""
    response = await client.post("/api/products/search", json={
        "query": "a",  # Too short
    })
    
    assert response.status_code == 422  # Validation error

async def test_product_search_deduplication():
    """Test that Grocy products with local copies are deduplicated."""
    # Create local product linked to Grocy
    product = Product(name="Milk", grocy_product_id=123)
    db.add(product)
    
    # Mock Grocy to return same product
    mock_grocy.get_products.return_value = [{"id": 123, "name": "Milk"}]
    
    response = await client.post("/api/products/search", json={
        "query": "milk",
        "include_grocy": True,
    })
    
    # Should only have one result
    assert len(response.json()["results"]) == 1
```

### 7.2 Integration Tests

```python
# tests/integration/test_scan_page.py

async def test_product_search_mode():
    """Test switching to product search mode."""
    # Navigate to scan page
    # Click "Search by Name" button
    # Verify search input appears
    # Type search query
    # Verify results display
    # Click result
    # Verify review popup opens
    pass
```

### 7.3 Browser Tests (MCP)

Using cursor-browser-extension MCP tools:
1. Navigate to scan page
2. Click "Search by Name" toggle
3. Type product name in search input
4. Wait for results to load
5. Take screenshot of search results
6. Click a result
7. Verify review popup opens with product data

---

## 8. Implementation Notes

### 8.1 Performance Considerations

- **Debouncing**: 300ms delay prevents excessive API calls while typing
- **Grocy caching**: Consider caching Grocy product list for 5 minutes
- **Result limit**: Default 20 results to prevent slow rendering
- **Pagination**: Future enhancement for large result sets

### 8.2 Search Algorithm

Current implementation uses simple substring matching. Future enhancements:
- Fuzzy matching using `rapidfuzz` library
- Trigram similarity for typo tolerance
- Boost exact matches to top of results
- Consider Elasticsearch for large product catalogs

### 8.3 Mobile UX

- Search mode toggle should be touch-friendly (large tap targets)
- Results cards should be easily tappable on mobile
- Consider virtual keyboard behavior when switching modes

### 8.4 Edge Cases

- Empty Grocy product list: Show only local results
- Grocy API timeout: Proceed with local results, show warning
- Special characters in search: Sanitize for SQL injection prevention
- Very long product names: Truncate with ellipsis in results

---

## Navigation

- **Back to:** [README](README.md)
- **Related:** [UI Specification](07-ui-specification.md), [API Specification](06-api-specification.md), [User Stories](02-user-stories.md)
