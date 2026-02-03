"""Settings service for persistent configuration storage."""

import json
from typing import Any

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

from app.config import settings as app_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# Default settings structure
class LLMSettings(BaseModel):
    """LLM configuration settings."""
    
    provider_preset: str = "ollama"
    api_url: str = "http://localhost:11434/v1"
    api_key: str = ""  # Encrypted when stored
    model: str = "llama3.1:8b"


class LookupSettings(BaseModel):
    """Lookup provider settings."""
    
    strategy: str = "sequential"
    provider_order: list[str] = Field(
        default_factory=lambda: ["openfoodfacts", "goupc", "upcitemdb", "brave"],
        description="Order for barcode/UPC lookup (first match wins in sequential).",
    )
    name_search_provider_order: list[str] = Field(
        default_factory=lambda: ["brave", "openfoodfacts"],
        description="Order for search-by-name (Brave preferred; results merged in this order).",
    )
    timeout_seconds: int = 10
    
    # Provider-specific settings
    openfoodfacts_enabled: bool = True
    
    goupc_enabled: bool = False
    goupc_api_key: str = ""  # Encrypted when stored
    
    upcitemdb_enabled: bool = False
    upcitemdb_api_key: str = ""  # Encrypted when stored
    
    brave_enabled: bool = False
    brave_api_key: str = ""  # Encrypted when stored
    brave_use_as_fallback: bool = True


class GrocySettings(BaseModel):
    """Grocy connection settings."""
    
    api_url: str = "http://localhost:9283"
    api_key: str = ""  # Encrypted when stored
    web_url: str = "http://localhost:9283"
    timeout_seconds: int = 30


class ScanningSettings(BaseModel):
    """Scanning behavior settings."""
    
    auto_add_enabled: bool = False
    kiosk_mode_enabled: bool = False
    fuzzy_match_threshold: float = 0.9
    default_quantity_unit: str = "pieces"


class UISettings(BaseModel):
    """UI preference settings."""
    
    theme: str = "auto"  # "light", "dark", "auto"
    compact_mode: bool = False


class AllSettings(BaseModel):
    """All application settings."""
    
    llm: LLMSettings = Field(default_factory=LLMSettings)
    lookup: LookupSettings = Field(default_factory=LookupSettings)
    grocy: GrocySettings = Field(default_factory=GrocySettings)
    scanning: ScanningSettings = Field(default_factory=ScanningSettings)
    ui: UISettings = Field(default_factory=UISettings)


