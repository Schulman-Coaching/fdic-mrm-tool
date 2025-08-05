"""
FDIC API integration for collecting bank data
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from config import settings
from data_models import BankInfo, DataSource, BankSizeCategory
from database import db_manager

logger = logging.getLogger(__name__)

class FDICCollector:
    """Collects bank data from FDIC APIs and databases"""
    
    def __init__(self):
        self.base_url = settings.FDIC_API_BASE_URL
        self.timeout = settings.FDIC_API_TIMEOUT
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_top_banks_by_assets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get top banks by total assets from FDIC API"""
        try:
            # FDIC API endpoint for institutions
            url = f"{self.base_url}/institutions"
            
            params = {
                'filters': 'ACTIVE:1',  # Only active banks
                'fields': 'NAME,CERT,RSSDID,ASSET,CITY,STALP,DATEUPDT,REPDTE,CHARTER,REGAGENT',
                'sort_by': 'ASSET',
                'sort_order': 'DESC',
                'limit': limit,
                'format': 'json'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    banks = data.get('data', [])
                    logger.info(f"Retrieved {len(banks)} banks from FDIC API")
                    return banks
                else:
                    logger.error(f"FDIC API request failed with status {response.status}")
                    return []
        
        except Exception as e:
            logger.error(f"Error fetching banks from FDIC API: {e}")
            return []
    
    async def get_bank_details(self, cert_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific bank by CERT ID"""
        try:
            url = f"{self.base_url}/institutions"
            
            params = {
                'filters': f'CERT:{cert_id}',
                'fields': 'NAME,CERT,RSSDID,ASSET,CITY,STALP,DATEUPDT,REPDTE,CHARTER,REGAGENT,WEBADDR,OFFICES,EMPLOYEES',
                'format': 'json'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    banks = data.get('data', [])
                    return banks[0] if banks else None
                else:
                    logger.error(f"FDIC API request failed for CERT {cert_id} with status {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error fetching bank details for CERT {cert_id}: {e}")
            return None
    
    def _convert_fdic_to_bank_info(self, fdic_data: Dict[str, Any], asset_rank: int = None) -> BankInfo:
        """Convert FDIC API data to BankInfo model"""
        try:
            # Extract basic information
            bank_name = fdic_data.get('NAME', '').strip()
            cert_id = fdic_data.get('CERT')
            rssd_id = fdic_data.get('RSSDID')
            
            # Convert asset amount (FDIC reports in thousands)
            asset_str = fdic_data.get('ASSET', '0')
            try:
                total_assets = float(asset_str) / 1000 if asset_str else 0  # Convert to millions
            except (ValueError, TypeError):
                total_assets = 0
            
            # Location information
            city = fdic_data.get('CITY', '').strip()
            state = fdic_data.get('STALP', '').strip()
            
            # Determine size category
            size_category = self._determine_size_category(total_assets)
            
            # Create BankInfo object
            bank_info = BankInfo(
                bank_name=bank_name,
                fdic_cert_id=cert_id,
                rssd_id=rssd_id,
                asset_rank=asset_rank,
                total_assets=total_assets,
                size_category=size_category,
                headquarters_city=city,
                headquarters_state=state,
                primary_source=DataSource.FDIC_API,
                data_sources=[DataSource.FDIC_API],
                source_urls=[f"{self.base_url}/institutions?filters=CERT:{cert_id}"],
                confidence_score=0.95,  # High confidence for official FDIC data
                tags=["fdic_official", "automated_collection"],
                research_priority=8,  # High priority for data collection
                last_updated=datetime.utcnow()
            )
            
            return bank_info
        
        except Exception as e:
            logger.error(f"Error converting FDIC data to BankInfo: {e}")
            raise
    
    def _determine_size_category(self, total_assets_millions: float) -> BankSizeCategory:
        """Determine bank size category based on total assets"""
        assets_billions = total_assets_millions / 1000
        
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
    
    async def collect_top_100_banks(self) -> List[BankInfo]:
        """Collect top 100 banks by assets and convert to BankInfo objects"""
        start_time = time.time()
        banks_collected = []
        errors = 0
        
        try:
            fdic_banks = await self.get_top_banks_by_assets(100)
            
            for rank, fdic_bank in enumerate(fdic_banks, 1):
                try:
                    bank_info = self._convert_fdic_to_bank_info(fdic_bank, rank)
                    banks_collected.append(bank_info)
                    
                    # Add delay to be respectful to FDIC API
                    await asyncio.sleep(settings.SCRAPING_DELAY)
                    
                except Exception as e:
                    logger.error(f"Error processing bank rank {rank}: {e}")
                    errors += 1
                    continue
            
            execution_time = time.time() - start_time
            
            # Log collection activity
            db_manager.log_collection_activity(
                source=DataSource.FDIC_API,
                collection_type="top_100_banks",
                status="success" if errors == 0 else "partial",
                records_collected=len(banks_collected),
                errors_encountered=errors,
                execution_time=execution_time,
                details={
                    "total_requested": 100,
                    "successfully_processed": len(banks_collected),
                    "api_endpoint": f"{self.base_url}/institutions"
                }
            )
            
            logger.info(f"Collected {len(banks_collected)} banks from FDIC API in {execution_time:.2f} seconds")
            return banks_collected
        
        except Exception as e:
            execution_time = time.time() - start_time
            db_manager.log_collection_activity(
                source=DataSource.FDIC_API,
                collection_type="top_100_banks",
                status="failed",
                records_collected=len(banks_collected),
                errors_encountered=errors + 1,
                execution_time=execution_time,
                error_messages=str(e)
            )
            logger.error(f"Failed to collect banks from FDIC API: {e}")
            return banks_collected
    
    async def update_existing_bank_data(self, bank_id: int) -> bool:
        """Update existing bank with fresh FDIC data"""
        try:
            # Get existing bank info
            bank_info = db_manager.get_bank(bank_id)
            if not bank_info or not bank_info.fdic_cert_id:
                logger.warning(f"Bank ID {bank_id} not found or missing FDIC CERT ID")
                return False
            
            # Fetch fresh data from FDIC
            fdic_data = await self.get_bank_details(bank_info.fdic_cert_id)
            if not fdic_data:
                logger.warning(f"No FDIC data found for CERT ID {bank_info.fdic_cert_id}")
                return False
            
            # Update bank info with fresh data
            updated_info = self._convert_fdic_to_bank_info(fdic_data, bank_info.asset_rank)
            
            # Preserve existing MRM data and research
            updated_info.mrm_departments = bank_info.mrm_departments
            updated_info.leadership = bank_info.leadership
            updated_info.notes = bank_info.notes
            updated_info.tags = list(set(bank_info.tags + updated_info.tags))
            updated_info.research_priority = bank_info.research_priority
            
            # Update completeness and confidence scores
            if bank_info.mrm_departments or bank_info.leadership:
                updated_info.completeness_score = max(bank_info.completeness_score, updated_info.completeness_score)
                updated_info.confidence_score = (bank_info.confidence_score + updated_info.confidence_score) / 2
            
            # Save updated information
            db_manager.update_bank(bank_id, updated_info)
            
            logger.info(f"Updated bank {updated_info.bank_name} with fresh FDIC data")
            return True
        
        except Exception as e:
            logger.error(f"Error updating bank ID {bank_id} with FDIC data: {e}")
            return False
    
    async def populate_placeholder_banks(self) -> int:
        """Populate database with placeholder entries for top 100 banks"""
        try:
            # Get existing banks to avoid duplicates
            existing_banks = db_manager.get_all_banks()
            existing_certs = {bank.fdic_cert_id for bank in existing_banks if bank.fdic_cert_id}
            existing_names = {bank.bank_name.lower() for bank in existing_banks}
            
            # Collect top 100 banks from FDIC
            fdic_banks = await self.collect_top_100_banks()
            
            added_count = 0
            for bank_info in fdic_banks:
                # Skip if bank already exists
                if (bank_info.fdic_cert_id in existing_certs or 
                    bank_info.bank_name.lower() in existing_names):
                    logger.info(f"Bank {bank_info.bank_name} already exists, skipping")
                    continue
                
                try:
                    bank_id = db_manager.add_bank(bank_info)
                    added_count += 1
                    logger.info(f"Added placeholder bank: {bank_info.bank_name} (ID: {bank_id})")
                    
                    # Create research task for MRM data collection
                    db_manager.add_research_task(
                        bank_id=bank_id,
                        task_type="mrm_research",
                        description=f"Research MRM department and leadership information for {bank_info.bank_name}",
                        priority=8 if bank_info.asset_rank <= 50 else 6
                    )
                    
                except Exception as e:
                    logger.error(f"Error adding bank {bank_info.bank_name}: {e}")
                    continue
            
            logger.info(f"Added {added_count} new placeholder banks to database")
            return added_count
        
        except Exception as e:
            logger.error(f"Error populating placeholder banks: {e}")
            return 0

# Async function for easy usage
async def collect_fdic_data():
    """Convenience function to collect FDIC data"""
    async with FDICCollector() as collector:
        return await collector.populate_placeholder_banks()

# Global collector instance
fdic_collector = FDICCollector()