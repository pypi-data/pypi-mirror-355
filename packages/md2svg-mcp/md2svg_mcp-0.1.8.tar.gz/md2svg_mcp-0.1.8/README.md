# Md2svg-mcp

A Model Context Protocol (MCP) server that converts Markdown text to SVG images.

## Overview

This MCP server provides a tool to transform Markdown content into SVG format. It supports various Markdown elements, including headings, lists, code blocks, and tables. The server can be easily integrated into any MCP client, allowing users to visualize Markdown content in a scalable vector graphic format.

## Features

- **Markdown Parsing**: Converts Markdown text to structured blocks.
- **SVG Generation**: Renders Markdown elements as SVG elements.
- **Customization**: Supports customizable output dimensions, padding, and colors.
- **MCP Integration**: Compatible with any MCP client.

## Installation


```json
{
  "mcpServers": {
    "md2svg-mcp": {
      "command": "uvx",
      "args": [
        "md2svg-mcp"
      ]
    }
  }
}
```

## Configuration

The `markdown_to_svg` tool supports the following parameters:

- `md_text`: The Markdown text to be converted.
- `output_file`: The output SVG file name (default: `output.svg`).
- `width`: The width of the SVG image (default: `720`).
- `padding`: The padding around the SVG content (default: `50`).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