class SettingsService:
    """Service for managing persistent settings.
    
    Settings are stored in a JSON file for the MVP.
    In production, this would use the database Setting model.
    """
    
    SETTINGS_FILE = "data/settings.json"
    SENSITIVE_KEYS = {"api_key", "goupc_api_key", "upcitemdb_api_key", "brave_api_key"}
    
    def __init__(self) -> None:
        self._settings: AllSettings | None = None
        self._fernet: Fernet | None = None
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """Initialize encryption for sensitive values."""
        try:
            # Use app secret key as base for encryption key
            secret = app_settings.grocyscan_secret_key.get_secret_value()
            # Derive a valid Fernet key from the secret (must be 32 url-safe base64 bytes)
            import base64
            import hashlib
            key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
            self._fernet = Fernet(key)
        except Exception as e:
            logger.warning("Failed to initialize encryption, sensitive data will not be encrypted", error=str(e))
            self._fernet = None
    
    def _encrypt(self, value: str) -> str:
        """Encrypt a sensitive value."""
        if not value or not self._fernet:
            return value
        try:
            return self._fernet.encrypt(value.encode()).decode()
        except Exception:
            return value
    
    def _decrypt(self, value: str) -> str:
        """Decrypt a sensitive value."""
        if not value or not self._fernet:
            return value
        try:
            return self._fernet.decrypt(value.encode()).decode()
        except Exception:
            # Return as-is if decryption fails (might be unencrypted)
            return value
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        import os
        os.makedirs("data", exist_ok=True)
    
    def load(self) -> AllSettings:
        """Load settings from storage."""
        if self._settings is not None:
            return self._settings
        
        try:
            import os
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                
                # Decrypt sensitive values
                self._decrypt_settings(data)
                
                self._settings = AllSettings.model_validate(data)
                logger.info("Settings loaded from file")
            else:
                # Initialize with defaults from app config
                self._settings = self._get_defaults_from_config()
                logger.info("Using default settings")
        except Exception as e:
            logger.error("Failed to load settings, using defaults", error=str(e))
            self._settings = AllSettings()
        
        return self._settings
    
    def _get_defaults_from_config(self) -> AllSettings:
        """Get default settings from app config."""
        return AllSettings(
            llm=LLMSettings(
                provider_preset=app_settings.llm_provider_preset,
                api_url=app_settings.llm_api_url,
                api_key=app_settings.llm_api_key.get_secret_value() if app_settings.llm_api_key else "",
                model=app_settings.llm_model,
            ),
            lookup=LookupSettings(
                strategy=app_settings.lookup_strategy,
                provider_order=app_settings.provider_list,
                timeout_seconds=app_settings.lookup_timeout_seconds,
                openfoodfacts_enabled=app_settings.openfoodfacts_enabled,
                goupc_enabled=app_settings.goupc_enabled,
                goupc_api_key=app_settings.goupc_api_key.get_secret_value() if app_settings.goupc_api_key else "",
                upcitemdb_enabled=app_settings.upcitemdb_enabled,
                upcitemdb_api_key=app_settings.upcitemdb_api_key.get_secret_value() if app_settings.upcitemdb_api_key else "",
                brave_enabled=app_settings.brave_enabled,
                brave_api_key=app_settings.brave_api_key.get_secret_value() if app_settings.brave_api_key else "",
                brave_use_as_fallback=app_settings.brave_use_as_fallback,
            ),
            grocy=GrocySettings(
                api_url=app_settings.grocy_api_url,
                api_key=app_settings.grocy_api_key.get_secret_value() if app_settings.grocy_api_key else "",
                web_url=app_settings.grocy_web_url,
                timeout_seconds=app_settings.grocy_timeout_seconds,
            ),
            scanning=ScanningSettings(
                auto_add_enabled=app_settings.auto_add_enabled,
                kiosk_mode_enabled=app_settings.kiosk_mode_enabled,
                fuzzy_match_threshold=app_settings.fuzzy_match_threshold,
                default_quantity_unit=app_settings.default_quantity_unit,
            ),
            ui=UISettings(),
        )
    
    def _decrypt_settings(self, data: dict) -> None:
        """Decrypt sensitive values in settings data."""
        for section in data.values():
            if isinstance(section, dict):
                for key, value in section.items():
                    if key in self.SENSITIVE_KEYS and isinstance(value, str):
                        section[key] = self._decrypt(value)
    
    def _encrypt_settings(self, data: dict) -> dict:
        """Encrypt sensitive values in settings data for storage."""
        result = {}
        for section_name, section in data.items():
            if isinstance(section, dict):
                result[section_name] = {}
                for key, value in section.items():
                    if key in self.SENSITIVE_KEYS and isinstance(value, str) and value:
                        result[section_name][key] = self._encrypt(value)
                    else:
                        result[section_name][key] = value
            else:
                result[section_name] = section
        return result
    
    def save(self, settings: AllSettings) -> None:
        """Save settings to storage."""
        self._ensure_data_dir()
        
        try:
            data = settings.model_dump()
            encrypted_data = self._encrypt_settings(data)
            
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(encrypted_data, f, indent=2)
            
            self._settings = settings
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error("Failed to save settings", error=str(e))
            raise
    
    def update_section(self, section: str, values: dict[str, Any]) -> AllSettings:
        """Update a specific section of settings.
        
        Args:
            section: Section name (llm, lookup, grocy, scanning, ui)
            values: Dictionary of values to update
            
        Returns:
            Updated AllSettings
        """
        current = self.load()
        
        if section == "llm":
            current.llm = LLMSettings(**{**current.llm.model_dump(), **values})
        elif section == "lookup":
            current.lookup = LookupSettings(**{**current.lookup.model_dump(), **values})
        elif section == "grocy":
            current.grocy = GrocySettings(**{**current.grocy.model_dump(), **values})
        elif section == "scanning":
            current.scanning = ScanningSettings(**{**current.scanning.model_dump(), **values})
        elif section == "ui":
            current.ui = UISettings(**{**current.ui.model_dump(), **values})
        else:
            raise ValueError(f"Unknown settings section: {section}")
        
        self.save(current)
        return current
    
    def get_section(self, section: str) -> BaseModel:
        """Get a specific section of settings."""
        current = self.load()
        
        if section == "llm":
            return current.llm
        elif section == "lookup":
            return current.lookup
        elif section == "grocy":
            return current.grocy
        elif section == "scanning":
            return current.scanning
        elif section == "ui":
            return current.ui
        else:
            raise ValueError(f"Unknown settings section: {section}")
    
    def reset_to_defaults(self) -> AllSettings:
        """Reset all settings to defaults from config."""
        defaults = self._get_defaults_from_config()
        self.save(defaults)
        return defaults


# Global settings service instance
settings_service = SettingsService()
