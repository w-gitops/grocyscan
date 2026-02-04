# Grocy Custom Fields (Userfields) for GrocyScan

GrocyScan can store **Brand** (and optionally other custom data) in Grocy using [userfields](https://demo.grocy.info/userfields). Grocy’s product table has built-in **name** and **description**; custom fields like Brand are added as userfields.

## Add a “Brand” userfield for products

1. In Grocy, go to **Settings** (gear icon) → **Userfields**.
2. Click **Add** (or “Create userfield”).
3. Set:
   - **Entity**: `products`
   - **Name**: `Brand` (exact name; GrocyScan sends `userfields.Brand`).
   - **Caption**: e.g. `Brand`
   - **Type**: `Text (single line)` (or `Text (multi line)` if you prefer).
4. Save.

After this, when you add products via GrocyScan with **Use AI to clean title, description and brand** enabled and a brand is detected or entered, GrocyScan will:

- Put a **clean title** and **description** (and brand line in description) into Grocy’s normal fields.
- Send **Brand** in the product create/update request so it appears in the Brand userfield, if your Grocy version supports userfields on the products API.

If Grocy’s API does not accept userfields on product create (some versions/instances), GrocyScan still writes brand into the product **description** as `Brand: …`, so the information is never lost.

## LLM enhancement

With **Use AI to clean title, description and brand** enabled in the review popup, GrocyScan uses the configured LLM to:

- **Title**: Clean, standard product name (Title Case, brand at start when relevant, size/quantity kept).
- **Description**: Short 1–2 sentence product description for Grocy.
- **Brand**: Extracted or normalized brand name (and stored in userfield and/or description as above).
- **Category**: Inferred category (Dairy, Produce, Beverages, etc.) for internal use.

Configure the LLM under **Settings → LLM** (API key and model). If the LLM is not configured or the checkbox is off, the raw name/description/brand from the form are used as-is.
