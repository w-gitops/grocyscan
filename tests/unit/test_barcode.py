"""Tests for barcode validation."""

import pytest

from app.core.exceptions import BarcodeValidationError
from app.services.barcode import (
    BarcodeType,
    calculate_ean_checksum,
    detect_barcode_type,
    expand_upce_to_upca,
    generate_location_code,
    validate_barcode,
    validate_ean13,
    validate_ean8,
    validate_location_barcode,
    validate_or_raise,
    validate_upca,
    validate_upce,
)


class TestChecksumCalculation:
    """Tests for checksum calculation."""

    def test_ean13_checksum(self) -> None:
        """Test EAN-13 checksum calculation."""
        # Test with known barcode: 4006381333931
        assert calculate_ean_checksum("400638133393") == 1

    def test_upc_a_checksum(self) -> None:
        """Test UPC-A checksum calculation."""
        # Test with known barcode: 012345678905
        assert calculate_ean_checksum("01234567890") == 5


class TestEAN13Validation:
    """Tests for EAN-13 validation."""

    def test_valid_ean13(self) -> None:
        """Test valid EAN-13 barcodes."""
        assert validate_ean13("4006381333931") is True
        assert validate_ean13("5901234123457") is True
        assert validate_ean13("0012345678905") is True  # UPC-A as EAN-13

    def test_invalid_ean13_checksum(self) -> None:
        """Test EAN-13 with invalid checksum."""
        assert validate_ean13("4006381333932") is False

    def test_invalid_ean13_length(self) -> None:
        """Test EAN-13 with wrong length."""
        assert validate_ean13("400638133393") is False
        assert validate_ean13("40063813339310") is False

    def test_invalid_ean13_non_digit(self) -> None:
        """Test EAN-13 with non-digit characters."""
        assert validate_ean13("400638133393A") is False


class TestEAN8Validation:
    """Tests for EAN-8 validation."""

    def test_valid_ean8(self) -> None:
        """Test valid EAN-8 barcodes."""
        assert validate_ean8("96385074") is True

    def test_invalid_ean8_checksum(self) -> None:
        """Test EAN-8 with invalid checksum."""
        assert validate_ean8("96385075") is False

    def test_invalid_ean8_length(self) -> None:
        """Test EAN-8 with wrong length."""
        assert validate_ean8("9638507") is False


class TestUPCAValidation:
    """Tests for UPC-A validation."""

    def test_valid_upca(self) -> None:
        """Test valid UPC-A barcodes."""
        assert validate_upca("012345678905") is True
        assert validate_upca("042100005264") is True

    def test_invalid_upca_checksum(self) -> None:
        """Test UPC-A with invalid checksum."""
        assert validate_upca("012345678906") is False


class TestUPCEValidation:
    """Tests for UPC-E validation."""

    def test_valid_upce(self) -> None:
        """Test valid UPC-E barcodes."""
        # UPC-E: 04252614 expands to 042100005264
        assert validate_upce("04252614") is True

    def test_invalid_upce_start(self) -> None:
        """Test UPC-E not starting with 0 or 1."""
        assert validate_upce("24252614") is False


class TestUPCEExpansion:
    """Tests for UPC-E to UPC-A expansion."""

    def test_expand_type_0(self) -> None:
        """Test expansion with last digit 0."""
        result = expand_upce_to_upca("01234505")
        assert result is not None
        assert len(result) == 12

    def test_invalid_upce(self) -> None:
        """Test expansion with invalid UPC-E."""
        assert expand_upce_to_upca("1234567") is None
        assert expand_upce_to_upca("21234567") is None


class TestLocationBarcode:
    """Tests for location barcode validation."""

    def test_valid_location(self) -> None:
        """Test valid location barcodes."""
        is_valid, area, number = validate_location_barcode("LOC-PANTRY-01")
        assert is_valid is True
        assert area == "PANTRY"
        assert number == "01"

    def test_valid_location_lowercase(self) -> None:
        """Test location barcode with lowercase."""
        is_valid, area, number = validate_location_barcode("loc-fridge-03")
        assert is_valid is True
        assert area == "FRIDGE"
        assert number == "03"

    def test_invalid_location_format(self) -> None:
        """Test invalid location format."""
        is_valid, area, number = validate_location_barcode("PANTRY-01")
        assert is_valid is False
        assert area is None

    def test_invalid_location_missing_number(self) -> None:
        """Test location without number."""
        is_valid, _, _ = validate_location_barcode("LOC-PANTRY-")
        assert is_valid is False


class TestBarcodeTypeDetection:
    """Tests for barcode type detection."""

    def test_detect_ean13(self) -> None:
        """Test EAN-13 detection."""
        assert detect_barcode_type("4006381333931") == BarcodeType.EAN_13

    def test_detect_ean8(self) -> None:
        """Test EAN-8 detection."""
        assert detect_barcode_type("96385074") == BarcodeType.EAN_8

    def test_detect_upca(self) -> None:
        """Test UPC-A detection."""
        assert detect_barcode_type("012345678905") == BarcodeType.UPC_A

    def test_detect_upce(self) -> None:
        """Test UPC-E detection (starts with 0)."""
        assert detect_barcode_type("04252614") == BarcodeType.UPC_E

    def test_detect_location(self) -> None:
        """Test location barcode detection."""
        assert detect_barcode_type("LOC-PANTRY-01") == BarcodeType.LOCATION

    def test_detect_unknown(self) -> None:
        """Test unknown barcode type."""
        assert detect_barcode_type("ABC123") == BarcodeType.UNKNOWN


class TestValidateBarcode:
    """Tests for the main validate_barcode function."""

    def test_validate_valid_ean13(self) -> None:
        """Test validation of valid EAN-13."""
        info = validate_barcode("4006381333931")
        assert info.is_valid is True
        assert info.barcode_type == BarcodeType.EAN_13
        assert info.normalized == "4006381333931"

    def test_validate_valid_location(self) -> None:
        """Test validation of valid location."""
        info = validate_barcode("LOC-FREEZER-05")
        assert info.is_valid is True
        assert info.barcode_type == BarcodeType.LOCATION
        assert info.location_area == "FREEZER"
        assert info.location_number == "05"

    def test_validate_invalid_barcode(self) -> None:
        """Test validation of invalid barcode."""
        info = validate_barcode("invalid")
        assert info.is_valid is False
        assert info.barcode_type == BarcodeType.UNKNOWN


class TestValidateOrRaise:
    """Tests for validate_or_raise function."""

    def test_valid_barcode_returns_info(self) -> None:
        """Test that valid barcode returns info."""
        info = validate_or_raise("4006381333931")
        assert info.is_valid is True

    def test_invalid_barcode_raises(self) -> None:
        """Test that invalid barcode raises exception."""
        with pytest.raises(BarcodeValidationError) as exc_info:
            validate_or_raise("invalid")

        assert exc_info.value.error_code == "BARCODE_VALIDATION_ERROR"


class TestGenerateLocationCode:
    """Tests for location code generation."""

    def test_generate_location_code(self) -> None:
        """Test location code generation."""
        code = generate_location_code("Pantry", 1)
        assert code == "LOC-PANTRY-01"

    def test_generate_location_code_with_spaces(self) -> None:
        """Test location code with special characters."""
        code = generate_location_code("My Pantry!", 12)
        assert code == "LOC-MYPANTRY-12"
