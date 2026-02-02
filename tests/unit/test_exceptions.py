"""Tests for custom exceptions."""

from app.core.exceptions import (
    AppException,
    BarcodeValidationError,
    NotFoundError,
    ValidationError,
)


def test_app_exception_to_dict() -> None:
    """Test AppException to_dict method."""
    exc = AppException("Test error", details={"key": "value"})
    result = exc.to_dict()

    assert result["error"] == "AppException"
    assert result["message"] == "Test error"
    assert result["details"] == {"key": "value"}


def test_not_found_error() -> None:
    """Test NotFoundError."""
    exc = NotFoundError("Product not found", details={"id": "123"})
    result = exc.to_dict()

    assert result["error"] == "NOT_FOUND"
    assert result["message"] == "Product not found"
    assert result["details"]["id"] == "123"


def test_validation_error() -> None:
    """Test ValidationError."""
    exc = ValidationError("Invalid input", details={"field": "name"})
    result = exc.to_dict()

    assert result["error"] == "VALIDATION_ERROR"
    assert result["message"] == "Invalid input"


def test_barcode_validation_error() -> None:
    """Test BarcodeValidationError."""
    exc = BarcodeValidationError(
        "Invalid barcode format",
        barcode="12345",
        barcode_type="EAN-13",
    )
    result = exc.to_dict()

    assert result["error"] == "BARCODE_VALIDATION_ERROR"
    assert result["details"]["barcode"] == "12345"
    assert result["details"]["expected_type"] == "EAN-13"
