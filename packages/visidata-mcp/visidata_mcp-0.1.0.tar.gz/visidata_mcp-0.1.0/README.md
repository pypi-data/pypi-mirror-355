# VisiData MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that provides access to [VisiData](https://visidata.org) functionality. VisiData is a terminal spreadsheet multitool for discovering and arranging tabular data.

## Features

This MCP server exposes VisiData's powerful data manipulation capabilities through the following tools:

### 🔧 Tools

- **`load_data`** - Load and inspect data files from various formats
- **`get_data_sample`** - Get a preview of your data with configurable row count
- **`analyze_data`** - Perform comprehensive data analysis with column types and statistics
- **`convert_data`** - Convert between different data formats (CSV ↔ JSON ↔ Excel, etc.)
- **`filter_data`** - Filter data based on conditions (equals, contains, greater/less than)
- **`get_column_stats`** - Get detailed statistics for specific columns
- **`sort_data`** - Sort data by any column in ascending or descending order
- **`get_supported_formats`** - List all supported file formats

### 📚 Resources

- **`visidata://help`** - Comprehensive help documentation and usage examples

### 🎯 Prompts

- **`analyze_dataset_prompt`** - Generate structured prompts for comprehensive dataset analysis

## Supported Data Formats

VisiData supports a wide variety of data formats:

- **Spreadsheets**: CSV, TSV, Excel (XLSX/XLS)
- **Structured Data**: JSON, JSONL, XML, YAML
- **Databases**: SQLite
- **Scientific**: HDF5, Parquet, Arrow
- **Archives**: ZIP, TAR, GZ, BZ2, XZ
- **Web**: HTML tables
- **Python**: Pickle files

## Installation

### 🚀 Quick Install (Recommended)

The easiest way to install visidata-mcp is via npm. This automatically handles Python dependencies and setup:

```bash
npm install -g @moeloubani/visidata-mcp@beta
```

**Prerequisites**: Python 3.8+ (the installer will check and guide you if needed)

**That's it!** The npm package automatically:
- ✅ Checks for Python 3.8+ 
- ✅ Installs the Python package and all dependencies
- ✅ Creates a global `visidata-mcp` command
- ✅ Works with both Claude Desktop and Cursor

### Alternative: Python-only Install

#### Install from PyPI

```bash
pip install visidata-mcp
```

#### Install from Source

```bash
git clone https://github.com/moeloubani/visidata-mcp.git
cd visidata-mcp
pip install -e .
```

## Usage

### With Claude Desktop (npm install)

After installing via npm, simply add this to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "visidata": {
      "command": "visidata-mcp"
    }
  }
}
```

### With Cursor AI (npm install)

Create `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "visidata": {
      "command": "visidata-mcp"
    }
  }
}
```

**Restart your AI application** and you're ready to go! 🎉

### Legacy Configuration (Python-only install)

<details>
<summary>Click to expand legacy configuration instructions</summary>

#### With Cursor AI

1. **Navigate to your project directory** and ensure the virtual environment is activated:
   ```bash
   cd /path/to/your/visidata-mcp
   source venv/bin/activate
   ```

2. **Create/Edit Cursor MCP configuration** at `.cursor/mcp.json` in your project:
   ```json
   {
     "mcpServers": {
       "visidata": {
         "command": "/path/to/your/visidata-mcp/venv/bin/python",
         "args": ["-m", "visidata_mcp.server"],
         "cwd": "/path/to/your/visidata-mcp"
       }
     }
   }
   ```

   **⚠️ Important**: Use the **full path to your virtual environment's Python** executable. This ensures Cursor uses the correct Python interpreter with all dependencies installed.

3. **Restart Cursor completely** (Cmd+Q and reopen)
4. **Start using VisiData tools** in your AI chat! Look for "Available MCP Tools" in the chat interface.

#### With Claude Desktop

Add the server to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "visidata": {
      "command": "visidata-mcp"
    }
  }
}
```

</details>

### Direct Execution

```bash
# Run the server directly
visidata-mcp

# Or with Python module
python -m visidata_mcp.server
```

### Development Mode

```bash
# Using MCP Inspector for debugging
npx @modelcontextprotocol/inspector visidata-mcp
```

## Example Usage

### Loading and Analyzing Data

```python
# Load a CSV file
load_data("/path/to/sales_data.csv")

# Get a sample of the first 5 rows
get_data_sample("/path/to/sales_data.csv", 5)

# Perform comprehensive analysis
analyze_data("/path/to/sales_data.csv")

# Get statistics for a specific column
get_column_stats("/path/to/sales_data.csv", "revenue")
```

### Data Transformation

```python
# Convert CSV to JSON
convert_data("/path/to/data.csv", "/path/to/output.json")

# Filter data
filter_data("/path/to/sales_data.csv", "revenue", "greater_than", "1000", "/path/to/high_revenue.csv")

# Sort data by column
sort_data("/path/to/sales_data.csv", "date", False, "/path/to/sorted_data.csv")
```

### Getting Help

```python
# Access the help resource
# This will provide comprehensive documentation and examples
```

## Troubleshooting

### Common Issues

#### "0 tools available" in Cursor
- **Solution**: Ensure you're using the full path to your virtual environment's Python in the MCP configuration
- **Example**: Use `/path/to/visidata-mcp/venv/bin/python` instead of just `python`
- Restart Cursor completely after changing the configuration

