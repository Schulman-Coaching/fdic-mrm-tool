"""
Export functionality for FDIC MRM data to CSV and Excel formats
"""
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from config import settings
from data_models import BankInfo, LeadershipInfo, MRMDepartmentInfo
from database import db_manager

logger = logging.getLogger(__name__)

class ExportHandler:
    """Handles data export to various formats"""
    
    def __init__(self):
        self.exports_dir = settings.EXPORTS_DIR
        self.exports_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_csv(self, 
                     banks: List[BankInfo] = None,
                     filename: str = None,
                     include_detailed: bool = True) -> str:
        """Export bank data to CSV format"""
        try:
            if banks is None:
                banks = db_manager.get_all_banks()
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fdic_mrm_data_{timestamp}.csv"
            
            filepath = self.exports_dir / filename
            
            # Prepare data for export
            export_data = []
            
            for bank in banks:
                # Basic bank information
                base_row = {
                    'Bank Name': bank.bank_name,
                    'Asset Rank': bank.asset_rank,
                    'Total Assets (Millions)': bank.total_assets,
                    'Size Category': bank.size_category.value if bank.size_category else '',
                    'Headquarters City': bank.headquarters_city,
                    'Headquarters State': bank.headquarters_state,
                    'FDIC CERT ID': bank.fdic_cert_id,
                    'RSSD ID': bank.rssd_id,
                }
                
                if include_detailed:
                    # MRM Department information
                    mrm_dept_names = '; '.join([dept.department_name for dept in bank.mrm_departments])
                    mrm_functions = '; '.join([
                        f"{dept.department_name}: {', '.join(dept.key_functions)}" 
                        for dept in bank.mrm_departments if dept.key_functions
                    ])
                    
                    # Leadership information
                    leadership_titles = '; '.join([
                        leader.title for leader in bank.leadership if leader.title
                    ])
                    leadership_names = '; '.join([
                        f"{leader.name} ({leader.title})" if leader.name and leader.title
                        else leader.name or leader.title or "Unknown"
                        for leader in bank.leadership
                    ])
                    
                    base_row.update({
                        'MRM Department Name(s)': mrm_dept_names,
                        'MRM Key Functions': mrm_functions,
                        'Key Leadership Title(s)': leadership_titles,
                        'Named Leader(s)': leadership_names,
                        'Completeness Score': round(bank.completeness_score, 2),
                        'Confidence Score': round(bank.confidence_score, 2),
                        'Quality Status': bank.quality_status.value,
                        'Primary Source': bank.primary_source.value,
                        'Data Sources': '; '.join([source.value for source in bank.data_sources]),
                        'Last Updated': bank.last_updated.strftime('%Y-%m-%d %H:%M:%S') if bank.last_updated else '',
                        'Last Verified': bank.last_verified.strftime('%Y-%m-%d %H:%M:%S') if bank.last_verified else '',
                        'Research Priority': bank.research_priority,
                        'Tags': '; '.join(bank.tags),
                        'Notes / Sources': bank.notes or ''
                    })
                
                export_data.append(base_row)
            
            # Create DataFrame and export
            df = pd.DataFrame(export_data)
            df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Exported {len(banks)} banks to CSV: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            raise
    
    def export_to_excel(self, 
                       banks: List[BankInfo] = None,
                       filename: str = None,
                       include_sheets: List[str] = None) -> str:
        """Export bank data to Excel format with multiple sheets"""
        try:
            if banks is None:
                banks = db_manager.get_all_banks()
            
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"fdic_mrm_data_{timestamp}.xlsx"
            
            filepath = self.exports_dir / filename
            
            if include_sheets is None:
                include_sheets = ['summary', 'detailed', 'leadership', 'departments', 'research_tasks']
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Summary sheet
                if 'summary' in include_sheets:
                    summary_data = self._prepare_summary_data(banks)
                    summary_df = pd.DataFrame(summary_data)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed sheet
                if 'detailed' in include_sheets:
                    detailed_data = self._prepare_detailed_data(banks)
                    detailed_df = pd.DataFrame(detailed_data)
                    detailed_df.to_excel(writer, sheet_name='Detailed', index=False)
                
                # Leadership sheet
                if 'leadership' in include_sheets:
                    leadership_data = self._prepare_leadership_data(banks)
                    leadership_df = pd.DataFrame(leadership_data)
                    leadership_df.to_excel(writer, sheet_name='Leadership', index=False)
                
                # Departments sheet
                if 'departments' in include_sheets:
                    dept_data = self._prepare_departments_data(banks)
                    dept_df = pd.DataFrame(dept_data)
                    dept_df.to_excel(writer, sheet_name='Departments', index=False)
                
                # Research tasks sheet
                if 'research_tasks' in include_sheets:
                    tasks_data = self._prepare_research_tasks_data()
                    tasks_df = pd.DataFrame(tasks_data)
                    tasks_df.to_excel(writer, sheet_name='Research Tasks', index=False)
                
                # Statistics sheet
                if 'statistics' in include_sheets:
                    stats_data = self._prepare_statistics_data(banks)
                    stats_df = pd.DataFrame(stats_data)
                    stats_df.to_excel(writer, sheet_name='Statistics', index=False)
            
            logger.info(f"Exported {len(banks)} banks to Excel: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            raise
    
    def _prepare_summary_data(self, banks: List[BankInfo]) -> List[Dict[str, Any]]:
        """Prepare summary data for export"""
        summary_data = []
        
        for bank in banks:
            summary_data.append({
                'Bank Name': bank.bank_name,
                'Asset Rank': bank.asset_rank,
                'Total Assets (Millions)': bank.total_assets,
                'Size Category': bank.size_category.value if bank.size_category else '',
                'State': bank.headquarters_state,
                'Has MRM Data': 'Yes' if bank.mrm_departments else 'No',
                'Leadership Count': len(bank.leadership),
                'Completeness Score': round(bank.completeness_score, 2),
                'Quality Status': bank.quality_status.value,
                'Last Updated': bank.last_updated.strftime('%Y-%m-%d') if bank.last_updated else ''
            })
        
        return summary_data
    
    def _prepare_detailed_data(self, banks: List[BankInfo]) -> List[Dict[str, Any]]:
        """Prepare detailed data for export"""
        detailed_data = []
        
        for bank in banks:
            # MRM Department information
            mrm_dept_names = '; '.join([dept.department_name for dept in bank.mrm_departments])
            mrm_functions = '; '.join([
                f"{dept.department_name}: {', '.join(dept.key_functions)}" 
                for dept in bank.mrm_departments if dept.key_functions
            ])
            
            # Leadership information
            leadership_summary = '; '.join([
                f"{leader.name or 'Unknown'} - {leader.title or 'Unknown Role'}"
                for leader in bank.leadership
            ])
            
            detailed_data.append({
                'Bank Name': bank.bank_name,
                'Asset Rank': bank.asset_rank,
                'Total Assets (Millions)': bank.total_assets,
                'Size Category': bank.size_category.value if bank.size_category else '',
                'Headquarters': f"{bank.headquarters_city}, {bank.headquarters_state}",
                'FDIC CERT ID': bank.fdic_cert_id,
                'RSSD ID': bank.rssd_id,
                'MRM Department Name(s)': mrm_dept_names,
                'MRM Key Functions': mrm_functions,
                'Leadership Summary': leadership_summary,
                'Completeness Score': round(bank.completeness_score, 2),
                'Confidence Score': round(bank.confidence_score, 2),
                'Quality Status': bank.quality_status.value,
                'Primary Source': bank.primary_source.value,
                'Data Sources': '; '.join([source.value for source in bank.data_sources]),
                'Source URLs': '; '.join(bank.source_urls),
                'Last Updated': bank.last_updated.strftime('%Y-%m-%d %H:%M:%S') if bank.last_updated else '',
                'Last Verified': bank.last_verified.strftime('%Y-%m-%d %H:%M:%S') if bank.last_verified else '',
                'Research Priority': bank.research_priority,
                'Tags': '; '.join(bank.tags),
                'Notes': bank.notes or ''
            })
        
        return detailed_data
    
    def _prepare_leadership_data(self, banks: List[BankInfo]) -> List[Dict[str, Any]]:
        """Prepare leadership data for export"""
        leadership_data = []
        
        for bank in banks:
            for leader in bank.leadership:
                leadership_data.append({
                    'Bank Name': bank.bank_name,
                    'Asset Rank': bank.asset_rank,
                    'Leader Name': leader.name or 'Unknown',
                    'Title': leader.title or 'Unknown',
                    'Department': leader.department or '',
                    'LinkedIn URL': leader.linkedin_url or '',
                    'Email': leader.email or '',
                    'Phone': leader.phone or '',
                    'Start Date': leader.start_date.strftime('%Y-%m-%d') if leader.start_date else '',
                    'End Date': leader.end_date.strftime('%Y-%m-%d') if leader.end_date else '',
                    'Confidence Score': round(leader.confidence_score, 2),
                    'Source': leader.source.value,
                    'Last Verified': leader.last_verified.strftime('%Y-%m-%d') if leader.last_verified else '',
                    'Notes': leader.notes or ''
                })
        
        return leadership_data
    
    def _prepare_departments_data(self, banks: List[BankInfo]) -> List[Dict[str, Any]]:
        """Prepare departments data for export"""
        dept_data = []
        
        for bank in banks:
            for dept in bank.mrm_departments:
                dept_data.append({
                    'Bank Name': bank.bank_name,
                    'Asset Rank': bank.asset_rank,
                    'Department Name': dept.department_name,
                    'Parent Organization': dept.parent_organization or '',
                    'Reporting Structure': dept.reporting_structure or '',
                    'Team Size': dept.team_size or '',
                    'Budget': dept.budget or '',
                    'Established Date': dept.established_date.strftime('%Y-%m-%d') if dept.established_date else '',
                    'Key Functions': '; '.join(dept.key_functions),
                    'Technologies Used': '; '.join(dept.technologies_used),
                    'Confidence Score': round(dept.confidence_score, 2),
                    'Source': dept.source.value,
                    'Last Updated': dept.last_updated.strftime('%Y-%m-%d') if dept.last_updated else ''
                })
        
        return dept_data
    
    def _prepare_research_tasks_data(self) -> List[Dict[str, Any]]:
        """Prepare research tasks data for export"""
        tasks = db_manager.get_pending_research_tasks(limit=1000)
        tasks_data = []
        
        for task in tasks:
            # Get bank name
            bank = db_manager.get_bank(task.bank_id)
            bank_name = bank.bank_name if bank else f"Bank ID {task.bank_id}"
            
            tasks_data.append({
                'Bank Name': bank_name,
                'Task Type': task.task_type,
                'Priority': task.priority,
                'Status': task.status,
                'Assigned To': task.assigned_to or 'Unassigned',
                'Created Date': task.created_at.strftime('%Y-%m-%d') if task.created_at else '',
                'Due Date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                'Completed Date': task.completed_at.strftime('%Y-%m-%d') if task.completed_at else '',
                'Description': task.description or '',
                'Findings': task.findings or '',
                'Sources Checked': '; '.join(task.sources_checked or []),
                'Notes': task.notes or ''
            })
        
        return tasks_data
    
    def _prepare_statistics_data(self, banks: List[BankInfo]) -> List[Dict[str, Any]]:
        """Prepare statistics data for export"""
        stats = db_manager.get_database_stats()
        
        # Calculate additional statistics
        total_banks = len(banks)
        banks_with_leadership = len([b for b in banks if b.leadership])
        banks_with_departments = len([b for b in banks if b.mrm_departments])
        
        avg_completeness = sum(b.completeness_score for b in banks) / total_banks if total_banks > 0 else 0
        avg_confidence = sum(b.confidence_score for b in banks) / total_banks if total_banks > 0 else 0
        
        # Size category distribution
        size_distribution = {}
        for bank in banks:
            category = bank.size_category.value if bank.size_category else 'unknown'
            size_distribution[category] = size_distribution.get(category, 0) + 1
        
        # Quality status distribution
        quality_distribution = {}
        for bank in banks:
            status = bank.quality_status.value
            quality_distribution[status] = quality_distribution.get(status, 0) + 1
        
        statistics_data = [
            {'Metric': 'Total Banks', 'Value': total_banks},
            {'Metric': 'Banks with MRM Data', 'Value': stats['banks_with_mrm_data']},
            {'Metric': 'Banks with Leadership Info', 'Value': banks_with_leadership},
            {'Metric': 'Banks with Department Info', 'Value': banks_with_departments},
            {'Metric': 'MRM Coverage Percentage', 'Value': f"{stats['mrm_coverage_percentage']:.1f}%"},
            {'Metric': 'Average Completeness Score', 'Value': f"{avg_completeness:.2f}"},
            {'Metric': 'Average Confidence Score', 'Value': f"{avg_confidence:.2f}"},
            {'Metric': 'Pending Research Tasks', 'Value': stats['pending_research_tasks']},
            {'Metric': 'Recent Collection Activities', 'Value': stats['recent_collection_activities']},
            {'Metric': '', 'Value': ''},  # Separator
            {'Metric': 'Size Distribution:', 'Value': ''},
        ]
        
        for category, count in size_distribution.items():
            statistics_data.append({'Metric': f"  {category.title()}", 'Value': count})
        
        statistics_data.append({'Metric': '', 'Value': ''})  # Separator
        statistics_data.append({'Metric': 'Quality Distribution:', 'Value': ''})
        
        for status, count in quality_distribution.items():
            statistics_data.append({'Metric': f"  {status.title()}", 'Value': count})
        
        return statistics_data
    
    def export_research_template(self, filename: str = None) -> str:
        """Export a research template for manual data collection"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mrm_research_template_{timestamp}.xlsx"
            
            filepath = self.exports_dir / filename
            
            # Get banks needing research
            banks_needing_research = db_manager.get_banks_needing_research(50)
            
            template_data = []
            for bank in banks_needing_research:
                template_data.append({
                    'Bank Name': bank.bank_name,
                    'Asset Rank': bank.asset_rank,
                    'Current Completeness': f"{bank.completeness_score:.1%}",
                    'MRM Department Name(s)': '',  # To be filled
                    'Key Leadership Title(s)': '',  # To be filled
                    'Named Leader(s)': '',  # To be filled
                    'Department Functions': '',  # To be filled
                    'Team Size (if available)': '',  # To be filled
                    'Reporting Structure': '',  # To be filled
                    'Source URLs': '',  # To be filled
                    'Notes': '',  # To be filled
                    'Research Status': 'Pending',
                    'Researcher': '',  # To be filled
                    'Date Completed': ''  # To be filled
                })
            
            df = pd.DataFrame(template_data)
            df.to_excel(filepath, index=False)
            
            logger.info(f"Exported research template with {len(banks_needing_research)} banks: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting research template: {e}")
            raise

# Global export handler instance
export_handler = ExportHandler()