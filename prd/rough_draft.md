# GrocyScan - Product Requirements Document

## Overview

GrocyScan is a Python CLI application that bridges barcode scanning with Grocy inventory management. Users can scan grocery barcodes to look up product information and automatically add items to their Grocy inventory.

## Problem Statement

Manually entering grocery items into Grocy is tedious. Users want to quickly scan barcodes and have products automatically identified and added to their inventory.

## Target Users

- Grocy users who want faster inventory management
- Home users tracking groceries
- Small businesses managing stock

## Core Features

### 1. Barcode Lookup
- Scan/enter a barcode
- Query Open Food Facts API for product information
- Display product name, brand, quantity, etc.

### 2. Grocy Integration
- Connect to user's Grocy instance via API
- Search for existing products
- Create new products if not found
- Add items to inventory with quantity

### 3. Configuration
- Store Grocy URL and API key securely
- Remember user preferences
- Support multiple Grocy instances

## Technical Requirements

- Python 3.12+
- CLI interface (typer or click)
- Async HTTP client (httpx)
- Data validation (pydantic)
- Configuration management (python-dotenv or dynaconf)

## API Integrations

### Open Food Facts
- Endpoint: `https://world.openfoodfacts.org/api/v0/product/{barcode}.json`
- Free, no authentication required
- Returns product name, brand, images, nutrition info

### Grocy API
- Base URL: User's Grocy instance
- Authentication: API key in header
- Key endpoints:
  - `GET /api/stock` - Current inventory
  - `POST /api/stock/products/{id}/add` - Add to inventory
  - `GET /api/objects/products` - List products
  - `POST /api/objects/products` - Create product

## Success Metrics

- Successfully lookup 90%+ of common grocery barcodes
- Add item to Grocy in under 5 seconds
- Zero manual data entry for known products

## Future Considerations

- Mobile app with camera scanning
- Batch scanning mode
- Shopping list integration
- Receipt OCR scanning
