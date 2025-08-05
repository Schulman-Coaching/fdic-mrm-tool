"""
Parser for existing FDIC MRM dataset and data import functionality
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from data_models import BankInfo, LeadershipInfo, MRMDepartmentInfo, DataSource, BankSizeCategory
from database import db_manager

logger = logging.getLogger(__name__)

@dataclass
class RawBankData:
    """Raw bank data structure for parsing"""
    bank_name: str
    asset_rank: str
    mrm_department_names: str
    key_leadership_titles: str
    named_leaders: str
    notes_sources: str

class DataParser:
    """Parses and imports existing bank MRM data"""
    
    def __init__(self):
        self.leadership_title_patterns = [
            r"chief.*model.*risk.*officer",
            r"cmro",
            r"head.*model.*risk",
            r"director.*model.*risk",
            r"vice.*president.*model.*risk",
            r"managing.*director.*model.*risk",
            r"executive.*vice.*president.*model.*risk",
            r"senior.*vice.*president.*model.*risk",
            r"evp.*model.*risk",
            r"svp.*model.*risk"
        ]
    
    def parse_existing_dataset(self) -> List[BankInfo]:
        """Parse the existing 22-bank dataset"""
        raw_data = self._get_existing_raw_data()
        parsed_banks = []
        
        for raw_bank in raw_data:
            try:
                bank_info = self._parse_single_bank(raw_bank)
                parsed_banks.append(bank_info)
                logger.info(f"Parsed bank: {bank_info.bank_name}")
            except Exception as e:
                logger.error(f"Error parsing bank {raw_bank.bank_name}: {e}")
                continue
        
        return parsed_banks
    
    def _get_existing_raw_data(self) -> List[RawBankData]:
        """Get the existing 22-bank raw data"""
        return [
            RawBankData(
                bank_name="JPMorgan Chase & Co.",
                asset_rank="1",
                mrm_department_names="Model Risk Governance and Review (MRGR)",
                key_leadership_titles="• Vice President, Risk Management - Business Analysis Manager (within MRGR) • Chief Operating Officer, Model Risk Governance & Review",
                named_leaders="Ashwani Aggarwal (former COO of MRGR)",
                notes_sources="MRGR is described as a global team of modeling experts within the Risk Management and Compliance organization, indicating a centralized and specialized function."
            ),
            RawBankData(
                bank_name="Bank of America",
                asset_rank="2",
                mrm_department_names="Model Risk Management; Global Financial Crimes (coordinates with MRM)",
                key_leadership_titles="• Managing Director, Model Risk Officer • Head of Model Risk - Consumer, Small Business, Wealth & Investment Management",
                named_leaders="Manoj Singh; Harish Sharma (former Head)",
                notes_sources="MRM is a distinct function that interacts with various business lines and other risk teams like Global Financial Crimes, highlighting its cross-functional oversight role."
            ),
            RawBankData(
                bank_name="Citigroup Inc.",
                asset_rank="3",
                mrm_department_names="Model Risk Management",
                key_leadership_titles="• Model Risk Governance Manager • Head of Model Risk Management (former role) • Managing Director, Global Head of Credit Risk Strategy, Digitization and Execution Oversight",
                named_leaders="Steven Umlauf (former Head of MRM); Savy Sriram",
                notes_sources="MRM is a global function within the broader Risk organization. The \"Governance Manager\" title underscores a focus on policy and framework implementation."
            ),
            RawBankData(
                bank_name="Wells Fargo & Co.",
                asset_rank="4",
                mrm_department_names="Corporate Model Risk (CMR); Model Risk Management (MRM)",
                key_leadership_titles="• EVP, Head of Corporate Model Risk • Model Risk Officer (Quantitative Analytics Director) • Head of Decision Science and AI Model Validation",
                named_leaders="Agus Sudjianto (former Head of CMR); Jie Chen",
                notes_sources="The \"Corporate Model Risk\" title suggests a centralized, enterprise-level strategic function. The bank shows clear specialization with a dedicated head for AI/ML validation."
            ),
            RawBankData(
                bank_name="Goldman Sachs",
                asset_rank="5",
                mrm_department_names="Model Risk Management (MRM)",
                key_leadership_titles="• Chief Model Risk Officer (CMRO), GS Bank • Model Risk Governance Vice President",
                named_leaders="Ramakrishnan Chirayathumadom",
                notes_sources="MRM is explicitly listed as a key function within the firm's Risk division. The CMRO title is formally used for the primary bank entity (GS Bank)."
            ),
            RawBankData(
                bank_name="Morgan Stanley",
                asset_rank="6",
                mrm_department_names="Model Risk Management (MRM)",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Executive Director, Model Risk Management Governance",
                named_leaders="Tony Cirincione (former CMRO)",
                notes_sources="The existence of a CMRO is confirmed in official corporate documents. The \"Executive Director of Governance\" role points to a senior position focused on framework and policy."
            ),
            RawBankData(
                bank_name="U.S. Bancorp",
                asset_rank="7",
                mrm_department_names="Enterprise Model Risk",
                key_leadership_titles="• Chief Model Risk Officer (CMRO)",
                named_leaders="Yu Pan",
                notes_sources="The CMRO title indicates a senior, centralized leader responsible for all enterprise model risk functions."
            ),
            RawBankData(
                bank_name="PNC Financial Services",
                asset_rank="8",
                mrm_department_names="Model Risk Management Group (MRMG); Financial and Model Risk",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Head of Financial and Model Risk • SVP, Model Risk Management",
                named_leaders="Elizabeth Mays; Amy Wierenga; John Straka",
                notes_sources="The structure features a CMRO, with a broader \"Head of Financial and Model Risk\" role suggesting a potential combination of risk disciplines at a very senior level."
            ),
            RawBankData(
                bank_name="Truist Financial",
                asset_rank="9",
                mrm_department_names="Model Risk Management; AI Risk Oversight",
                key_leadership_titles="• Head of Model Risk Management • Head of AI Risk Oversight",
                named_leaders="(Unnamed)",
                notes_sources="Truist provides a clear example of a new, specialized oversight function for AI, distinct from but collaborative with traditional MRM."
            ),
            RawBankData(
                bank_name="TD Bank, N.A.",
                asset_rank="10",
                mrm_department_names="Model Risk Management; Office of the Chief Risk Officer",
                key_leadership_titles="• Head of Model Risk Governance and Controls • Model Risk Management Executive",
                named_leaders="Rhea Rajwani; Christophe Rougeaux",
                notes_sources="A dedicated \"Head of Model Risk Governance and Controls\" role highlights the importance of the framework and its enforcement within the broader risk organization."
            ),
            RawBankData(
                bank_name="Capital One Financial",
                asset_rank="11",
                mrm_department_names="Model Risk Audit; Model Risk Management",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Principal Quantitative Analyst, Model Risk Audit",
                named_leaders="Evan Sekeris (former CMRO)",
                notes_sources="Capital One has a distinct \"Model Risk Audit\" function, likely part of the Third Line, working alongside the Second Line MRM team."
            ),
            RawBankData(
                bank_name="The Bank of New York Mellon",
                asset_rank="13",
                mrm_department_names="Model Risk Management",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Vice President, Model Risk",
                named_leaders="Dominic S.",
                notes_sources="The structure includes a CMRO and VP-level roles responsible for executing the firm's validation standards."
            ),
            RawBankData(
                bank_name="State Street Corporation",
                asset_rank="14",
                mrm_department_names="Model Risk Management; Centralized Modelling & Analytics Team",
                key_leadership_titles="• Executive Vice President, Chief Financial Risk Officer • Managing Director, Global Head of SSGA Model Risk • MD, Head of Centralized Modelling & Analytics Team",
                named_leaders="Steven Umlauf; Julia Litvinova; Katherine Zhang",
                notes_sources="State Street shows a complex structure with a senior executive (Umlauf) whose responsibilities include risk modeling, and specific heads for model risk within asset management (SSGA) and a centralized analytics team."
            ),
            RawBankData(
                bank_name="BMO Financial Corp.",
                asset_rank="15",
                mrm_department_names="Model Risk Management; Structural Market Risk Oversight",
                key_leadership_titles="• Head, Model Risk Management • Senior Manager: Data Analytics & AI Risk",
                named_leaders="Beizhen Lei; Aleksandr Kolomiets",
                notes_sources="BMO has a clear Head of MRM and shows specialization with a senior manager focused on the emerging area of AI risk."
            ),
            RawBankData(
                bank_name="HSBC Bank USA",
                asset_rank="17",
                mrm_department_names="Model Risk Management (MRM)",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) (Global) • EVP - Head of US Model Risk Management",
                named_leaders="Manan Rawal (US Head)",
                notes_sources="HSBC demonstrates a global functional model, with a global CMRO setting policy and a dedicated EVP-level head for the US entity responsible for local implementation."
            ),
            RawBankData(
                bank_name="Citizens Financial Group",
                asset_rank="20",
                mrm_department_names="Model Risk Management & Validation",
                key_leadership_titles="• Executive Vice President, Head of Credit Review • Executive, Vice President (Risk Models)",
                named_leaders="Saad P. Aslam; Steve Boras",
                notes_sources="The combined title \"Model Risk Management & Validation\" is used. Leadership includes senior executives at the EVP level."
            ),
            RawBankData(
                bank_name="Fifth Third Bancorp",
                asset_rank="21",
                mrm_department_names="Model Risk Management (MRM)",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Head of Model Governance",
                named_leaders="Rafic Fahs; Lee Medoff",
                notes_sources="A clear CMRO structure is in place, with distinct senior roles for overall leadership and for the specific function of governance."
            ),
            RawBankData(
                bank_name="M&T Bank",
                asset_rank="23",
                mrm_department_names="Model Risk Management",
                key_leadership_titles="• Executive Vice President, Head of Model Risk Management",
                named_leaders="Rhea R.",
                notes_sources="A senior EVP-level leader heads the MRM function, indicating significant stature within the organization."
            ),
            RawBankData(
                bank_name="KeyBank",
                asset_rank="27",
                mrm_department_names="Model Risk Management",
                key_leadership_titles="• Chief Model Risk Officer (CMRO) • Senior Model Validation Director",
                named_leaders="(Unnamed)",
                notes_sources="The structure clearly identifies a CMRO, to whom senior directors for specific areas (e.g., Fraud Models) report, showing a hierarchical and specialized team."
            ),
            RawBankData(
                bank_name="Ally Financial",
                asset_rank="26",
                mrm_department_names="Model Validation Risk; Risk Analytics",
                key_leadership_titles="• Senior Director, Model Validation Risk • Financial Model Risk Executive",
                named_leaders="Liming Brotcke; Bradley Currell",
                notes_sources="Ally's titles suggest a strong focus on the validation component of MRM, with senior director and executive-level leadership."
            ),
            RawBankData(
                bank_name="Regions Bank",
                asset_rank="32",
                mrm_department_names="Model Risk Management & Validation",
                key_leadership_titles="• Head of the Model Risk Management & Validation, SVP",
                named_leaders="Jacob Kosoff",
                notes_sources="Regions uses a combined title for the department, which is led by a Senior Vice President."
            ),
            RawBankData(
                bank_name="Charles Schwab",
                asset_rank="12",
                mrm_department_names="Enterprise and Operational Risk Management; Model Risk Oversight (MRO)",
                key_leadership_titles="• Managing Director, Enterprise and Operational Risk Management • Managing Director, Model Risk Management",
                named_leaders="Stuart J. Strepman; Vaughn Zakarian",
                notes_sources="Schwab's structure appears to integrate MRM within a broader Enterprise Risk function while also having dedicated MRM leadership."
            )
        ]
    
    def _parse_single_bank(self, raw_bank: RawBankData) -> BankInfo:
        """Parse a single bank's raw data into structured format"""
        # Parse basic information
        asset_rank = int(raw_bank.asset_rank) if raw_bank.asset_rank.isdigit() else None
        
        # Parse MRM departments
        mrm_departments = self._parse_mrm_departments(raw_bank.mrm_department_names)
        
        # Parse leadership information
        leadership = self._parse_leadership(raw_bank.key_leadership_titles, raw_bank.named_leaders)
        
        # Determine data sources
        data_sources = [DataSource.MANUAL_ENTRY]
        source_urls = []
        
        # Calculate initial scores
        completeness_score = self._calculate_completeness_score(raw_bank)
        confidence_score = 0.8  # High confidence for manually curated data
        
        return BankInfo(
            bank_name=raw_bank.bank_name,
            asset_rank=asset_rank,
            mrm_departments=mrm_departments,
            leadership=leadership,
            completeness_score=completeness_score,
            confidence_score=confidence_score,
            primary_source=DataSource.MANUAL_ENTRY,
            data_sources=data_sources,
            source_urls=source_urls,
            notes=raw_bank.notes_sources,
            tags=["existing_dataset", "high_quality"],
            research_priority=3,  # Lower priority since already researched
            last_updated=datetime.utcnow()
        )
    
    def _parse_mrm_departments(self, dept_names: str) -> List[MRMDepartmentInfo]:
        """Parse MRM department names into structured format"""
        departments = []
        
        # Split by semicolon or common separators
        dept_list = re.split(r'[;,]|(?:\s*•\s*)', dept_names)
        dept_list = [dept.strip() for dept in dept_list if dept.strip()]
        
        for dept_name in dept_list:
            # Clean up department name
            dept_name = re.sub(r'^\s*[•\-\*]\s*', '', dept_name)
            dept_name = dept_name.strip()
            
            if dept_name:
                # Extract key functions from department name
                key_functions = self._extract_key_functions(dept_name)
                
                department = MRMDepartmentInfo(
                    department_name=dept_name,
                    key_functions=key_functions,
                    confidence_score=0.8,
                    source=DataSource.MANUAL_ENTRY,
                    last_updated=datetime.utcnow()
                )
                departments.append(department)
        
        return departments
    
    def _parse_leadership(self, titles: str, names: str) -> List[LeadershipInfo]:
        """Parse leadership titles and names into structured format"""
        leadership = []
        
        # Parse titles
        title_list = re.split(r'[;]|(?:\s*•\s*)', titles)
        title_list = [title.strip() for title in title_list if title.strip()]
        
        # Parse names
        name_list = re.split(r'[;,]', names) if names and names != "(Unnamed)" else []
        name_list = [name.strip() for name in name_list if name.strip()]
        
        # Match titles with names where possible
        for i, title in enumerate(title_list):
            # Clean up title
            title = re.sub(r'^\s*[•\-\*]\s*', '', title)
            title = title.strip()
            
            if not title:
                continue
            
            # Try to find corresponding name
            name = None
            if i < len(name_list):
                name = name_list[i]
                # Clean up name (remove parenthetical info)
                name = re.sub(r'\s*\([^)]*\)', '', name).strip()
            
            # Determine confidence based on title specificity
            confidence = self._calculate_title_confidence(title)
            
            leader = LeadershipInfo(
                name=name,
                title=title,
                confidence_score=confidence,
                source=DataSource.MANUAL_ENTRY,
                last_verified=datetime.utcnow()
            )
            leadership.append(leader)
        
        # Add any remaining names without specific titles
        for i in range(len(title_list), len(name_list)):
            name = name_list[i]
            name = re.sub(r'\s*\([^)]*\)', '', name).strip()
            
            if name:
                leader = LeadershipInfo(
                    name=name,
                    title="Model Risk Management (Role TBD)",
                    confidence_score=0.6,
                    source=DataSource.MANUAL_ENTRY,
                    last_verified=datetime.utcnow()
                )
                leadership.append(leader)
        
        return leadership
    
    def _extract_key_functions(self, dept_name: str) -> List[str]:
        """Extract key functions from department name"""
        functions = []
        dept_lower = dept_name.lower()
        
        function_keywords = {
            "governance": ["governance", "oversight", "controls"],
            "validation": ["validation", "review", "audit"],
            "risk_management": ["risk management", "risk oversight"],
            "analytics": ["analytics", "quantitative", "modeling"],
            "ai_ml": ["ai", "artificial intelligence", "machine learning", "ml"],
            "credit_risk": ["credit risk", "credit modeling"],
            "market_risk": ["market risk", "trading risk"],
            "operational_risk": ["operational risk", "op risk"]
        }
        
        for function, keywords in function_keywords.items():
            if any(keyword in dept_lower for keyword in keywords):
                functions.append(function.replace("_", " ").title())
        
        return functions
    
    def _calculate_title_confidence(self, title: str) -> float:
        """Calculate confidence score based on title specificity"""
        title_lower = title.lower()
        
        # High confidence for specific MRM titles
        high_confidence_patterns = [
            "chief model risk officer", "cmro", "head of model risk",
            "director of model risk", "model risk officer"
        ]
        
        if any(pattern in title_lower for pattern in high_confidence_patterns):
            return 0.9
        
        # Medium confidence for related titles
        medium_confidence_patterns = [
            "model risk", "risk management", "quantitative risk"
        ]
        
        if any(pattern in title_lower for pattern in medium_confidence_patterns):
            return 0.7
        
        # Lower confidence for general titles
        return 0.5
    
    def _calculate_completeness_score(self, raw_bank: RawBankData) -> float:
        """Calculate completeness score for raw bank data"""
        total_fields = 6
        completed_fields = 0
        
        if raw_bank.bank_name: completed_fields += 1
        if raw_bank.asset_rank: completed_fields += 1
        if raw_bank.mrm_department_names: completed_fields += 1
        if raw_bank.key_leadership_titles: completed_fields += 1
        if raw_bank.named_leaders and raw_bank.named_leaders != "(Unnamed)": completed_fields += 1
        if raw_bank.notes_sources: completed_fields += 1
        
        return completed_fields / total_fields
    
    def import_existing_data(self) -> int:
        """Import all existing data into the database"""
        banks = self.parse_existing_dataset()
        imported_count = 0
        
        for bank in banks:
            try:
                bank_id = db_manager.add_bank(bank)
                imported_count += 1
                logger.info(f"Imported bank: {bank.bank_name} (ID: {bank_id})")
            except Exception as e:
                logger.error(f"Error importing bank {bank.bank_name}: {e}")
                continue
        
        logger.info(f"Successfully imported {imported_count} banks from existing dataset")
        return imported_count

# Global parser instance
data_parser = DataParser()