"""
Data models for FDIC MRM information using Pydantic for validation
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class DataSource(str, Enum):
    """Enumeration of data sources"""
    FDIC_API = "fdic_api"
    SEC_EDGAR = "sec_edgar"
    BANK_WEBSITE = "bank_website"
    LINKEDIN = "linkedin"
    REGULATORY_FILING = "regulatory_filing"
    MANUAL_ENTRY = "manual_entry"
    THIRD_PARTY = "third_party"

class BankSizeCategory(str, Enum):
    """Bank size categories based on assets"""
    MEGA = "mega"           # > $500B
    LARGE = "large"         # $100B - $500B
    REGIONAL = "regional"   # $10B - $100B
    COMMUNITY = "community" # $1B - $10B
    SMALL = "small"         # < $1B

class DataQualityStatus(str, Enum):
    """Data quality status levels"""
    EXCELLENT = "excellent"  # > 90% complete, high confidence
    GOOD = "good"           # 70-90% complete, medium-high confidence
    FAIR = "fair"           # 50-70% complete, medium confidence
    POOR = "poor"           # < 50% complete, low confidence
    UNKNOWN = "unknown"     # Not yet assessed

# Pydantic Models for API and validation
class LeadershipInfo(BaseModel):
    """Individual leadership information"""
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source: DataSource = DataSource.MANUAL_ENTRY
    last_verified: Optional[datetime] = None
    notes: Optional[str] = None

class MRMDepartmentInfo(BaseModel):
    """MRM Department structure information"""
    department_name: str
    parent_organization: Optional[str] = None
    reporting_structure: Optional[str] = None
    team_size: Optional[int] = None
    budget: Optional[float] = None
    established_date: Optional[datetime] = None
    key_functions: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source: DataSource = DataSource.MANUAL_ENTRY
    last_updated: Optional[datetime] = None

class BankInfo(BaseModel):
    """Complete bank information model"""
    # Basic bank information
    bank_name: str
    fdic_cert_id: Optional[int] = None
    rssd_id: Optional[int] = None
    asset_rank: Optional[int] = None
    total_assets: Optional[float] = None  # in millions
    size_category: Optional[BankSizeCategory] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    established_date: Optional[datetime] = None
    
    # MRM Department information
    mrm_departments: List[MRMDepartmentInfo] = Field(default_factory=list)
    leadership: List[LeadershipInfo] = Field(default_factory=list)
    
    # Data quality and metadata
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_status: DataQualityStatus = DataQualityStatus.UNKNOWN
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    last_verified: Optional[datetime] = None
    
    # Source tracking
    primary_source: DataSource = DataSource.MANUAL_ENTRY
    data_sources: List[DataSource] = Field(default_factory=list)
    source_urls: List[str] = Field(default_factory=list)
    
    # Additional metadata
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    research_priority: int = Field(default=5, ge=1, le=10)  # 1=low, 10=high
    
    @validator('size_category', pre=True, always=True)
    def determine_size_category(cls, v, values):
        """Automatically determine size category based on total assets"""
        if v is not None:
            return v
        
        assets = values.get('total_assets')
        if assets is None:
            return None
            
        # Convert to billions for comparison
        assets_billions = assets / 1000
        
        if assets_billions > 500:
            return BankSizeCategory.MEGA
        elif assets_billions > 100:
            return BankSizeCategory.LARGE
        elif assets_billions > 10:
            return BankSizeCategory.REGIONAL
        elif assets_billions > 1:
            return BankSizeCategory.COMMUNITY
        else:
            return BankSizeCategory.SMALL
    
    @validator('completeness_score', pre=True, always=True)
    def calculate_completeness_score(cls, v, values):
        """Calculate completeness score based on available data"""
        if v != 0.0:  # If manually set, keep it
            return v
        
        total_fields = 15  # Key fields to track
        completed_fields = 0
        
        # Check basic information
        if values.get('bank_name'): completed_fields += 1
        if values.get('fdic_cert_id'): completed_fields += 1
        if values.get('asset_rank'): completed_fields += 1
        if values.get('total_assets'): completed_fields += 1
        if values.get('headquarters_city'): completed_fields += 1
        if values.get('headquarters_state'): completed_fields += 1
        
        # Check MRM information
        mrm_depts = values.get('mrm_departments', [])
        if mrm_depts: completed_fields += 2
        
        leadership = values.get('leadership', [])
        if leadership: completed_fields += 2
        if any(l.name for l in leadership): completed_fields += 1
        if any(l.title for l in leadership): completed_fields += 1
        
        # Check metadata
        if values.get('source_urls'): completed_fields += 1
        if values.get('notes'): completed_fields += 1
        if values.get('last_verified'): completed_fields += 1
        if values.get('data_sources'): completed_fields += 1
        
        return min(completed_fields / total_fields, 1.0)

# SQLAlchemy Models for database storage
class BankRecord(Base):
    """SQLAlchemy model for bank records"""
    __tablename__ = 'banks'
    
    id = Column(Integer, primary_key=True)
    bank_name = Column(String(255), nullable=False, index=True)
    fdic_cert_id = Column(Integer, unique=True, index=True)
    rssd_id = Column(Integer, index=True)
    asset_rank = Column(Integer, index=True)
    total_assets = Column(Float)
    size_category = Column(String(50))
    headquarters_city = Column(String(100))
    headquarters_state = Column(String(50))
    established_date = Column(DateTime)
    
    # MRM Information (stored as JSON)
    mrm_departments = Column(JSON)
    leadership = Column(JSON)
    
    # Data quality metrics
    completeness_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    quality_status = Column(String(50), default='unknown')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_verified = Column(DateTime)
    
    # Source tracking
    primary_source = Column(String(50))
    data_sources = Column(JSON)
    source_urls = Column(JSON)
    
    # Additional metadata
    notes = Column(Text)
    tags = Column(JSON)
    research_priority = Column(Integer, default=5)
    
    def to_pydantic(self) -> BankInfo:
        """Convert SQLAlchemy model to Pydantic model"""
        return BankInfo(
            bank_name=self.bank_name,
            fdic_cert_id=self.fdic_cert_id,
            rssd_id=self.rssd_id,
            asset_rank=self.asset_rank,
            total_assets=self.total_assets,
            size_category=self.size_category,
            headquarters_city=self.headquarters_city,
            headquarters_state=self.headquarters_state,
            established_date=self.established_date,
            mrm_departments=[MRMDepartmentInfo(**dept) for dept in (self.mrm_departments or [])],
            leadership=[LeadershipInfo(**leader) for leader in (self.leadership or [])],
            completeness_score=self.completeness_score or 0.0,
            confidence_score=self.confidence_score or 0.0,
            quality_status=self.quality_status or DataQualityStatus.UNKNOWN,
            last_updated=self.last_updated or datetime.utcnow(),
            last_verified=self.last_verified,
            primary_source=self.primary_source or DataSource.MANUAL_ENTRY,
            data_sources=self.data_sources or [],
            source_urls=self.source_urls or [],
            notes=self.notes,
            tags=self.tags or [],
            research_priority=self.research_priority or 5
        )

class DataCollectionLog(Base):
    """Log of data collection activities"""
    __tablename__ = 'collection_logs'
    
    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, index=True)
    source = Column(String(50), nullable=False)
    collection_type = Column(String(100))  # 'full_refresh', 'update', 'verification'
    status = Column(String(50))  # 'success', 'partial', 'failed'
    records_collected = Column(Integer, default=0)
    errors_encountered = Column(Integer, default=0)
    execution_time = Column(Float)  # in seconds
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON)  # Additional details about the collection
    error_messages = Column(Text)

class ResearchTask(Base):
    """Research tasks for manual data collection"""
    __tablename__ = 'research_tasks'
    
    id = Column(Integer, primary_key=True)
    bank_id = Column(Integer, nullable=False, index=True)
    task_type = Column(String(100))  # 'leadership_research', 'department_structure', etc.
    priority = Column(Integer, default=5)
    status = Column(String(50), default='pending')  # 'pending', 'in_progress', 'completed', 'failed'
    assigned_to = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    description = Column(Text)
    findings = Column(Text)
    sources_checked = Column(JSON)
    notes = Column(Text)