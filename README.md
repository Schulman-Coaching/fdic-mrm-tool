# FDIC MRM Data Collection Tool

An automated Python-based system for collecting, managing, and analyzing Model Risk Management (MRM) data for FDIC banks.

## Features

- **Automated Data Collection**: Integrates with FDIC APIs to collect official bank data
- **Intelligent Data Processing**: Uses NLP and AI for extracting MRM information from various sources
- **Comprehensive Database**: Structured storage of bank information, MRM departments, and leadership data
- **Export Capabilities**: Professional CSV and Excel exports with multiple sheets and formatting
- **Research Workflow**: Templates and tracking for manual data collection efforts
- **Quality Monitoring**: Data completeness and confidence scoring with quality alerts

## Quick Start

### Installation

1. Clone or download the project files
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. LinkedIn credentials are already configured in the `.env` file for automated data collection

**LinkedIn Integration Benefits:**
- **Current Leadership Data**: Automatically finds up-to-date MRM professionals and their current titles
- **Contact Information**: Extracts LinkedIn profiles, which often lead to email addresses and phone numbers
- **Career History**: Tracks leadership movements between banks and role changes
- **Network Analysis**: Identifies connections between MRM professionals across different institutions
- **Real-time Updates**: LinkedIn profiles are typically more current than corporate websites or SEC filings

### Basic Usage

1. **Initialize the system and import existing data:**
```bash
python main.py init
```

2. **Collect top 100 FDIC banks:**
```bash
python main.py collect
```

3. **Export data to Excel:**
```bash
python main.py export --format xlsx
```

4. **Search for specific banks:**
```bash
python main.py search --name "JPMorgan" --limit 5
```

5. **Collect LinkedIn data for a specific bank:**
```bash
python main.py linkedin "JPMorgan Chase & Co."
```

6. **View database statistics:**
```bash
python main.py stats
```

## Command Reference

### Core Commands

- `init` - Initialize database and import existing 22-bank dataset
- `collect` - Collect top FDIC banks and populate database
- `export` - Export bank data to CSV or Excel formats
- `search` - Search and filter bank information
- `stats` - Display database statistics and distributions
- `detail <bank_name>` - Show detailed information for a specific bank
- `linkedin <bank_name>` - Collect MRM leadership data from LinkedIn
- `tasks` - Show pending research tasks
- `template` - Generate research template for manual data collection

### Export Options

```bash
# Export to CSV
python main.py export --format csv

# Export to Excel with custom filename
python main.py export --format xlsx --filename my_export.xlsx

# Export only banks needing research
python main.py export --filter-incomplete
```

### Search Options

```bash
# Search by name
python main.py search --name "Bank of America"

# Filter by asset rank range
python main.py search --rank-min 1 --rank-max 10

# Filter by state and size
python main.py search --state "NY" --size large

# Show only incomplete data
python main.py search --incomplete --limit 50

# Collect LinkedIn data for specific banks
python main.py linkedin "Bank of America"
python main.py linkedin "Wells Fargo & Co." --limit 15
```

## Data Structure

### Bank Information
- Basic bank details (name, assets, location, FDIC identifiers)
- Asset ranking and size categorization
- Data quality metrics and source tracking

### MRM Departments
- Department names and organizational structure
- Key functions and responsibilities
- Team size and budget information (when available)
- Technology stack and tools used

### Leadership Information
- Names, titles, and contact information
- Department assignments and reporting structure
- Employment dates and career history
- Confidence scoring for data reliability

### Data Quality Tracking
- Completeness scores (0-100%)
- Confidence levels for each data point
- Source attribution and verification dates
- Research priority rankings

## File Structure

```
fdic_mrm_tool/
├── config.py              # Configuration and settings
├── data_models.py          # Pydantic models and database schemas
├── database.py             # Database operations and management
├── data_parser.py          # Parser for existing dataset
├── fdic_collector.py       # FDIC API integration
├── export_handler.py       # CSV/Excel export functionality
├── main.py                 # CLI interface
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data/                  # Data storage directory
├── exports/               # Export output directory
├── logs/                  # Application logs
└── cache/                 # Temporary cache files
```

## Data Sources

### Primary Sources
1. **FDIC API** - Official bank data, assets, locations
2. **SEC EDGAR** - Annual reports, proxy statements, leadership information
3. **Bank Websites** - Career pages, organizational charts, leadership bios
4. **LinkedIn** - Professional profiles and job titles
5. **Regulatory Filings** - OCC, Federal Reserve, state banking regulators

### Data Quality Levels
- **Excellent** (90%+ complete, high confidence)
- **Good** (70-90% complete, medium-high confidence)
- **Fair** (50-70% complete, medium confidence)
- **Poor** (<50% complete, low confidence)
- **Unknown** (not yet assessed)

## Bank Size Categories

- **Mega Banks**: >$500B in assets
- **Large Banks**: $100B-$500B in assets
- **Regional Banks**: $10B-$100B in assets
- **Community Banks**: $1B-$10B in assets
- **Small Banks**: <$1B in assets

## Export Formats

### CSV Export
Single file with all bank data in tabular format, suitable for:
- Data analysis and filtering
- Import into other systems
- Quick sharing and collaboration

### Excel Export (Multiple Sheets)
- **Summary**: High-level overview of all banks
- **Detailed**: Complete bank information with all fields
- **Leadership**: Individual leadership records
- **Departments**: MRM department details
- **Research Tasks**: Pending research activities
- **Statistics**: Data quality and distribution metrics

## Research Workflow

### Automated Research Tasks
The system automatically creates research tasks for:
- Banks with low completeness scores
- Banks with outdated information
- High-priority banks missing MRM data

### Manual Research Process
1. Generate research template: `python main.py template`
2. Fill in missing information using provided sources
3. Import completed research back into the system
4. Verify and validate new data entries

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: For AI-powered data extraction
- `LINKEDIN_USERNAME/PASSWORD`: For LinkedIn data collection
- `DATABASE_URL`: Custom database connection string

### Settings (config.py)
- API timeouts and retry settings
- Data quality thresholds
- Export format preferences
- Logging levels and formats
- Scheduling parameters

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure SQLite permissions are correct
   - Check database file path in config

2. **API Rate Limiting**
   - Increase delay between requests in config
   - Check API key validity and quotas

3. **Export Failures**
   - Verify export directory permissions
   - Check available disk space

4. **Import Errors**
   - Validate data format and encoding
   - Check for duplicate entries

### Logging
Application logs are stored in the `logs/` directory:
- `fdic_mrm_tool.log`: Main application log
- Console output for immediate feedback

## Development

### Adding New Data Sources
1. Create collector class in new module
2. Implement data extraction methods
3. Add data source to `DataSource` enum
4. Update database models if needed
5. Add CLI commands for new functionality

### Extending Export Formats
1. Add new export method to `ExportHandler`
2. Update CLI options and help text
3. Add format validation and error handling

## License

This tool is provided for research and educational purposes. Please respect the terms of service of all data sources and APIs used.

## Support

For issues, questions, or contributions:
1. Check the logs for detailed error information
2. Review configuration settings
3. Verify all dependencies are installed correctly
4. Ensure proper API keys and permissions are configured