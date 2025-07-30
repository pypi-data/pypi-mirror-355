# DocsetMCP

[![PyPI](https://img.shields.io/pypi/v/docsetmcp)](https://pypi.org/project/docsetmcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/docsetmcp)](https://pypi.org/project/docsetmcp/)

**Access your local Dash documentation directly from AI assistants** 🚀

DocsetMCP is a Model Context Protocol (MCP) server that seamlessly integrates your local Dash docsets with AI assistants like Claude, enabling instant access to offline documentation without leaving your conversation.

## 📋 Table of Contents

- [Why DocsetMCP?](#why-docsetmcp)
- [Quick Start](#quick-start)
- [Features](#-features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Available Tools](#available-tools)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Why DocsetMCP?

- 📚 **Instant Documentation**: No switching, no web searches. Get straight to the docs directly in your AI conversation
- 🔒 **Local and Private**: Work with docset files on your machine
- ⚡ **Lightning Fast**: Optimized caching and direct database queries
- 🎯 **Precise Results**: Get exactly what you need with smart filtering

## Quick Start

```json
{
  "mcpServers": {
    "docsetmcp": {
      "command": "uvx",
      "args": ["docsetmcp"]
    }
  }
}
```

Add to your MCP config and restart your MCP client. Then try asking something like "Find me the AppIntent documentation"

## ✨ Features

### Documentation Search

- **Multi-Docset Support**: Search across 165+ supported docsets including Apple, NodeJS, Python, and more
- **Language Filtering**: Target specific programming languages within docsets
- **Name-Based Search**: Only returns entries where search terms match item names for precise results
- **Smart Ranking**: Results ranked by match type (exact > prefix > substring) and dynamic type ordering
- **Container Guidance**: Framework and class entries show drilldown notes for exploring members

### Cheatsheet Access

- **Quick Reference**: Instant access to Git, Vim, Docker, and 40+ other cheatsheets
- **Fuzzy Matching**: Find cheatsheets even with partial names
- **Category Browsing**: Explore commands by category within each cheatsheet
- **Search Within**: Query specific commands inside any cheatsheet

### Performance & Integration

- **Efficient Caching**: In-memory caching for repeated queries
- **Direct Database Access**: No intermediate servers or APIs
- **Universal**: Works with Claude Desktop, Cursor, VS Code, and any MCP-compatible client
- **Framework Discovery**: List all available frameworks/types in any docset
- **Container Guidance**: Automatic drilldown notes for frameworks and classes with members

## 📦 Supported Docsets

DocsetMCP supports 165+ docsets including:

<details>
<summary><b>Popular Languages</b></summary>

- Python (2 & 3)
- JavaScript / TypeScript
- Java
- C / C++
- Go
- Rust
- Ruby
- Swift / Objective-C
- PHP
- Bash
- And many more...

</details>

<details>
<summary><b>Web Frameworks</b></summary>

- React / Angular / Vue
- Node.js / Express
- Django / Flask
- Ruby on Rails
- Bootstrap
- jQuery
- And many more...

</details>

<details>
<summary><b>Developer Tools</b></summary>

- Git (cheatsheet)
- Docker (cheatsheet)
- Vim (cheatsheet)
- MySQL / PostgreSQL
- MongoDB / Redis
- nginx / Apache
- And many more...

</details>

Use `list_available_docsets` to see all docsets installed on your system.

## Prerequisites

- macOS (Dash is Mac-only)
- [Dash](https://kapeli.com/dash) with desired docsets downloaded
- Python 3.10 or higher
- UV package manager ([How to Install](https://docs.astral.sh/uv/getting-started/installation/))
- An AI assistant that supports MCP (Claude Desktop, Claude Code CLI, Cursor IDE, etc.)

## Configuration

Choose your MCP client below for specific setup instructions:

<details>
<summary><b>🤖 Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "docsetmcp": {
      "command": "uvx",
      "args": ["docsetmcp"]
    }
  }
}
```

</details>

<details>
<summary><b>⌨️ Claude Code CLI</b></summary>

```bash
# For current project
claude mcp add docsetmcp "uvx docsetmcp"

# For all projects
claude mcp add --scope user docsetmcp "uvx docsetmcp"
```

</details>

<details>
<summary><b>📝 Cursor, VS Code, Windsurf and other MCP-compatible clients</b></summary>

Add to your MCP configuration (Cursor: `.mcp/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "docsetmcp": {
      "command": "uvx",
      "args": ["docsetmcp"]
    }
  }
}
```

**Note**: Restart your client and check your MCP settings for connection status.

</details>

## Installation

### No Installation Required (Recommended)

If your MCP client supports `uvx`, no installation is needed! The package will be automatically downloaded and run when needed. See the [Quick Start](#quick-start) or [Configuration](#configuration) sections.

### Manual Installation

If you prefer to install locally or your MCP client doesn't support `uvx`:

```bash
pip install docsetmcp
```

Then use `docsetmcp` instead of `uvx docsetmcp` in your configuration.

### Development Installation

1. **Clone and install**:

   ```bash
   git clone https://github.com/codybrom/docsetmcp.git
   cd docsetmcp
   pip install -e .
   ```

2. **Run tests** (optional):

   ```bash
   # Install test dependencies
   pip install pytest pytest-cov pytest-xdist

   # Run basic tests
   pytest tests/test_docsets.py::TestDocsets::test_yaml_structure -v

   # Run quick tests (structure + existence checks)
   pytest tests/ -k "yaml_structure or test_docset_exists" -v

   # Run full test suite (all docsets)
   pytest tests/ -v

   # Run with coverage
   pytest tests/ --cov=docsetmcp --cov-report=html -v

   # Validate all local cheatsheets work (integration test)
   python scripts/validate_cheatsheets.py
   ```

## Usage Examples

Once configured, you can ask your AI assistant to search documentation naturally:

### 🍎 iOS/macOS Development

```text
"Search for URLSession documentation"
"Show me how to use AppIntent in SwiftUI"
"Find CarPlay framework documentation"  # Returns framework + related entries with drilldown notes
"Search for CPListTemplate class"       # Returns specific CarPlay class
"Find NSPredicate examples"
```

### 🌐 Web Development

```text
"Look up Express.js middleware documentation"
"Search React hooks in the React docset"
"Find CSS flexbox properties"
```

### 🛠️ DevOps & Terminal

```text
"Search git rebase commands in the Git cheatsheet"
"Show Docker compose syntax from the cheatsheet"
"Find bash array manipulation commands"
```

### 📊 Data Science

```text
"Search pandas DataFrame methods"
"Look up NumPy array broadcasting"
"Find matplotlib pyplot functions"
```

### Advanced Usage

```text
# Search specific docset with language filter
"Use search_docs for 'URLSession' in the apple_api_reference docset with Swift language"

# Explore framework members using drilldown guidance
"Search for 'SwiftData' then follow the drilldown note to see all members"

# List all available tools
"What frameworks are available in the nodejs docset?"

# Browse cheatsheet categories
"Show all categories in the vim cheatsheet"
```

## Discovery Workflow

DocsetMCP is designed for **name-based searches**, not keyword searching. Follow this workflow:

### 1. **Start with Discovery Tools**

```text
# Find what languages are available
"List all available programming languages"

# Find docsets for your language
"Show me all Python docsets" 

# See what types are available in a docset
"List all types in the apple_api_reference docset for Swift"

# Browse entries by type with letter filters
"Show me all Classes starting with 'UI' in apple_api_reference for Swift"
```

### 2. **Then Search by Exact Names**

```text
# Once you know exact names, search for them
"Search for UIViewController in apple_api_reference with Swift"
"Find readFile documentation in nodejs docset"
"Show me the CarPlay framework documentation"
```

### 3. **Use Drilldown Notes**

When you find container types (frameworks, classes), follow the drilldown guidance:

```text
# Container entry will show: "contains 42 additional members - use search_docs('ContainerName', max_results=50)"
"Search for SwiftData in apple_api_reference with max_results=50"
```

## How It Works

1. **Multi-Format Support**: Handles both Apple cache format and tarix compression
2. **Direct Database Access**: Queries Dash's SQLite databases for fast lookups
3. **Name-Based Matching**: Only returns entries where search terms match item names (no false positives)
4. **Smart Ranking**: Prioritizes exact matches, then prefix matches, then substring matches
5. **Dynamic Type Ordering**: Uses docset configuration files for intelligent result prioritization
6. **Container Detection**: Automatically detects frameworks/classes with members and provides exploration guidance
7. **Smart Extraction**: Decompresses Apple's DocC JSON or extracts HTML from tarix archives
8. **Markdown Formatting**: Converts documentation to readable Markdown

## Available Tools

DocsetMCP provides eleven powerful tools for accessing your documentation:

### 🔍 `search_docs`

Search and extract documentation from any docset.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `query` | string | **Exact name** to search (not keywords) | *required* |
| `docset` | string | Target docset (e.g., 'nodejs', 'python_3') | *required* |
| `language` | string | Programming language filter | docset default |
| `max_results` | int | Number of results (1-10) | 3 |

### 📋 `search_cheatsheet`

Search Dash cheatsheets for quick command reference.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `cheatsheet` | string | Cheatsheet name (e.g., 'git', 'vim') | *required* |
| `query` | string | Search within cheatsheet | - |
| `category` | string | Filter by category | - |
| `max_results` | int | Number of results (1-50) | 10 |

### 📚 `list_available_docsets`

List all installed Dash docsets with their supported languages.

### 📝 `list_available_cheatsheets`

List all available Dash cheatsheets that can be searched.

### 🏗️ `list_frameworks`

List frameworks/types within a specific docset.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `docset` | string | Target docset | *required* |
| `filter` | string | Filter framework names | - |

### 🌍 `list_languages`

Discover all programming languages with available documentation.

### 📖 `list_docsets_by_language`

Find all docsets that support a specific programming language.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `language` | string | Programming language | *required* |

### 🏷️ `list_types`

List all available types (Class, Protocol, Function, etc.) in a docset/language.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `docset` | string | Target docset | *required* |
| `language` | string | Programming language filter | - |

### 📋 `list_entries`

List entries filtered by type and optional name prefix.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `docset` | string | Target docset | *required* |
| `type_name` | string | Type to filter by (e.g., 'Class', 'Protocol') | *required* |
| `language` | string | Programming language filter | - |
| `name_filter` | string | Filter entries by name prefix | - |
| `max_results` | int | Number of results (1-100) | 20 |

### 📂 `list_cheatsheet_categories`

List all categories within a specific cheatsheet.

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `cheatsheet` | string | Cheatsheet name | *required* |

### 📄 `fetch_cheatsheet`

Fetch entire cheatsheet content (recommended for comprehensive access).

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `cheatsheet` | string | Cheatsheet name | *required* |

## Troubleshooting

<details>
<summary><b>❌ "Docset not found" error</b></summary>

This means the docset isn't installed in Dash. To fix:

1. Open Dash.app
2. Go to Preferences → Downloads
3. Download the required docset
4. Restart your MCP client

</details>

<details>
<summary><b>🔌 MCP connection failed</b></summary>

1. **Check installation**: Run `pip show docsetmcp` to verify installation
2. **Test manually**: Run `uvx docsetmcp` in terminal - you should see MCP output
3. **Check logs**:
   - Claude Desktop: Check Console.app for Claude logs
   - Cursor: Check Output → MCP panel
4. **Verify config path**: Ensure config file is in the correct location

</details>

<details>
<summary><b>📭 No results found</b></summary>

- The content might not be in your local Dash cache
- Try searching with different terms or partial matches
- Use `list_available_docsets` to verify the docset is loaded
- Some docsets may use different naming conventions (e.g., 'fs' vs 'filesystem')

</details>

<details>
<summary><b>🐛 Other issues</b></summary>

1. **Python version**: Ensure you have Python 3.10 or higher
2. **UV not found**: Install UV package manager from <https://docs.astral.sh/uv/>
3. **Permission denied**: Check file permissions on Dash docsets directory
4. **Report bugs**: Open an issue at <https://github.com/codybrom/docsetmcp/issues>

</details>

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/codybrom/docsetmcp.git
cd docsetmcp

# Install in development mode
pip install -e .

# Run tests
pytest tests/ -v
```

### Running Tests

```bash
# Quick tests (structure validation)
pytest tests/test_docsets.py::TestDocsets::test_yaml_structure -v

# Full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=docsetmcp --cov-report=html -v

# Validate cheatsheets
python scripts/validate_cheatsheets.py
```

## Contributing

We welcome contributions! Here's how you can help:

### Adding New Docset Support

1. Create a YAML configuration in `docsetmcp/docsets/`:

   ```yaml
   # docsetmcp/docsets/my_docset.yaml
   name: My Docset
   description: Brief description of the docset
   docset_path: My_Docset/My_Docset.docset
   languages:
     - python
     - javascript
   ```

2. Test your configuration:

   ```bash
   pytest tests/test_docsets.py -k "my_docset" -v
   ```

3. Submit a pull request

### Reporting Issues

- 🐛 [Bug Reports](https://github.com/codybrom/docsetmcp/issues/new?labels=bug)
- 💡 [Feature Requests](https://github.com/codybrom/docsetmcp/issues/new?labels=enhancement)
- 📚 [Documentation Issues](https://github.com/codybrom/docsetmcp/issues/new?labels=documentation)

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Keep commits focused and descriptive

## Technical Architecture

DocsetMCP leverages Dash's internal structure for efficient documentation access:

- **Format Support**: Handles both Apple's modern cache format (SHA-1 UUID-based with brotli compression) and traditional tarix archives
- **Caching Strategy**: In-memory caching for repeated queries
- **Database Access**: Direct SQLite queries to Dash's optimized indexes
- **Content Extraction**: Smart extraction with fallback strategies
- **Type System**: Full type hints for better IDE support

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to [Kapeli](https://kapeli.com/) for creating Dash
- Built on the [Model Context Protocol](https://modelcontextprotocol.io/) standard
- Inspired by the MCP community and ecosystem
