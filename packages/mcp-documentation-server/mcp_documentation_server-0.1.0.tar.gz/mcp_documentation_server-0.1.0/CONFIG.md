# MCP Documentation Server - Configuration Examples

This directory contains configuration examples for different MCP clients.

## Installation

1. Install the package:
```bash
pip install mcp-documentation-server
```

2. Run the installation wizard:
```bash
mcp-doc-install
```

3. Or configure manually using the examples below.

## Claude Desktop Configuration

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server",
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/docs",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Cursor Configuration

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server",
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/docs",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## VS Code Configuration

Add to your VS Code MCP configuration:

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server",
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/docs",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Environment Variables

- `MCP_DOC_BASE_DIR`: Base directory for the server (default: current directory)
- `MCP_DOC_DATA_DIR`: Directory containing documentation files (default: data)
- `MCP_DOC_EMBEDDINGS_DIR`: Directory for embeddings cache (default: embeddings)
- `MCP_DOC_METADATA_FILE`: Metadata file path (default: metadata.json)
- `MCP_DOC_LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR, default: INFO)
- `MCP_DOC_CACHE_SIZE`: Cache size for embeddings (default: 1000)

## Manual Startup

You can also start the server manually:

```bash
# Start with default settings
mcp-documentation-server

# Start with custom settings
mcp-doc-launcher --base-dir /path/to/docs --log-level DEBUG

# Run installation wizard
mcp-doc-install
```

## Usage

Once configured, you can use these MCP tools in your client:

- `get_upload_info`: Get information about where to upload documents
- `list_documents`: List all uploaded documents
- `search_documents`: Perform semantic search in documents  
- `remove_document`: Remove a document from the index

## Supported File Formats

- `.txt` - Plain text files
- `.md` - Markdown files

## Performance Tips

1. Keep your documents organized in subdirectories
2. Use descriptive filenames
3. For large document collections, consider increasing cache size
4. Monitor log files for performance insights
