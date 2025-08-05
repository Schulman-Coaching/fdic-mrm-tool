"""
Configuration settings for FDIC MRM Data Collection Tool
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    EXPORTS_DIR: Path = PROJECT_ROOT / "exports"
    CACHE_DIR: Path = PROJECT_ROOT / "cache"
    
    # Database settings
    DATABASE_URL: str = Field(default="sqlite:///fdic_mrm.db")
    
    # API Keys and credentials
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    LINKEDIN_USERNAME: Optional[str] = Field(default=None, env="LINKEDIN_USERNAME")
    LINKEDIN_PASSWORD: Optional[str] = Field(default=None, env="LINKEDIN_PASSWORD")
    SEC_EDGAR_USER_AGENT: str = Field(default="FDIC MRM Tool (contact@example.com)")
    
    # FDIC API settings
    FDIC_API_BASE_URL: str = "https://banks.data.fdic.gov/api"
    FDIC_API_TIMEOUT: int = 30
    
    # Web scraping settings
    SCRAPING_DELAY: float = 1.0  # Delay between requests in seconds
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Data processing settings
    BATCH_SIZE: int = 100
    MAX_WORKERS: int = 4
    CACHE_EXPIRY_HOURS: int = 24
    
    # Data quality thresholds
    MIN_COMPLETENESS_SCORE: float = 0.6
    MIN_CONFIDENCE_SCORE: float = 0.7
    
    # Export settings
    DEFAULT_EXPORT_FORMAT: str = "xlsx"
    MAX_EXPORT_ROWS: int = 10000
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    
    # Scheduling settings
    AUTO_UPDATE_ENABLED: bool = True
    DAILY_UPDATE_HOUR: int = 2  # 2 AM
    WEEKLY_UPDATE_DAY: int = 1  # Monday
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# MRM-related keywords and patterns for data extraction
MRM_KEYWORDS = [
    "model risk management", "model risk", "mrm", "model validation",
    "model governance", "quantitative risk", "credit risk modeling",
    "market risk modeling", "operational risk modeling", "stress testing",
    "model review", "model oversight", "risk analytics", "model audit",
    "chief model risk officer", "cmro", "head of model risk",
    "model risk governance", "model risk controls", "model risk framework"
]

# Leadership title patterns
LEADERSHIP_PATTERNS = [
    r"chief.*model.*risk.*officer",
    r"head.*model.*risk",
    r"director.*model.*risk",
    r"vice.*president.*model.*risk",
    r"managing.*director.*model.*risk",
    r"executive.*vice.*president.*model.*risk",
    r"senior.*vice.*president.*model.*risk"
]

# Bank classification by asset size (in billions)
BANK_SIZE_CATEGORIES = {
    "mega": 500,      # > $500B
    "large": 100,     # $100B - $500B
    "regional": 10,   # $10B - $100B
    "community": 1,   # $1B - $10B
    "small": 0        # < $1B
}

# Data source priorities (higher number = higher priority)
DATA_SOURCE_PRIORITIES = {
    "fdic_api": 10,
    "sec_edgar": 9,
    "bank_website": 8,
    "linkedin": 7,
    "regulatory_filing": 6,
    "manual_entry": 5,
    "third_party": 3
}

# Create settings instance
settings = Settings()

# Ensure directories exist
for directory in [settings.DATA_DIR, settings.LOGS_DIR, settings.EXPORTS_DIR, settings.CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)