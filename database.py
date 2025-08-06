"""
Database management and operations for FDIC MRM Tool
"""
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, desc, asc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from config import settings
from data_models import Base, BankRecord, DataCollectionLog, ResearchTask, BankInfo, DataSource

logger = logging.getLogger(__name__)

def serialize_pydantic_model(model):
    """Serialize a Pydantic model to a JSON-compatible dictionary"""
    return json.loads(model.json())

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.DATABASE_URL
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def add_bank(self, bank_info: BankInfo) -> int:
        """Add a new bank record to the database"""
        with self.get_session() as session:
            # Check if bank already exists
            existing = session.query(BankRecord).filter(
                or_(
                    BankRecord.bank_name == bank_info.bank_name,
                    and_(BankRecord.fdic_cert_id == bank_info.fdic_cert_id, 
                         bank_info.fdic_cert_id is not None)
                )
            ).first()
            
            if existing:
                logger.warning(f"Bank {bank_info.bank_name} already exists, updating instead")
                return self.update_bank(existing.id, bank_info)
            
            # Create new bank record
            bank_record = BankRecord(
                bank_name=bank_info.bank_name,
                fdic_cert_id=bank_info.fdic_cert_id,
                rssd_id=bank_info.rssd_id,
                asset_rank=bank_info.asset_rank,
                total_assets=bank_info.total_assets,
                size_category=bank_info.size_category.value if bank_info.size_category else None,
                headquarters_city=bank_info.headquarters_city,
                headquarters_state=bank_info.headquarters_state,
                established_date=bank_info.established_date,
                mrm_departments=[serialize_pydantic_model(dept) for dept in bank_info.mrm_departments],
                leadership=[serialize_pydantic_model(leader) for leader in bank_info.leadership],
                completeness_score=bank_info.completeness_score,
                confidence_score=bank_info.confidence_score,
                quality_status=bank_info.quality_status.value,
                last_verified=bank_info.last_verified,
                primary_source=bank_info.primary_source.value,
                data_sources=[source.value for source in bank_info.data_sources],
                source_urls=bank_info.source_urls,
                notes=bank_info.notes,
                tags=bank_info.tags,
                research_priority=bank_info.research_priority
            )
            
            session.add(bank_record)
            session.flush()
            
            logger.info(f"Added new bank: {bank_info.bank_name} (ID: {bank_record.id})")
            return bank_record.id
    
    def update_bank(self, bank_id: int, bank_info: BankInfo) -> int:
        """Update an existing bank record"""
        with self.get_session() as session:
            bank_record = session.query(BankRecord).filter(BankRecord.id == bank_id).first()
            
            if not bank_record:
                raise ValueError(f"Bank with ID {bank_id} not found")
            
            # Update fields
            bank_record.bank_name = bank_info.bank_name
            bank_record.fdic_cert_id = bank_info.fdic_cert_id
            bank_record.rssd_id = bank_info.rssd_id
            bank_record.asset_rank = bank_info.asset_rank
            bank_record.total_assets = bank_info.total_assets
            bank_record.size_category = bank_info.size_category.value if bank_info.size_category else None
            bank_record.headquarters_city = bank_info.headquarters_city
            bank_record.headquarters_state = bank_info.headquarters_state
            bank_record.established_date = bank_info.established_date
            bank_record.mrm_departments = [serialize_pydantic_model(dept) for dept in bank_info.mrm_departments]
            bank_record.leadership = [serialize_pydantic_model(leader) for leader in bank_info.leadership]
            bank_record.completeness_score = bank_info.completeness_score
            bank_record.confidence_score = bank_info.confidence_score
            bank_record.quality_status = bank_info.quality_status.value
            bank_record.last_verified = bank_info.last_verified
            bank_record.primary_source = bank_info.primary_source.value
            bank_record.data_sources = [source.value for source in bank_info.data_sources]
            bank_record.source_urls = bank_info.source_urls
            bank_record.notes = bank_info.notes
            bank_record.tags = bank_info.tags
            bank_record.research_priority = bank_info.research_priority
            bank_record.last_updated = datetime.utcnow()
            
            logger.info(f"Updated bank: {bank_info.bank_name} (ID: {bank_id})")
            return bank_id
    
    def get_bank(self, bank_id: int) -> Optional[BankInfo]:
        """Get a bank by ID"""
        with self.get_session() as session:
            bank_record = session.query(BankRecord).filter(BankRecord.id == bank_id).first()
            return bank_record.to_pydantic() if bank_record else None
    
    def get_bank_by_name(self, bank_name: str) -> Optional[BankInfo]:
        """Get a bank by name"""
        with self.get_session() as session:
            bank_record = session.query(BankRecord).filter(
                BankRecord.bank_name.ilike(f"%{bank_name}%")
            ).first()
            return bank_record.to_pydantic() if bank_record else None
    
    def get_all_banks(self, limit: int = None, offset: int = 0) -> List[BankInfo]:
        """Get all banks with optional pagination"""
        with self.get_session() as session:
            query = session.query(BankRecord).order_by(asc(BankRecord.asset_rank))
            
            if limit:
                query = query.limit(limit).offset(offset)
            
            bank_records = query.all()
            return [record.to_pydantic() for record in bank_records]
    
    def search_banks(self, 
                    name_pattern: str = None,
                    asset_rank_min: int = None,
                    asset_rank_max: int = None,
                    size_category: str = None,
                    state: str = None,
                    min_completeness: float = None,
                    has_mrm_data: bool = None) -> List[BankInfo]:
        """Search banks with various filters"""
        with self.get_session() as session:
            query = session.query(BankRecord)
            
            if name_pattern:
                query = query.filter(BankRecord.bank_name.ilike(f"%{name_pattern}%"))
            
            if asset_rank_min:
                query = query.filter(BankRecord.asset_rank >= asset_rank_min)
            
            if asset_rank_max:
                query = query.filter(BankRecord.asset_rank <= asset_rank_max)
            
            if size_category:
                query = query.filter(BankRecord.size_category == size_category)
            
            if state:
                query = query.filter(BankRecord.headquarters_state == state)
            
            if min_completeness:
                query = query.filter(BankRecord.completeness_score >= min_completeness)
            
            if has_mrm_data is not None:
                if has_mrm_data:
                    query = query.filter(BankRecord.mrm_departments.isnot(None))
                else:
                    query = query.filter(BankRecord.mrm_departments.is_(None))
            
            query = query.order_by(asc(BankRecord.asset_rank))
            bank_records = query.all()
            return [record.to_pydantic() for record in bank_records]
    
    def get_banks_needing_research(self, limit: int = 50) -> List[BankInfo]:
        """Get banks that need research (low completeness or old data)"""
        with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=30)  # 30 days ago
            
            query = session.query(BankRecord).filter(
                or_(
                    BankRecord.completeness_score < settings.MIN_COMPLETENESS_SCORE,
                    BankRecord.last_verified < cutoff_date,
                    BankRecord.last_verified.is_(None)
                )
            ).order_by(desc(BankRecord.research_priority), asc(BankRecord.asset_rank))
            
            if limit:
                query = query.limit(limit)
            
            bank_records = query.all()
            return [record.to_pydantic() for record in bank_records]
    
    def log_collection_activity(self, 
                              bank_id: int = None,
                              source: DataSource = None,
                              collection_type: str = None,
                              status: str = None,
                              records_collected: int = 0,
                              errors_encountered: int = 0,
                              execution_time: float = 0.0,
                              details: Dict[str, Any] = None,
                              error_messages: str = None):
        """Log data collection activity"""
        with self.get_session() as session:
            log_entry = DataCollectionLog(
                bank_id=bank_id,
                source=source.value if source else None,
                collection_type=collection_type,
                status=status,
                records_collected=records_collected,
                errors_encountered=errors_encountered,
                execution_time=execution_time,
                details=details or {},
                error_messages=error_messages
            )
            
            session.add(log_entry)
            logger.info(f"Logged collection activity: {collection_type} from {source} - {status}")
    
    def add_research_task(self, 
                         bank_id: int,
                         task_type: str,
                         description: str,
                         priority: int = 5,
                         assigned_to: str = None,
                         due_date: datetime = None) -> int:
        """Add a research task"""
        with self.get_session() as session:
            task = ResearchTask(
                bank_id=bank_id,
                task_type=task_type,
                description=description,
                priority=priority,
                assigned_to=assigned_to,
                due_date=due_date
            )
            
            session.add(task)
            session.flush()
            
            logger.info(f"Added research task for bank ID {bank_id}: {task_type}")
            return task.id
    
    def get_pending_research_tasks(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get pending research tasks with bank information"""
        with self.get_session() as session:
            query = session.query(ResearchTask).filter(
                ResearchTask.status == 'pending'
            ).order_by(desc(ResearchTask.priority), asc(ResearchTask.created_at))
            
            if limit:
                query = query.limit(limit)
            
            tasks = query.all()
            
            # Convert to dictionaries with all needed data loaded
            result = []
            for task in tasks:
                task_dict = {
                    'id': task.id,
                    'bank_id': task.bank_id,
                    'task_type': task.task_type,
                    'description': task.description,
                    'priority': task.priority,
                    'status': task.status,
                    'assigned_to': task.assigned_to,
                    'created_at': task.created_at,
                    'due_date': task.due_date,
                    'completed_at': task.completed_at
                }
                result.append(task_dict)
            
            return result
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            total_banks = session.query(BankRecord).count()
            banks_with_mrm = session.query(BankRecord).filter(
                BankRecord.mrm_departments.isnot(None)
            ).count()
            
            avg_completeness = session.query(BankRecord.completeness_score).filter(
                BankRecord.completeness_score > 0
            ).all()
            avg_completeness = sum(score[0] for score in avg_completeness) / len(avg_completeness) if avg_completeness else 0
            
            pending_tasks = session.query(ResearchTask).filter(
                ResearchTask.status == 'pending'
            ).count()
            
            recent_collections = session.query(DataCollectionLog).filter(
                DataCollectionLog.timestamp >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            return {
                "total_banks": total_banks,
                "banks_with_mrm_data": banks_with_mrm,
                "mrm_coverage_percentage": (banks_with_mrm / total_banks * 100) if total_banks > 0 else 0,
                "average_completeness_score": round(avg_completeness, 2),
                "pending_research_tasks": pending_tasks,
                "recent_collection_activities": recent_collections
            }

# Global database manager instance
db_manager = DatabaseManager()