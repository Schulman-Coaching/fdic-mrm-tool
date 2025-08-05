"""
Comprehensive MRM data extraction from multiple sources
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from config import settings
from data_models import BankInfo, LeadershipInfo, MRMDepartmentInfo, DataSource
from database import db_manager
from linkedin_collector import LinkedInCollector
from fdic_collector import FDICCollector

logger = logging.getLogger(__name__)

class MRMExtractor:
    """Orchestrates MRM data extraction from multiple sources"""
    
    def __init__(self):
        self.linkedin_collector = None
        self.fdic_collector = None
        self.extraction_stats = {
            'banks_processed': 0,
            'linkedin_profiles_found': 0,
            'errors_encountered': 0,
            'sources_used': set()
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.linkedin_collector = LinkedInCollector()
        self.fdic_collector = FDICCollector()
        await self.fdic_collector.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.linkedin_collector:
            self.linkedin_collector.close()
        if self.fdic_collector:
            await self.fdic_collector.__aexit__(exc_type, exc_val, exc_tb)
    
    async def extract_mrm_data_for_bank(self, bank: BankInfo) -> BankInfo:
        """Extract comprehensive MRM data for a single bank from all available sources"""
        logger.info(f"Starting MRM extraction for {bank.bank_name}")
        start_time = time.time()
        
        try:
            # Track original data for comparison
            original_leadership_count = len(bank.leadership)
            original_dept_count = len(bank.mrm_departments)
            
            # 1. LinkedIn Data Collection
            if settings.LINKEDIN_USERNAME and settings.LINKEDIN_PASSWORD:
                try:
                    linkedin_profiles = self.linkedin_collector.collect_bank_leadership(bank.bank_name)
                    if linkedin_profiles:
                        # Merge with existing leadership data
                        existing_urls = {leader.linkedin_url for leader in bank.leadership if leader.linkedin_url}
                        new_profiles = [profile for profile in linkedin_profiles 
                                      if profile.linkedin_url not in existing_urls]
                        
                        bank.leadership.extend(new_profiles)
                        self.extraction_stats['linkedin_profiles_found'] += len(new_profiles)
                        self.extraction_stats['sources_used'].add('linkedin')
                        
                        logger.info(f"Added {len(new_profiles)} LinkedIn profiles for {bank.bank_name}")
                    
                except Exception as e:
                    logger.warning(f"LinkedIn extraction failed for {bank.bank_name}: {e}")
                    self.extraction_stats['errors_encountered'] += 1
            
            # 2. Bank Website Scraping (placeholder for future implementation)
            try:
                website_data = await self._extract_from_bank_website(bank)
                if website_data:
                    self._merge_website_data(bank, website_data)
                    self.extraction_stats['sources_used'].add('bank_website')
            except Exception as e:
                logger.warning(f"Website extraction failed for {bank.bank_name}: {e}")
                self.extraction_stats['errors_encountered'] += 1
            
            # 3. SEC EDGAR Filings (placeholder for future implementation)
            try:
                edgar_data = await self._extract_from_edgar_filings(bank)
                if edgar_data:
                    self._merge_edgar_data(bank, edgar_data)
                    self.extraction_stats['sources_used'].add('sec_edgar')
            except Exception as e:
                logger.warning(f"EDGAR extraction failed for {bank.bank_name}: {e}")
                self.extraction_stats['errors_encountered'] += 1
            
            # 4. Update bank metadata
            bank.last_updated = datetime.utcnow()
            if bank.leadership or bank.mrm_departments:
                bank.last_verified = datetime.utcnow()
            
            # Recalculate completeness and confidence scores
            bank = self._recalculate_scores(bank)
            
            # Log extraction results
            new_leadership_count = len(bank.leadership) - original_leadership_count
            new_dept_count = len(bank.mrm_departments) - original_dept_count
            
            execution_time = time.time() - start_time
            
            db_manager.log_collection_activity(
                bank_id=getattr(bank, 'id', None),
                source=DataSource.MANUAL_ENTRY,  # Multi-source extraction
                collection_type="comprehensive_mrm_extraction",
                status="success",
                records_collected=new_leadership_count + new_dept_count,
                execution_time=execution_time,
                details={
                    "bank_name": bank.bank_name,
                    "new_leadership": new_leadership_count,
                    "new_departments": new_dept_count,
                    "sources_used": list(self.extraction_stats['sources_used']),
                    "total_leadership": len(bank.leadership),
                    "total_departments": len(bank.mrm_departments)
                }
            )
            
            logger.info(f"MRM extraction completed for {bank.bank_name} in {execution_time:.2f}s")
            self.extraction_stats['banks_processed'] += 1
            
            return bank
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"MRM extraction failed for {bank.bank_name}: {e}")
            self.extraction_stats['errors_encountered'] += 1
            
            db_manager.log_collection_activity(
                bank_id=getattr(bank, 'id', None),
                source=DataSource.MANUAL_ENTRY,
                collection_type="comprehensive_mrm_extraction",
                status="failed",
                execution_time=execution_time,
                error_messages=str(e)
            )
            
            return bank
    
    async def _extract_from_bank_website(self, bank: BankInfo) -> Optional[Dict[str, Any]]:
        """Extract MRM data from bank's official website"""
        # Placeholder for future implementation
        # This would scrape the bank's careers page, leadership page, etc.
        logger.debug(f"Website extraction for {bank.bank_name} - placeholder")
        return None
    
    async def _extract_from_edgar_filings(self, bank: BankInfo) -> Optional[Dict[str, Any]]:
        """Extract MRM data from SEC EDGAR filings"""
        # Placeholder for future implementation
        # This would search proxy statements, 10-K forms, etc.
        logger.debug(f"EDGAR extraction for {bank.bank_name} - placeholder")
        return None
    
    def _merge_website_data(self, bank: BankInfo, website_data: Dict[str, Any]):
        """Merge website-extracted data into bank record"""
        # Placeholder for merging website data
        pass
    
    def _merge_edgar_data(self, bank: BankInfo, edgar_data: Dict[str, Any]):
        """Merge EDGAR-extracted data into bank record"""
        # Placeholder for merging EDGAR data
        pass
    
    def _recalculate_scores(self, bank: BankInfo) -> BankInfo:
        """Recalculate completeness and confidence scores based on available data"""
        # Calculate completeness score
        total_fields = 15
        completed_fields = 0
        
        # Basic information
        if bank.bank_name: completed_fields += 1
        if bank.fdic_cert_id: completed_fields += 1
        if bank.asset_rank: completed_fields += 1
        if bank.total_assets: completed_fields += 1
        if bank.headquarters_city: completed_fields += 1
        if bank.headquarters_state: completed_fields += 1
        
        # MRM information
        if bank.mrm_departments: completed_fields += 3
        if bank.leadership: completed_fields += 3
        if any(l.name for l in bank.leadership): completed_fields += 1
        if any(l.title for l in bank.leadership): completed_fields += 1
        if any(l.linkedin_url for l in bank.leadership): completed_fields += 1
        
        # Metadata
        if bank.source_urls: completed_fields += 1
        if bank.notes: completed_fields += 1
        if bank.last_verified: completed_fields += 1
        
        bank.completeness_score = min(completed_fields / total_fields, 1.0)
        
        # Calculate confidence score based on data sources
        source_weights = {
            DataSource.FDIC_API: 0.95,
            DataSource.LINKEDIN: 0.8,
            DataSource.SEC_EDGAR: 0.9,
            DataSource.BANK_WEBSITE: 0.85,
            DataSource.MANUAL_ENTRY: 0.7
        }
        
        if bank.data_sources:
            weighted_confidence = sum(source_weights.get(source, 0.5) for source in bank.data_sources)
            bank.confidence_score = min(weighted_confidence / len(bank.data_sources), 1.0)
        
        return bank
    
    async def extract_mrm_data_batch(self, banks: List[BankInfo], batch_size: int = 5) -> List[BankInfo]:
        """Extract MRM data for multiple banks in batches"""
        logger.info(f"Starting batch MRM extraction for {len(banks)} banks")
        
        updated_banks = []
        
        # Process banks in batches to avoid overwhelming APIs
        for i in range(0, len(banks), batch_size):
            batch = banks[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(banks) + batch_size - 1)//batch_size}")
            
            batch_results = []
            for bank in batch:
                try:
                    updated_bank = await self.extract_mrm_data_for_bank(bank)
                    batch_results.append(updated_bank)
                    
                    # Add delay between banks to be respectful to APIs
                    await asyncio.sleep(settings.SCRAPING_DELAY * 2)
                    
                except Exception as e:
                    logger.error(f"Error processing {bank.bank_name}: {e}")
                    batch_results.append(bank)  # Return original bank if extraction fails
            
            updated_banks.extend(batch_results)
            
            # Longer delay between batches
            if i + batch_size < len(banks):
                await asyncio.sleep(settings.SCRAPING_DELAY * 5)
        
        logger.info(f"Batch MRM extraction completed. Stats: {self.extraction_stats}")
        return updated_banks
    
    async def extract_and_update_database(self, banks: List[BankInfo]) -> Dict[str, Any]:
        """Extract MRM data and update database records"""
        logger.info(f"Starting database update for {len(banks)} banks")
        
        updated_banks = await self.extract_mrm_data_batch(banks)
        
        update_stats = {
            'banks_updated': 0,
            'update_errors': 0,
            'total_new_leadership': 0,
            'total_new_departments': 0
        }
        
        for bank in updated_banks:
            try:
                # Find existing bank record
                existing_bank = db_manager.get_bank_by_name(bank.bank_name)
                if existing_bank:
                    # Update the existing record
                    bank_id = db_manager.update_bank(existing_bank.id if hasattr(existing_bank, 'id') else None, bank)
                    update_stats['banks_updated'] += 1
                    logger.info(f"Updated database record for {bank.bank_name}")
                else:
                    # Add as new record
                    bank_id = db_manager.add_bank(bank)
                    update_stats['banks_updated'] += 1
                    logger.info(f"Added new database record for {bank.bank_name}")
                
            except Exception as e:
                logger.error(f"Error updating database for {bank.bank_name}: {e}")
                update_stats['update_errors'] += 1
        
        # Combine stats
        final_stats = {**self.extraction_stats, **update_stats}
        logger.info(f"Database update completed. Final stats: {final_stats}")
        
        return final_stats

# Async function for easy usage
async def extract_mrm_data_for_banks(banks: List[BankInfo]) -> Dict[str, Any]:
    """Convenience function to extract MRM data for multiple banks"""
    async with MRMExtractor() as extractor:
        return await extractor.extract_and_update_database(banks)

# Global extractor instance
mrm_extractor = MRMExtractor()