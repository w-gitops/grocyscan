"""Barcode scanning endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.core.logging import get_logger
from app.schemas.scan import (
    ProductInfo,
    ScanConfirmRequest,
    ScanConfirmResponse,
    ScanRequest,
    ScanResponse,
)
from app.services.barcode import BarcodeType, validate_barcode
from app.services.grocy import grocy_client
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
    lookup_result = await lookup_manager.lookup(lookup_barcode)

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

    try:
        if confirm.create_in_grocy:
            # Create or get product in Grocy
            if grocy_product:
                grocy_product_id = grocy_product.get("id")
            else:
                # Create new product
                created = await grocy_client.create_product(
                    name=confirm.name,
                    description=confirm.category,  # Use category as description for now
                )
                grocy_product_id = created.get("created_object_id") or created.get("id")

                # Add barcode to product
                if grocy_product_id:
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
