"""Barcode validation and utilities."""

import re
from enum import Enum
from typing import NamedTuple

from app.core.exceptions import BarcodeValidationError


class BarcodeType(str, Enum):
    """Supported barcode types."""

    EAN_13 = "EAN-13"
    EAN_8 = "EAN-8"
    UPC_A = "UPC-A"
    UPC_E = "UPC-E"
    LOCATION = "LOCATION"
    UNKNOWN = "UNKNOWN"


class BarcodeInfo(NamedTuple):
    """Parsed barcode information."""

    barcode: str
    barcode_type: BarcodeType
    is_valid: bool
    normalized: str | None = None
    location_area: str | None = None
    location_number: str | None = None


# Location barcode pattern: LOC-{AREA}-{NUMBER}
LOCATION_PATTERN = re.compile(r"^LOC-([A-Z0-9]+)-(\d+)$", re.IGNORECASE)


def calculate_ean_checksum(digits: str) -> int:
    """Calculate EAN/UPC checksum digit.

    Uses the standard modulo 10 algorithm with weights 1 and 3.

    Args:
        digits: The barcode digits without the check digit

    Returns:
        int: The check digit (0-9)
    """
    total = 0
    for i, digit in enumerate(digits):
        weight = 1 if i % 2 == 0 else 3
        total += int(digit) * weight
    return (10 - (total % 10)) % 10


def validate_ean13(barcode: str) -> bool:
    """Validate an EAN-13 barcode.

    Args:
        barcode: 13-digit barcode string

    Returns:
        bool: True if valid EAN-13
    """
    if not barcode.isdigit() or len(barcode) != 13:
        return False

    expected_check = calculate_ean_checksum(barcode[:12])
    return int(barcode[12]) == expected_check


def validate_ean8(barcode: str) -> bool:
    """Validate an EAN-8 barcode.

    Args:
        barcode: 8-digit barcode string

    Returns:
        bool: True if valid EAN-8
    """
    if not barcode.isdigit() or len(barcode) != 8:
        return False

    expected_check = calculate_ean_checksum(barcode[:7])
    return int(barcode[7]) == expected_check


def validate_upca(barcode: str) -> bool:
    """Validate a UPC-A barcode.

    UPC-A is a 12-digit code, often represented as EAN-13 with leading zero.

    Args:
        barcode: 12-digit barcode string

    Returns:
        bool: True if valid UPC-A
    """
    if not barcode.isdigit() or len(barcode) != 12:
        return False

    expected_check = calculate_ean_checksum(barcode[:11])
    return int(barcode[11]) == expected_check


def validate_upce(barcode: str) -> bool:
    """Validate a UPC-E barcode.

    UPC-E is a compressed 8-digit version of UPC-A.

    Args:
        barcode: 8-digit barcode string

    Returns:
        bool: True if valid UPC-E (basic format check)
    """
    if not barcode.isdigit() or len(barcode) != 8:
        return False

    # UPC-E must start with 0 or 1
    if barcode[0] not in ("0", "1"):
        return False

    # Expand to UPC-A and validate
    expanded = expand_upce_to_upca(barcode)
    if expanded:
        return validate_upca(expanded)
    return False


def expand_upce_to_upca(upce: str) -> str | None:
    """Expand UPC-E to UPC-A format.

    Args:
        upce: 8-digit UPC-E barcode

    Returns:
        str: 12-digit UPC-A or None if invalid
    """
    if len(upce) != 8 or upce[0] not in ("0", "1"):
        return None

    number_system = upce[0]
    manufacturer_and_product = upce[1:7]
    check_digit = upce[7]
    last_digit = manufacturer_and_product[5]

    # Expansion rules based on last digit of manufacturer code
    if last_digit in ("0", "1", "2"):
        manufacturer = manufacturer_and_product[:2] + last_digit + "00"
        product = "00" + manufacturer_and_product[2:5]
    elif last_digit == "3":
        manufacturer = manufacturer_and_product[:3] + "00"
        product = "000" + manufacturer_and_product[3:5]
    elif last_digit == "4":
        manufacturer = manufacturer_and_product[:4] + "0"
        product = "0000" + manufacturer_and_product[4]
    else:
        manufacturer = manufacturer_and_product[:5]
        product = "0000" + last_digit

    return number_system + manufacturer + product + check_digit


