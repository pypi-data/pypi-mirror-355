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

> 🤖 **For LLM-Assisted Setup**: If you're using an AI assistant to help with setup, point them to the [LLM Setup Guide](LLM_SETUP_GUIDE.md) for step-by-step instructions.

> 🚀 **Interactive Setup**: Run `python3 setup_helper.py` for an interactive setup experience that will guide you through installation and configuration.

### 🚀 Quick Install (Recommended)

The easiest way to install visidata-mcp is via npm. This automatically handles Python dependencies and setup:

```bash
npm install -g @moeloubani/visidata-mcp@beta
```

**Prerequisites**: Python 3.10+ (the installer will check and guide you if needed)

**That's it!** The npm package automatically:
- ✅ Checks for Python 3.10+ 
- ✅ Installs the Python package and all dependencies
- ✅ Creates a global `visidata-mcp` command
- ✅ Works with both Claude Desktop and Cursor

### Alternative: Python Install Methods

#### 🐍 Install with pipx (Recommended for Python users)

If you have an externally managed Python environment (common on macOS with Homebrew), use pipx:

```bash
# Install pipx if you don't have it
brew install pipx  # macOS
# or
pip install --user pipx  # other systems

# Install visidata-mcp
pipx install visidata-mcp
```

**Benefits of pipx:**
- ✅ Handles virtual environments automatically
- ✅ Avoids conflicts with system Python
- ✅ Works on externally managed Python environments
- ✅ Creates global `visidata-mcp` command

#### Install from PyPI

```bash
pip install visidata-mcp
```

**Note**: If you get an "externally-managed-environment" error, use pipx instead (see above).

#### Install from Source

```bash
git clone https://github.com/moeloubani/visidata-mcp.git
cd visidata-mcp
pipx install .
# or if you prefer pip:
pip install -e .
```

## Usage

### With Claude Desktop

After installing via npm or pipx, add this to your Claude Desktop configuration:

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

**⚠️ PATH Issues**: If you have multiple versions installed (npm + pipx), use the full path:
```json
{
  "mcpServers": {
    "visidata": {
      "command": "/Users/yourusername/.local/bin/visidata-mcp"
    }
  }
}
```

### With Cursor AI

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

**⚠️ Recommended: Use Full Path**
To avoid PATH conflicts, use the full path to the specific version you want:

```json
{
  "mcpServers": {
    "visidata": {
      "command": "/Users/yourusername/.local/bin/visidata-mcp"
    }
  }
}
```

Replace `yourusername` with your actual username. Find your path with: `which visidata-mcp` or `ls ~/.local/bin/visidata-mcp`

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
# Run the server directly (runs indefinitely, use Ctrl+C to stop)
visidata-mcp

# Or with Python module
python -m visidata_mcp.server
```

**Note**: MCP servers run indefinitely and communicate via stdin/stdout. They're designed to be controlled by MCP clients, not run interactively. Use the MCP Inspector for testing.

### Development and Testing

#### Using MCP Inspector

The MCP Inspector is a web-based tool for testing and debugging MCP servers:

```bash
# Start the inspector (will open a browser)
npx @modelcontextprotocol/inspector visidata-mcp

# Or for pipx installations:
npx @modelcontextprotocol/inspector ~/.local/bin/visidata-mcp
```

The inspector will start and provide a URL with authentication token:
```
🔗 Open inspector with token pre-filled:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=your-token-here
```

**Note**: The MCP server runs indefinitely and doesn't respond to `--help` or similar commands. It's designed to be controlled by MCP clients or the inspector.

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

#### "externally-managed-environment" Error
If you see this error when trying to install:
```
error: externally-managed-environment
× This environment is externally managed
```

**Solution**: Use pipx instead of pip:
```bash
pipx install visidata-mcp
```

This is common on macOS with Homebrew Python and protects your system Python installation.

#### "0 tools available" in Cursor
- **Most common cause**: PATH conflict between npm and pipx versions
- **Solution**: Use the full path to ensure you get the working version:
  ```json
  {
    "mcpServers": {
      "visidata": {
        "command": "/Users/yourusername/.local/bin/visidata-mcp"
      }
    }
  }
  ```
- **Check which version**: Run `which visidata-mcp` to see which version is found first
- **For development**: Use the full path to your virtual environment's Python
- **Always restart** Cursor completely after changing the configuration

#### Server Won't Start or Hangs
- **MCP servers run indefinitely**: They don't respond to `--help` or exit normally
- **Test with MCP Inspector**: Use `npx @modelcontextprotocol/inspector visidata-mcp`
- **Check dependencies**: `pipx list` to see if visidata-mcp is properly installed
- **Verify installation**: Try importing in Python: `python3 -c "import visidata_mcp.server"`

#### VisiData Warning Messages
You may see warnings like:
```
setting unknown option confirm_overwrite
```
These warnings are **harmless** and don't affect functionality. They occur because the MCP server sets VisiData options that may not be recognized in all versions.

#### Permission Errors
- Ensure the command path is accessible
- For pipx: Check that `~/.local/bin` is in your PATH
- For development: Check file permissions on your project directory

## Setup Resources

This repository includes several resources to help with setup:

- **[LLM_SETUP_GUIDE.md](LLM_SETUP_GUIDE.md)**: Comprehensive guide for AI assistants to help users with setup
- **[setup_helper.py](setup_helper.py)**: Interactive Python script that guides users through installation
- **[README.md](README.md)**: Main documentation (this file)

### Testing Your Installation

#### Quick Test (Recommended)

Test that the installation works:

```bash
# Check that the command is available
which visidata-mcp

# Test with MCP Inspector (opens in browser)
npx @modelcontextprotocol/inspector visidata-mcp
```

The inspector will show you all available tools and let you test them interactively.

#### Verify Python Module Import

```bash
# Test that Python can import the module
python3 -c "import visidata_mcp.server; print('✅ visidata-mcp installed correctly')"
```

#### For Development/Source Installs

If you're working with the source code:

```bash
cd /path/to/visidata-mcp
source venv/bin/activate
python verify_setup.py
```

This comprehensive script checks:
- Python version and virtual environment
- Package installations
- MCP server tools registration (should show **8 tools**)
- Configuration files
- Server startup capability

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