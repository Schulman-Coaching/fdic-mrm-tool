"""
Test script to validate the FDIC MRM Tool functionality
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        import config
        print("✓ Config module imported successfully")
        
        import data_models
        print("✓ Data models imported successfully")
        
        import database
        print("✓ Database module imported successfully")
        
        import data_parser
        print("✓ Data parser imported successfully")
        
        import fdic_collector
        print("✓ FDIC collector imported successfully")
        
        import export_handler
        print("✓ Export handler imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_data_models():
    """Test data model creation and validation"""
    print("\nTesting data models...")
    
    try:
        from data_models import BankInfo, LeadershipInfo, MRMDepartmentInfo, DataSource
        from datetime import datetime
        
        # Test leadership info
        leader = LeadershipInfo(
            name="John Doe",
            title="Chief Model Risk Officer",
            confidence_score=0.9,
            source=DataSource.MANUAL_ENTRY
        )
        print("✓ Leadership model created successfully")
        
        # Test MRM department info
        dept = MRMDepartmentInfo(
            department_name="Model Risk Management",
            key_functions=["Validation", "Governance"],
            confidence_score=0.8,
            source=DataSource.MANUAL_ENTRY
        )
        print("✓ MRM Department model created successfully")
        
        # Test bank info
        bank = BankInfo(
            bank_name="Test Bank",
            asset_rank=1,
            total_assets=1000000.0,
            mrm_departments=[dept],
            leadership=[leader]
        )
        print("✓ Bank model created successfully")
        print(f"  - Completeness score: {bank.completeness_score:.2f}")
        print(f"  - Size category: {bank.size_category}")
        
        return True
    except Exception as e:
        print(f"✗ Data model test failed: {e}")
        return False

def test_database():
    """Test database operations"""
    print("\nTesting database operations...")
    
    try:
        from database import DatabaseManager
        from data_models import BankInfo, DataSource
        
        # Create test database
        db = DatabaseManager("sqlite:///test_fdic.db")
        print("✓ Database manager created successfully")
        
        # Test database stats (should work even with empty DB)
        stats = db.get_database_stats()
        print("✓ Database stats retrieved successfully")
        print(f"  - Total banks: {stats['total_banks']}")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

def test_data_parser():
    """Test data parsing functionality"""
    print("\nTesting data parser...")
    
    try:
        from data_parser import DataParser
        
        parser = DataParser()
        print("✓ Data parser created successfully")
        
        # Test parsing existing dataset
        banks = parser.parse_existing_dataset()
        print(f"✓ Parsed {len(banks)} banks from existing dataset")
        
        if banks:
            sample_bank = banks[0]
            print(f"  - Sample bank: {sample_bank.bank_name}")
            print(f"  - MRM departments: {len(sample_bank.mrm_departments)}")
            print(f"  - Leadership: {len(sample_bank.leadership)}")
            print(f"  - Completeness: {sample_bank.completeness_score:.2f}")
        
        return True
    except Exception as e:
        print(f"✗ Data parser test failed: {e}")
        return False

def test_export_handler():
    """Test export functionality"""
    print("\nTesting export handler...")
    
    try:
        from export_handler import ExportHandler
        from data_parser import DataParser
        
        # Get sample data
        parser = DataParser()
        banks = parser.parse_existing_dataset()[:5]  # Just test with 5 banks
        
        exporter = ExportHandler()
        print("✓ Export handler created successfully")
        
        # Test CSV export
        csv_file = exporter.export_to_csv(banks, "test_export.csv")
        print(f"✓ CSV export successful: {csv_file}")
        
        # Test Excel export
        excel_file = exporter.export_to_excel(banks, "test_export.xlsx")
        print(f"✓ Excel export successful: {excel_file}")
        
        return True
    except Exception as e:
        print(f"✗ Export test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("FDIC MRM Tool - System Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_data_models,
        test_database,
        test_data_parser,
        test_export_handler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Initialize system: python main.py init")
        print("3. Collect FDIC data: python main.py collect")
        print("4. Export data: python main.py export")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
    
    return passed == total

if __name__ == "__main__":
    main()