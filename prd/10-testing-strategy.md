# 10. Testing Strategy

## 10.1 Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_barcode_validator.py
│   ├── test_lookup_providers/
│   │   ├── test_openfoodfacts.py
│   │   ├── test_goupc.py
│   │   ├── test_upcitemdb.py
│   │   └── test_brave.py
│   ├── test_llm_optimizer.py
│   ├── test_grocy_client.py
│   └── test_fuzzy_matching.py
├── integration/
│   ├── test_scan_flow.py
│   ├── test_api_endpoints.py
│   ├── test_grocy_integration.py
│   └── test_job_queue.py
└── database/
    ├── test_migrations.py
    └── test_crud_operations.py
```

## 10.2 Test Fixtures

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db


TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/grocyscan_test"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_barcode():
    return "012345678901"


@pytest.fixture
def sample_product():
    return {
        "name": "Test Product",
        "category": "Test Category",
        "barcode": "012345678901",
    }
```

## 10.3 Unit Test Examples

### Barcode Validator Tests

```python
# tests/unit/test_barcode_validator.py
import pytest
from app.services.barcode_validator import BarcodeValidator


class TestBarcodeValidator:
    def test_valid_upc_a(self):
        assert BarcodeValidator.validate("012345678901") == True
        assert BarcodeValidator.get_type("012345678901") == "UPC-A"
    
    def test_valid_ean_13(self):
        assert BarcodeValidator.validate("4006381333931") == True
        assert BarcodeValidator.get_type("4006381333931") == "EAN-13"
    
    def test_invalid_barcode(self):
        assert BarcodeValidator.validate("invalid") == False
    
    def test_location_barcode(self):
        assert BarcodeValidator.is_location_barcode("LOC-PANTRY-01") == True
        assert BarcodeValidator.is_location_barcode("012345678901") == False
```

### Lookup Provider Tests

```python
# tests/unit/test_lookup_providers/test_openfoodfacts.py
import pytest
from app.services.lookup.openfoodfacts import OpenFoodFactsProvider


class TestOpenFoodFactsProvider:
    @pytest.fixture
    def provider(self):
        return OpenFoodFactsProvider()
    
    @pytest.mark.asyncio
    async def test_lookup_found_product(self, provider, httpx_mock):
        httpx_mock.add_response(json={
            "status": 1,
            "product": {"product_name": "Nutella", "brands": "Ferrero"}
        })
        
        result = await provider.lookup("3017620422003")
        
        assert result.found == True
        assert result.product_name == "Nutella"
    
    @pytest.mark.asyncio
    async def test_lookup_not_found(self, provider, httpx_mock):
        httpx_mock.add_response(json={"status": 0})
        
        result = await provider.lookup("0000000000000")
        
        assert result.found == False
```

## 10.4 Integration Test Examples

```python
# tests/integration/test_scan_flow.py
import pytest
from fastapi.testclient import TestClient


class TestScanFlow:
    @pytest.mark.asyncio
    async def test_scan_known_barcode(self, client, db_session):
        response = client.post("/api/scan", json={
            "barcode": "012345678901",
            "input_method": "scanner",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["found", "pending_review", "added"]
    
    def test_scan_location_barcode_sets_context(self, client):
        response = client.post("/api/scan", json={
            "barcode": "LOC-FRIDGE-01",
            "input_method": "scanner"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "location_set"
```

## 10.5 Database Test Examples

```python
# tests/database/test_crud_operations.py
import pytest
from uuid import uuid4
from app.db.crud import products


class TestProductCRUD:
    def test_create_product(self, db_session):
        product = products.create(
            db_session,
            name="Test Product",
            category="Test Category",
            user_id=uuid4()
        )
        
        assert product.id is not None
        assert product.name == "Test Product"
    
    def test_fuzzy_search_products(self, db_session):
        user_id = uuid4()
        products.create(db_session, name="Chobani Greek Yogurt", user_id=user_id)
        products.create(db_session, name="Fage Greek Yogurt", user_id=user_id)
        
        results = products.fuzzy_search(
            db_session,
            query="greek yogurt",
            user_id=user_id,
            threshold=0.5
        )
        
        assert len(results) == 2
```

## 10.6 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_barcode_validator.py

# Run tests matching pattern
pytest -k "test_lookup"

# Run with verbose output
pytest -v

# Run async tests
pytest -m asyncio
```

---

## Navigation

- **Previous:** [Installation & Operations](09-installation-operations.md)
- **Next:** [Schema Evolution](11-schema-evolution.md)
- **Back to:** [README](README.md)
