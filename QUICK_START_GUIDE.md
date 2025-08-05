# FDIC MRM Tool - Quick Start Guide for $25M-$50B Banks

## Prerequisites
Ensure Python 3.8+ is installed and available in your PATH.

## Step-by-Step Data Collection Process

### 1. Navigate to Project Directory
```bash
cd "C:\Users\elie\Development-Projects\fdic-mrm-tool"
```

### 2. Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

### 3. Initialize the System (First Time Only)
```bash
python main.py init
```
This will:
- Create the database
- Import the existing 22 high-quality banks
- Set up the foundation for data collection

### 4. Collect Banks in $25M-$50B Asset Range
```bash
python main.py collect-range --min-assets 25 --max-assets 50000 --limit 100
```
This will:
- Query FDIC API for banks with assets between $25M and $50B
- Add up to 100 banks to the database
- Create research tasks for each bank
- Provide progress indicators and statistics

### 5. Extract Comprehensive MRM Data
```bash
python main.py extract-mrm --incomplete-only --batch-size 5
```
This will:
- Process banks with incomplete MRM data
- Use LinkedIn integration with your credentials (elie@cohortlearninglabs.org)
- Search for MRM professionals at each bank
- Extract titles, names, and LinkedIn profiles
- Update database with new findings
- Process in batches of 5 to respect API limits

### 6. Generate Professional Report
```bash
python main.py export --format xlsx
```
This will create a comprehensive Excel report with:
- Summary sheet with all banks
- Detailed bank information
- Individual leadership records
- MRM department details
- Research task tracking
- Statistical analysis

## Alternative: Use Windows Batch Runner

If you prefer, you can use the batch file:
```bash
run_tool.bat init
run_tool.bat collect-range
run_tool.bat extract-mrm
run_tool.bat export
```

## Expected Results

After running these commands, you will have:
- **100+ banks** in the $25M-$50B asset range
- **Comprehensive MRM data** extracted from LinkedIn and other sources
- **Professional Excel reports** ready for analysis
- **Research tasks** for any remaining data gaps

## Monitoring Progress

Check your progress anytime with:
```bash
python main.py stats
```

Search for specific banks:
```bash
python main.py search --incomplete --limit 20
```

View detailed information for any bank:
```bash
python main.py detail "Bank Name Here"
```

## LinkedIn Integration Benefits

With your LinkedIn credentials configured, the system will automatically:
- Search for MRM professionals at each bank
- Extract current job titles and names
- Capture LinkedIn profile URLs for contact purposes
- Identify career movements and organizational changes
- Update completeness scores based on new data

## Troubleshooting

If you encounter any issues:
1. Ensure Python 3.8+ is installed
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Verify LinkedIn credentials in the `.env` file
4. Check logs in the `logs/` directory for detailed error information

## Next Steps

Once data collection is complete, you can:
- Export data for analysis
- Set up automated scheduling for regular updates
- Expand to additional asset ranges
- Integrate with other data sources

The system is designed to be scalable and can handle thousands of banks with the same systematic approach.