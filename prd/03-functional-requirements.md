# 3. Functional Requirements

## 3.1 Barcode Scanning

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-1** | Camera scanning | Use device camera via JavaScript barcode library (QuaggaJS/ZXing) |
| **FR-2** | USB/Bluetooth scanner | Capture keyboard input in kiosk mode (hidden input field always focused) |
| **FR-3** | Barcode validation | Validate UPC-A, UPC-E, EAN-13, EAN-8, Code128 formats |
| **FR-4** | Location barcode detection | Recognize `LOC-*` prefix pattern, set location context |
| **FR-5** | Scan feedback | Audio beep + visual confirmation on successful scan |

## 3.2 Product Lookup

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-6** | Multi-provider lookup | Support OpenFoodFacts, go-upc, UPCItemDB, Brave Search, Barcode Buddy Federation |
| **FR-7** | Configurable strategy | Sequential (priority order) or parallel (LLM judges winner) |
| **FR-8** | Provider priority UI | Drag-and-drop reordering in settings |
| **FR-9** | API key management | Secure storage for provider API keys (encrypted at rest) |
| **FR-10** | Brave Search fallback | Use Brave AI web search for unknown products as final fallback |
| **FR-11** | Image retrieval | Fetch product images via Brave Search API, store locally |

## 3.3 LLM Optimization

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-12** | Name cleaning | Transform messy names to proper case, expand abbreviations |
| **FR-13** | Category inference | Assign category based on product name/description |
| **FR-14** | Nutrition extraction | Parse nutrition info from description when available |
| **FR-15** | Unit standardization | Normalize units (oz, g, ml, L) to consistent format |
| **FR-16** | Data merging | LLM reconciles conflicting data from multiple providers |
| **FR-17** | Result caching | Cache optimized results in Redis (TTL: 30 days configurable) |
| **FR-18** | Async processing | LLM calls are non-blocking, queued on failure |
| **FR-19** | Provider presets | Easy configuration for OpenAI, Anthropic, Ollama, generic OpenAI-compatible |

## 3.4 Grocy Integration

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-20** | Product creation | Create new products in Grocy via API |
| **FR-21** | Stock entry creation | Add stock entries with quantity, location, best_before date |
| **FR-22** | Product matching | Fuzzy match by name (configurable threshold, default 90%) |
| **FR-23** | Multi-barcode support | Associate multiple barcodes with single Grocy product |
| **FR-24** | Image upload | Upload product images to Grocy |
| **FR-25** | Dual URL configuration | Separate API URL (internal) and Web URL (reverse proxy) |

## 3.5 Offline Support

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-26** | Local queue | Store pending scans in browser IndexedDB + server SQLite backup |
| **FR-27** | Connectivity detection | Monitor online/offline status |
| **FR-28** | Background sync | Process queue when connectivity restored |
| **FR-29** | Conflict resolution | Last-write-wins with user notification |

## 3.6 Multi-User Pre-Design

Although MVP is single-user, the architecture will support future multi-user expansion.

| ID | Requirement | Details |
|----|-------------|---------|
| **FR-30** | User table | `users` table with `id`, `email`, `password_hash`, `created_at` |
| **FR-31** | Session management | NiceGUI's server-side storage with unique identifier per user via browser session cookie |
| **FR-32** | Tenant isolation | All data tables include `user_id` foreign key for future filtering |
| **FR-33** | Per-user page instances | Use NiceGUI's `@ui.page` decorator ensuring each user sees their own instance |
| **FR-34** | Grocy config per user | Support multiple Grocy instances (one per user) in future |
| **FR-35** | Multi-tenant data model | Account key on root tables for future tenant isolation |

---

## Navigation

- **Previous:** [User Stories](02-user-stories.md)
- **Next:** [Technical Architecture](04-technical-architecture.md)
- **Back to:** [README](README.md)
