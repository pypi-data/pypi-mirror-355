# Tableau Parser

A Python library for parsing and analyzing Tableau workbook (.twb) files. This library provides detailed information about Tableau workbooks including datasources, calculations, dashboards, sheets, and more.

## Installation

```bash
pip install tableau-parser
```

## Usage

```python
from tableau_parser import analyze_tableau_workbook

# Analyze a Tableau workbook
result = analyze_tableau_workbook("path/to/your/workbook.twb")

# Access the analysis results
print(result.model_dump_json(indent=4))
```

## Features

- Parse Tableau workbook (.twb) files
- Extract detailed information about:
  - Datasources (published and embedded)
  - Calculations
  - Dashboards
  - Sheets
  - Charts
  - Tables
  - Parameters
  - Filters
  - Joins
  - And more!

## Example Output

The library returns a structured response containing:

- Summary information (counts of various components)
- Detailed information about each component
- Datasource information including filters and row-level security

## Requirements

- Python 3.7 or higher
- pydantic 2.0.0 or higher

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 