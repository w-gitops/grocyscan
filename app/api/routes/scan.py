"""Barcode scanning endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.logging import get_logger
from app.schemas.scan import (
    ProductInfo,
    ScanByProductRequest,
    ScanByProductResponse,
    ScanConfirmRequest,
    ScanConfirmResponse,
    ScanRequest,
    ScanResponse,
)
from app.core.exceptions import GrocyError
from app.services.barcode import BarcodeType, validate_barcode
from app.services.grocy import grocy_client
from app.services.llm import optimize_product_name
from app.services.llm.client import llm_client
from app.services.lookup import lookup_manager

logger = get_logger(__name__)

router = APIRouter()

# In-memory scan session storage (should be Redis in production)
_scan_sessions: dict[str, dict] = {}


@router.post("", response_model=ScanResponse)
async def scan_barcode(request: Request, scan_request: ScanRequest) -> ScanResponse:
    """Process a barcode scan.

    Validates the barcode, looks up product information, and returns
    a scan session that can be confirmed.

    Args:
        request: FastAPI request
        scan_request: Scan request with barcode

    Returns:
        ScanResponse: Scan result with product info
    """
    # Validate barcode
    barcode_info = validate_barcode(scan_request.barcode)

    scan_id = uuid.uuid4()

    # Handle location barcodes
    if barcode_info.barcode_type == BarcodeType.LOCATION:
        logger.info(
            "Location barcode scanned",
            barcode=scan_request.barcode,
            area=barcode_info.location_area,
            number=barcode_info.location_number,
        )
        return ScanResponse(
            scan_id=scan_id,
            barcode=scan_request.barcode,
            barcode_type=barcode_info.barcode_type.value,
            found=barcode_info.is_valid,
            location_code=barcode_info.normalized,
        )

    # Handle product barcodes
    if not barcode_info.is_valid:
        logger.warning("Invalid barcode scanned", barcode=scan_request.barcode)
        return ScanResponse(
            scan_id=scan_id,
            barcode=scan_request.barcode,
            barcode_type=barcode_info.barcode_type.value,
            found=False,
        )

    # Use normalized barcode for lookup
    lookup_barcode = barcode_info.normalized or scan_request.barcode

    # Check if product exists in Grocy
    existing_in_grocy = False
    grocy_product = None
    try:
        grocy_product = await grocy_client.get_product_by_barcode(lookup_barcode)
        if grocy_product:
            existing_in_grocy = True
            logger.info(
                "Product found in Grocy",
                barcode=lookup_barcode,
                product_id=grocy_product.get("id"),
            )
    except Exception as e:
        logger.warning("Grocy lookup failed", barcode=lookup_barcode, error=str(e))

    # Look up product information
    lookup_result = await lookup_manager.lookup(lookup_barcode, skip_cache=scan_request.skip_cache)

    # Build product info
    product = None
    if lookup_result.found or grocy_product:
        product = ProductInfo(
            name=grocy_product.get("name") if grocy_product else lookup_result.name,
            brand=lookup_result.brand,
            description=lookup_result.description,
            category=lookup_result.category,
            image_url=lookup_result.image_url,
            quantity=lookup_result.quantity,
            quantity_unit=lookup_result.quantity_unit,
            nutrition=lookup_result.nutrition,
            grocy_product_id=grocy_product.get("id") if grocy_product else None,
            is_new=not existing_in_grocy,
        )

    # Store scan session
    _scan_sessions[str(scan_id)] = {
        "barcode": lookup_barcode,
        "barcode_type": barcode_info.barcode_type.value,
        "product": product.model_dump() if product else None,
        "lookup_result": lookup_result.model_dump() if lookup_result.found else None,
        "grocy_product": grocy_product,
        "location_code": scan_request.location_code,
        "input_method": scan_request.input_method,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Barcode scanned",
        barcode=lookup_barcode,
        found=lookup_result.found or existing_in_grocy,
        provider=lookup_result.provider,
        lookup_time_ms=lookup_result.lookup_time_ms,
    )

    return ScanResponse(
        scan_id=scan_id,
        barcode=lookup_barcode,
        barcode_type=barcode_info.barcode_type.value,
        found=lookup_result.found or existing_in_grocy,
        product=product,
        location_code=scan_request.location_code,
        lookup_provider=lookup_result.provider if lookup_result.found else None,
        lookup_time_ms=lookup_result.lookup_time_ms,
        existing_in_grocy=existing_in_grocy,
    )


@router.post("/by-product", response_model=ScanByProductResponse)
async def scan_by_product(
    request: ScanByProductRequest,
) -> ScanByProductResponse:
    """Create a scan session from a product selected by name search.

    Used when the user adds inventory via product name search instead of barcode.
    Returns a scan_id that can be used with the confirm endpoint.
    """
    scan_id = uuid.uuid4()
    grocy_product = None
    if request.grocy_product_id:
        grocy_product = await grocy_client.get_product(request.grocy_product_id)
        if not grocy_product:
            grocy_product = {"id": request.grocy_product_id}

    product_info = ProductInfo(
        name=request.name,
        category=request.category,
        image_url=request.image_url,
        grocy_product_id=request.grocy_product_id,
        is_new=request.grocy_product_id is None,
    )

    _scan_sessions[str(scan_id)] = {
        "barcode": None,
        "barcode_type": "PRODUCT",
        "product": product_info.model_dump(),
        "lookup_result": None,
        "grocy_product": grocy_product,
        "location_code": request.location_code,
        "input_method": "name_search",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Scan session created from product search",
        name=request.name,
        grocy_product_id=request.grocy_product_id,
    )

    return ScanByProductResponse(
        scan_id=scan_id,
        name=request.name,
        category=request.category,
        image_url=request.image_url,
        location_code=request.location_code,
        existing_in_grocy=request.grocy_product_id is not None,
    )


@router.post("/{scan_id}/confirm", response_model=ScanConfirmResponse)
async def confirm_scan(scan_id: str, confirm: ScanConfirmRequest) -> ScanConfirmResponse:
    """Confirm and add scanned product to inventory.

    Creates the product in Grocy if needed, then adds stock.

    Args:
        scan_id: The scan session ID
        confirm: Confirmation request with product details

    Returns:
        ScanConfirmResponse: Result of the confirmation
    """
    # Get scan session
    session = _scan_sessions.get(scan_id)
    if not session:
        return ScanConfirmResponse(
            success=False,
            message="Scan session not found or expired",
        )

    barcode = session["barcode"]
    grocy_product = session.get("grocy_product")

    grocy_product_id = None
    grocy_stock_id = None

    # Resolve final name, description, brand (LLM enhancement if enabled)
    name_for_grocy = confirm.name
    description_for_grocy = confirm.description or confirm.category or ""
    brand_for_grocy = (confirm.brand or "").strip() or None
    if not brand_for_grocy and session.get("product"):
        brand_for_grocy = (session["product"].get("brand") or "").strip() or None

    if confirm.create_in_grocy and confirm.use_llm_enhancement:
        try:
            if await llm_client.is_available():
                lookup_desc = (session.get("product") or {}).get("description") or ""
                optimized = await optimize_product_name(
                    name=confirm.name,
                    brand=confirm.brand or (session.get("product") or {}).get("brand"),
                    description=confirm.description or lookup_desc,
                    raw_data={"category": confirm.category},
                )
                name_for_grocy = optimized.get("name") or name_for_grocy
                description_for_grocy = (optimized.get("description") or "").strip() or description_for_grocy
                if (optimized.get("brand") or "").strip():
                    brand_for_grocy = (optimized.get("brand") or "").strip()
                if (optimized.get("category") or "").strip() and not description_for_grocy:
                    description_for_grocy = optimized.get("category", "")
        except Exception as e:
            logger.warning("LLM enhancement skipped", error=str(e))

    # Build Grocy description: include brand line if we have brand (in case userfield not supported)
    if brand_for_grocy and description_for_grocy and "Brand:" not in description_for_grocy:
        description_for_grocy = f"Brand: {brand_for_grocy}\n\n{description_for_grocy}"
    elif brand_for_grocy and not description_for_grocy:
        description_for_grocy = f"Brand: {brand_for_grocy}"

    try:
        if confirm.create_in_grocy:
            # Create or get product in Grocy
            if grocy_product:
                grocy_product_id = grocy_product.get("id")
            else:
                # Create new product (optional Brand userfield if Grocy has it)
                userfields = {"Brand": brand_for_grocy} if brand_for_grocy else None
                try:
                    created = await grocy_client.create_product(
                        name=name_for_grocy,
                        description=description_for_grocy,
                        userfields=userfields,
                    )
                except GrocyError as e:
                    # Some Grocy versions reject userfields in POST; retry without
                    if userfields and "userfield" in str(e).lower():
                        logger.warning("Grocy rejected userfields, creating product without Brand userfield")
                        created = await grocy_client.create_product(
                            name=name_for_grocy,
                            description=description_for_grocy,
                        )
                    else:
                        raise
                grocy_product_id = created.get("created_object_id") or created.get("id")

                # Add barcode to product (only if we have a barcode, e.g. not from name search)
                if grocy_product_id and barcode:
                    await grocy_client.add_barcode_to_product(grocy_product_id, barcode)

            # Add stock
            if grocy_product_id:
                best_before_str = None
                if confirm.best_before:
                    best_before_str = confirm.best_before.strftime("%Y-%m-%d")

                stock_result = await grocy_client.add_to_stock(
                    product_id=grocy_product_id,
                    amount=confirm.quantity,
                    best_before_date=best_before_str,
                    price=confirm.price,
                )
                # Grocy returns list of stock entries
                if isinstance(stock_result, list) and stock_result:
                    grocy_stock_id = stock_result[0].get("stock_id")

        # Clean up session
        del _scan_sessions[scan_id]

        logger.info(
            "Scan confirmed",
            barcode=barcode,
            grocy_product_id=grocy_product_id,
            quantity=confirm.quantity,
        )

        return ScanConfirmResponse(
            success=True,
            grocy_product_id=grocy_product_id,
            grocy_stock_id=grocy_stock_id,
            message="Product added to inventory",
        )

    except Exception as e:
        logger.error("Failed to confirm scan", barcode=barcode, error=str(e))
        return ScanConfirmResponse(
            success=False,
            message=f"Failed to add product: {e}",
        )


@router.delete("/{scan_id}")
async def cancel_scan(scan_id: str) -> dict[str, str]:
    """Cancel a pending scan session.

    Args:
        scan_id: The scan session ID

    Returns:
        dict: Cancellation confirmation
    """
    if scan_id in _scan_sessions:
        del _scan_sessions[scan_id]
        return {"status": "cancelled"}
    return {"status": "not_found"}
