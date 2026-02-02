# 2. User Stories

## 2.1 Core Scanning

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-1** | user | scan a barcode with my phone camera | I can quickly add products | Camera opens, barcode detected within 2s, lookup initiated | P0 |
| **US-2** | user | use my USB barcode scanner in kiosk mode | I can rapidly scan multiple items without clicking | App captures barcode input without focus, processes immediately | P0 |
| **US-3** | user | have the system look up product details automatically | I don't have to type them | Lookup returns name, category, image within 5s | P0 |
| **US-4** | user | review product details before adding | I can verify accuracy | Review screen shows all fields, edit capability, confirm/cancel buttons | P0 |
| **US-5** | user | configure auto-add without review | I have faster workflow when confident | Setting toggles behavior, can be changed anytime | P1 |
| **US-6** | user | add exactly 1 unit per scan | inventory is accurate | Each scan creates one stock entry | P0 |

## 2.2 Product Lookup & Optimization

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-7** | user | the system to try multiple lookup services | obscure products are found | Configurable provider list, fallback chain or parallel mode | P0 |
| **US-8** | user | an LLM to clean up messy product names | my inventory looks professional | "CHOBANI YGRT STRWBRY" → "Chobani Strawberry Greek Yogurt" | P0 |
| **US-9** | user | the LLM to infer category if missing | products are organized | Category assigned based on product name/description | P0 |
| **US-10** | user | the LLM to standardize units | data is consistent | "5.3OZ" → "5.3 oz", grams/ml normalized | P0 |
| **US-11** | user | product images fetched and stored locally | I can visually identify items | Image downloaded, stored, uploaded to Grocy | P1 |
| **US-12** | user | lookup results cached | repeat scans are instant | Redis cache checked before external API calls | P0 |
| **US-13** | user | the LLM to judge winner when parallel lookup | best data is selected | LLM receives all responses, selects/merges best | P1 |
| **US-14** | user | Brave Search as final fallback for unknown products | nothing is unidentified | Brave AI search attempted when all other providers fail | P0 |

## 2.3 Location & Date Management

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-15** | user | scan a location barcode to set storage location | I know where products are | Location barcode (LOC-XXX) sets context for subsequent scans | P0 |
| **US-16** | user | generate custom location codes | I can label my storage areas | Format: `LOC-{AREA}-{NUMBER}`, e.g., `LOC-PANTRY-01` | P0 |
| **US-17** | user | print location labels via Brother QL | I have physical labels | Integration with brother_ql_web API | P2 |
| **US-18** | user | a touch-friendly date picker | I can enter expiration dates quickly | Large touch targets, swipe gestures, quick-select buttons | P0 |
| **US-19** | user | the date picker to remember last date for same product | I save time on batch entry | If same barcode scanned, pre-fill with last used date | P1 |
| **US-20** | user | each stock entry to track its own expiration | I can identify expiring items | New stock entry created per scan with best_before field | P0 |

## 2.4 Product Matching & Management

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-21** | user | fuzzy matching for existing products | slight variations still match | Configurable threshold (default 90%), auto-match above threshold | P0 |
| **US-22** | user | support multiple barcodes per product | product variants are handled | Barcode → Product is many-to-one relationship | P0 |
| **US-23** | user | prompted when confidence is below threshold | I make the final decision | List of candidates shown, user selects correct one | P0 |
| **US-24** | user | search products by name (non-barcode) | I can add items without scanning | Text search interface, results in AG Grid | P1 |
| **US-25** | user | create products without adding quantity | I can set up my catalog first | "Create product only" option on review screen | P1 |

## 2.5 Offline & Resilience

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-26** | user | scan products when offline | I'm not blocked by network issues | Scans queued locally in IndexedDB/SQLite | P0 |
| **US-27** | user | automatic sync when online | queued items are processed | Background sync on connectivity change | P0 |
| **US-28** | user | LLM failures to be non-blocking | I can keep scanning | Failed LLM calls queued for retry, raw data used | P0 |
| **US-29** | user | see a job queue UI | I know what's pending | Full queue view: status, retry button, cancel button | P0 |

## 2.6 Administration & Configuration

| ID | As a... | I want to... | So that... | Acceptance Criteria | Priority |
|----|---------|--------------|------------|---------------------|----------|
| **US-30** | admin | configure all settings via environment variables | deployment is consistent | Every setting has ENV_VAR equivalent | P0 |
| **US-31** | admin | configure lookup provider priority | I control the lookup flow | Drag-and-drop reorder in settings UI | P1 |
| **US-32** | admin | configure LLM endpoint easily | I use my preferred provider | Presets for OpenAI, Anthropic, Ollama + generic endpoint | P0 |
| **US-33** | admin | simple password authentication | the app isn't wide open | Local username/password, session-based | P0 |
| **US-34** | admin | view and search logs in the UI | I can debug issues | Log viewer with level filter, search, copy | P0 |
| **US-35** | admin | separate Grocy API URL from UI links | reverse proxy works correctly | `GROCY_API_URL` (internal) vs `GROCY_WEB_URL` (external) | P0 |

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| **P0** | Must have for MVP |
| **P1** | Should have, implement if time allows |
| **P2** | Nice to have, post-MVP |

---

## Navigation

- **Previous:** [Executive Summary](01-executive-summary.md)
- **Next:** [Functional Requirements](03-functional-requirements.md)
- **Back to:** [README](README.md)
