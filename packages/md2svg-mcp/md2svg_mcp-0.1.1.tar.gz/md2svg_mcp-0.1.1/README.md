# md2svg-mcp

A Python library to convert Markdown content to SVG format.

## Features

- Supports various Markdown elements including headers, lists, code blocks, and tables
- Converts Markdown to scalable vector graphics (SVG)
- Simple and easy-to-use API
- MCP server integration for remote conversion service

## Installation

```bash
pip install md2svg-mcp
```

## Usage

### Local Usage

```python
from md2svg_mcp import parse_markdown, markdown_to_svg

# Parse markdown content
blocks = parse_markdown("# Header\n\nThis is a paragraph\n\n- List item 1\n- List item 2")

# Convert to SVG
svg_output = markdown_to_svg(blocks, width=800, height=600)
```

### MCP Server Configuration

The tool includes an MCP server for remote access to the Markdown to SVG conversion functionality. To configure and use the MCP server:

1. Install the package with MCP support: `pip install md2svg-mcp`
2. Run the server: `md2svg-mcp` in your terminal
3. The server will start on the default port (usually 8000)
4. You can now connect to the MCP server from other applications

The MCP server provides the following capabilities:
- `markdown_to_svg`: Convert Markdown text to SVG images
- Configurable output dimensions and styling

For developers connecting to the MCP server, you'll need to use the MCP client protocol to communicate with the server.