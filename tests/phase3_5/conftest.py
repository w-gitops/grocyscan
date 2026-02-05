"""Phase 3.5 test fixtures."""

import pytest


@pytest.fixture
def sample_quantity_unit():
    """Sample quantity unit data."""
    return {
        "name": "Piece",
        "name_plural": "Pieces",
        "description": "Individual items",
    }


@pytest.fixture
def sample_product_group():
    """Sample product group data."""
    return {
        "name": "Dairy",
        "description": "Milk and dairy products",
    }
