"""Tests for database models."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Barcode,
    Job,
    Location,
    LookupCache,
    Product,
    ScanHistory,
    Setting,
    StockEntry,
    User,
)


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test creating a user."""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        display_name="Test User",
    )
    db_session.add(user)
    await db_session.flush()

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_admin is False


@pytest.mark.asyncio
async def test_create_product_with_barcode(db_session: AsyncSession) -> None:
    """Test creating a product with a barcode."""
    # Create user first
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    # Create product
    product = Product(
        user_id=user.id,
        name="Test Product",
        name_normalized="test product",
        category="Groceries",
    )
    db_session.add(product)
    await db_session.flush()

    # Create barcode
    barcode = Barcode(
        user_id=user.id,
        product_id=product.id,
        barcode="1234567890123",
        barcode_type="EAN-13",
        is_primary=True,
    )
    db_session.add(barcode)
    await db_session.flush()

    assert product.id is not None
    assert barcode.product_id == product.id


@pytest.mark.asyncio
async def test_create_location(db_session: AsyncSession) -> None:
    """Test creating a location."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    location = Location(
        user_id=user.id,
        code="LOC-PANTRY-01",
        name="Pantry Shelf 1",
        is_freezer=False,
    )
    db_session.add(location)
    await db_session.flush()

    assert location.id is not None
    assert location.code == "LOC-PANTRY-01"


@pytest.mark.asyncio
async def test_create_stock_entry(db_session: AsyncSession) -> None:
    """Test creating a stock entry."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    product = Product(user_id=user.id, name="Test Product")
    db_session.add(product)
    await db_session.flush()

    location = Location(user_id=user.id, code="LOC-01", name="Pantry")
    db_session.add(location)
    await db_session.flush()

    stock = StockEntry(
        user_id=user.id,
        product_id=product.id,
        location_id=location.id,
        quantity=5,
        best_before=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(stock)
    await db_session.flush()

    assert stock.id is not None
    assert stock.quantity == 5


@pytest.mark.asyncio
async def test_create_lookup_cache(db_session: AsyncSession) -> None:
    """Test creating a lookup cache entry."""
    cache = LookupCache(
        barcode="1234567890123",
        provider="openfoodfacts",
        response_json={"product": {"name": "Test"}},
        lookup_success=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(cache)
    await db_session.flush()

    assert cache.id is not None
    assert cache.barcode == "1234567890123"


@pytest.mark.asyncio
async def test_create_job(db_session: AsyncSession) -> None:
    """Test creating a job."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    job = Job(
        user_id=user.id,
        job_type="llm_optimize",
        status="pending",
        payload_json={"product_id": str(uuid.uuid4())},
    )
    db_session.add(job)
    await db_session.flush()

    assert job.id is not None
    assert job.status == "pending"
    assert job.attempts == 0


@pytest.mark.asyncio
async def test_create_scan_history(db_session: AsyncSession) -> None:
    """Test creating a scan history entry."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    scan = ScanHistory(
        user_id=user.id,
        barcode="1234567890123",
        action="added",
        input_method="scanner",
        lookup_provider="openfoodfacts",
        lookup_duration_ms=250,
    )
    db_session.add(scan)
    await db_session.flush()

    assert scan.id is not None
    assert scan.action == "added"


@pytest.mark.asyncio
async def test_create_setting(db_session: AsyncSession) -> None:
    """Test creating a setting."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    setting = Setting(
        user_id=user.id,
        key="auto_add_enabled",
        value_json={"value": True},
    )
    db_session.add(setting)
    await db_session.flush()

    assert setting.id is not None
    assert setting.key == "auto_add_enabled"


@pytest.mark.asyncio
async def test_user_product_relationship(db_session: AsyncSession) -> None:
    """Test user-product relationship."""
    user = User(email="test@example.com", password_hash="hash")
    db_session.add(user)
    await db_session.flush()

    product1 = Product(user_id=user.id, name="Product 1")
    product2 = Product(user_id=user.id, name="Product 2")
    db_session.add_all([product1, product2])
    await db_session.flush()

    # Refresh user to load relationships
    await db_session.refresh(user)

    assert len(user.products) == 2
