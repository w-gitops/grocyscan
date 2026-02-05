"""Phase 3.5 Stock Operations API Tests."""

import pytest


class TestStockInventory:
    """Test inventory correction operation."""

    def test_inventory_correction_request_schema(self):
        """StockInventoryRequest schema accepts required fields."""
        from app.schemas.v2.stock import StockInventoryRequest
        from decimal import Decimal
        import uuid

        req = StockInventoryRequest(
            product_id=uuid.uuid4(),
            new_amount=Decimal("5.5"),
        )
        assert req.new_amount == Decimal("5.5")
        assert req.location_id is None
        assert req.best_before_date is None

    def test_inventory_correction_with_location(self):
        """StockInventoryRequest accepts optional location_id."""
        from app.schemas.v2.stock import StockInventoryRequest
        from decimal import Decimal
        import uuid

        loc_id = uuid.uuid4()
        req = StockInventoryRequest(
            product_id=uuid.uuid4(),
            new_amount=Decimal("10"),
            location_id=loc_id,
        )
        assert req.location_id == loc_id


class TestStockOpen:
    """Test open product operation."""

    def test_open_request_schema(self):
        """StockOpenRequest schema accepts stock_entry_id."""
        from app.schemas.v2.stock import StockOpenRequest
        import uuid

        entry_id = uuid.uuid4()
        req = StockOpenRequest(stock_entry_id=entry_id)
        assert req.stock_entry_id == entry_id
        assert req.amount is None


class TestStockEntryEdit:
    """Test edit stock entry operation."""

    def test_edit_request_schema(self):
        """StockEntryEditRequest schema accepts partial updates."""
        from app.schemas.v2.stock import StockEntryEditRequest
        from decimal import Decimal

        req = StockEntryEditRequest(
            amount=Decimal("3.5"),
            note="Test note",
        )
        assert req.amount == Decimal("3.5")
        assert req.note == "Test note"
        assert req.location_id is None
        assert req.price is None
        assert req.open is None


class TestStockResponse:
    """Test enhanced stock response."""

    def test_stock_response_includes_phase35_fields(self):
        """StockResponse includes Phase 3.5 fields."""
        from app.schemas.v2.stock import StockResponse
        from decimal import Decimal
        import uuid
        from datetime import datetime, date

        resp = StockResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            location_id=None,
            quantity=Decimal("2.5"),
            expiration_date=date(2026, 6, 1),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            stock_id="test-stock-id-123",
            purchased_date=date(2026, 1, 15),
            price=Decimal("9.99"),
            open=True,
            opened_date=date(2026, 2, 1),
            note="Test stock entry",
        )
        assert resp.stock_id == "test-stock-id-123"
        assert resp.price == Decimal("9.99")
        assert resp.open is True
        assert resp.note == "Test stock entry"


class TestStockTransactionResponse:
    """Test enhanced transaction response."""

    def test_transaction_response_includes_phase35_fields(self):
        """StockTransactionResponse includes Phase 3.5 fields."""
        from app.schemas.v2.stock import StockTransactionResponse
        from decimal import Decimal
        import uuid
        from datetime import datetime

        resp = StockTransactionResponse(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            stock_id=uuid.uuid4(),
            product_id=uuid.uuid4(),
            transaction_type="inventory-correction",
            quantity=Decimal("5"),
            from_location_id=None,
            to_location_id=uuid.uuid4(),
            notes="Inventory audit",
            spoiled=False,
            correlation_id=uuid.uuid4(),
            undone=False,
            created_at=datetime.now(),
        )
        assert resp.transaction_type == "inventory-correction"
        assert resp.spoiled is False
        assert resp.undone is False
        assert resp.correlation_id is not None