#### VisiData Warning Messages
You may see warnings like:
```
setting unknown option confirm_overwrite
```
These warnings are **harmless** and don't affect functionality. They occur because the MCP server sets VisiData options that may not be recognized in all versions.

#### Server Not Starting
- Verify your virtual environment has all dependencies: `pip list | grep visidata`
- Check that Python 3.8+ is being used: `python --version`
- Try running the server directly: `python -m visidata_mcp.server`

#### Permission Errors
- Ensure the virtual environment Python executable is accessible
- Check file permissions on your project directory
- Try running with `python -m visidata_mcp.server` to test manually

### Testing Your Installation

Run the comprehensive verification script to check your entire setup:
```bash
cd /path/to/visidata-mcp
source venv/bin/activate
python verify_setup.py
```

This script will check:
- Python version and virtual environment
- Package installations
- MCP server tools registration (should show **8 tools**)
- Configuration files
- Server startup capability

For just testing tools registration:
```bash
python test_tools.py
```

## API Reference

### Tools

#### `load_data(file_path: str, file_type: Optional[str] = None) -> str`

Load and inspect a data file.

**Parameters:**
- `file_path`: Path to the data file
- `file_type`: Optional file type hint (csv, json, xlsx, etc.)

**Returns:** JSON string with file information (rows, columns, column names, types)

#### `get_data_sample(file_path: str, rows: int = 10) -> str`

Get a sample of data from the file.

**Parameters:**
- `file_path`: Path to the data file
- `rows`: Number of rows to return (default: 10)

**Returns:** JSON string with sample data and metadata

#### `analyze_data(file_path: str) -> str`

Perform comprehensive data analysis.

**Parameters:**
- `file_path`: Path to the data file

**Returns:** JSON string with detailed analysis including column types and sample values

#### `convert_data(input_path: str, output_path: str, output_format: Optional[str] = None) -> str`

Convert data between formats.

**Parameters:**
- `input_path`: Path to input file
- `output_path`: Path for output file
- `output_format`: Target format (inferred from extension if not provided)

**Returns:** Success message or error details

#### `filter_data(file_path: str, column: str, condition: str, value: str, output_path: Optional[str] = None) -> str`

Filter data based on conditions.

**Parameters:**
- `file_path`: Path to the data file
- `column`: Column name to filter on
- `condition`: Filter condition (`equals`, `contains`, `greater_than`, `less_than`)
- `value`: Value to filter by
- `output_path`: Optional path to save filtered data

**Returns:** JSON string with filtering results

#### `get_column_stats(file_path: str, column: str) -> str`

Get statistics for a specific column.

**Parameters:**
- `file_path`: Path to the data file
- `column`: Column name to analyze

**Returns:** JSON string with column statistics

#### `sort_data(file_path: str, column: str, descending: bool = False, output_path: Optional[str] = None) -> str`

Sort data by a column.

**Parameters:**
- `file_path`: Path to the data file
- `column`: Column name to sort by
- `descending`: Sort in descending order (default: False)
- `output_path`: Optional path to save sorted data

**Returns:** JSON string with sorting results

#### `get_supported_formats() -> str`

Get list of supported file formats.

**Returns:** JSON string with supported formats and descriptions

## Error Handling

The server includes comprehensive error handling:

- **File Access Errors**: Clear messages when files cannot be read
- **Format Errors**: Helpful messages for unsupported or corrupted files
- **Processing Errors**: Detailed error information with stack traces for debugging
- **Validation Errors**: Clear messages for invalid parameters or conditions

## Performance Considerations

- **Large Files**: The server handles large datasets efficiently through VisiData's streaming capabilities
- **Memory Usage**: VisiData uses lazy loading and efficient data structures
- **Batch Operations**: Operations are optimized for batch processing

## Development

### Project Structure

```
visidata-mcp/
├── src/
│   └── visidata_mcp/
│       ├── __init__.py
│       └── server.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

### Building and Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Build package
python -m build

# Run with debugging
python -m visidata_mcp.server
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## About VisiData

[VisiData](https://visidata.org) is an interactive multitool for tabular data. It combines the clarity of a spreadsheet, the efficiency of the terminal, and the power of Python, into a lightweight utility that can handle millions of rows with ease.

Key VisiData features exposed through this MCP server:
- **Universal Data Loader**: Open data from any format or source
- **Efficient Processing**: Handle large datasets with streaming and lazy evaluation
- **Rich Type System**: Automatic type detection and conversion
- **Powerful Filtering**: Complex filtering and selection capabilities
- **Format Conversion**: Convert between dozens of data formats

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [VisiData Website](https://visidata.org)
- [VisiData Documentation](https://visidata.org/docs/)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [MCP Specification](https://spec.modelcontextprotocol.io)

## Support

For issues and questions:
- **VisiData Issues**: Related to data processing functionality
- **MCP Issues**: Related to the Model Context Protocol integration
- **General Issues**: Use the GitHub issue tracker

## Changelog

### Version 0.1.0
- Initial release
- Core VisiData functionality exposed through MCP
- Support for major data formats
- Comprehensive data analysis tools
- Format conversion capabilities
- Data filtering and sorting
- Column statistics and analysis 