def validate_location_barcode(barcode: str) -> tuple[bool, str | None, str | None]:
    """Validate a location barcode.

    Format: LOC-{AREA}-{NUMBER}
    Example: LOC-PANTRY-01, LOC-FRIDGE-03

    Args:
        barcode: Location barcode string

    Returns:
        tuple: (is_valid, area, number)
    """
    match = LOCATION_PATTERN.match(barcode)
    if match:
        return True, match.group(1).upper(), match.group(2)
    return False, None, None


def detect_barcode_type(barcode: str) -> BarcodeType:
    """Detect the type of a barcode.

    Args:
        barcode: Barcode string

    Returns:
        BarcodeType: Detected type
    """
    barcode = barcode.strip()

    # Check for location barcode first
    if barcode.upper().startswith("LOC-"):
        return BarcodeType.LOCATION

    # Check numeric barcodes
    if barcode.isdigit():
        length = len(barcode)
        if length == 13:
            return BarcodeType.EAN_13
        elif length == 8:
            # Could be EAN-8 or UPC-E
            if barcode[0] in ("0", "1"):
                return BarcodeType.UPC_E
            return BarcodeType.EAN_8
        elif length == 12:
            return BarcodeType.UPC_A

    return BarcodeType.UNKNOWN


def validate_barcode(barcode: str) -> BarcodeInfo:
    """Validate a barcode and return its information.

    Args:
        barcode: Barcode string to validate

    Returns:
        BarcodeInfo: Parsed barcode information
    """
    barcode = barcode.strip()
    barcode_type = detect_barcode_type(barcode)

    if barcode_type == BarcodeType.LOCATION:
        is_valid, area, number = validate_location_barcode(barcode)
        return BarcodeInfo(
            barcode=barcode.upper(),
            barcode_type=barcode_type,
            is_valid=is_valid,
            normalized=barcode.upper() if is_valid else None,
            location_area=area,
            location_number=number,
        )

    if barcode_type == BarcodeType.EAN_13:
        is_valid = validate_ean13(barcode)
        # Normalize: EAN-13 with leading zero could be UPC-A
        normalized = barcode if is_valid else None
        return BarcodeInfo(
            barcode=barcode,
            barcode_type=barcode_type,
            is_valid=is_valid,
            normalized=normalized,
        )

    if barcode_type == BarcodeType.EAN_8:
        is_valid = validate_ean8(barcode)
        return BarcodeInfo(
            barcode=barcode,
            barcode_type=barcode_type,
            is_valid=is_valid,
            normalized=barcode if is_valid else None,
        )

    if barcode_type == BarcodeType.UPC_A:
        is_valid = validate_upca(barcode)
        # Normalize to EAN-13 by adding leading zero
        normalized = "0" + barcode if is_valid else None
        return BarcodeInfo(
            barcode=barcode,
            barcode_type=barcode_type,
            is_valid=is_valid,
            normalized=normalized,
        )

    if barcode_type == BarcodeType.UPC_E:
        is_valid = validate_upce(barcode)
        # Normalize to EAN-13 via UPC-A expansion
        if is_valid:
            expanded = expand_upce_to_upca(barcode)
            normalized = "0" + expanded if expanded else None
        else:
            normalized = None
        return BarcodeInfo(
            barcode=barcode,
            barcode_type=barcode_type,
            is_valid=is_valid,
            normalized=normalized,
        )

    return BarcodeInfo(
        barcode=barcode,
        barcode_type=BarcodeType.UNKNOWN,
        is_valid=False,
    )


def validate_or_raise(barcode: str) -> BarcodeInfo:
    """Validate a barcode or raise an exception.

    Args:
        barcode: Barcode string to validate

    Returns:
        BarcodeInfo: Parsed barcode information

    Raises:
        BarcodeValidationError: If barcode is invalid
    """
    info = validate_barcode(barcode)
    if not info.is_valid:
        raise BarcodeValidationError(
            f"Invalid {info.barcode_type.value} barcode",
            barcode=barcode,
            barcode_type=info.barcode_type.value,
        )
    return info


def generate_location_code(area: str, number: int) -> str:
    """Generate a location barcode.

    Args:
        area: Location area (e.g., PANTRY, FRIDGE)
        number: Location number

    Returns:
        str: Location barcode string
    """
    area_clean = re.sub(r"[^A-Z0-9]", "", area.upper())
    return f"LOC-{area_clean}-{number:02d}"
