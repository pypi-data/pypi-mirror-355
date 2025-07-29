# VS Code + GitHub Copilot Integration Guide

Follow these steps to integrate your MCP Documentation Server with VS Code and GitHub Copilot.

## Prerequisites

1. **VS Code 1.99+** - [Download latest version](https://code.visualstudio.com/download)
2. **GitHub Copilot subscription** - [Setup Copilot](https://code.visualstudio.com/docs/copilot/setup)
3. **Your MCP server running** - Make sure you can start `python server.py`

## Step 1: Enable MCP Support in VS Code

1. Open VS Code Settings (`Ctrl+,` or `Cmd+,`)
2. Search for `chat.mcp.enabled`
3. Enable the setting ✅
4. Optionally enable `chat.mcp.discovery.enabled` for auto-discovery

Or add to your `settings.json`:
```json
{
  "chat.mcp.enabled": true,
  "chat.mcp.discovery.enabled": true
}
```

## Step 2: Configure MCP Server

### Option A: Workspace Configuration (Recommended)

Create `.vscode/mcp.json` in your project root:

```json
{
  "servers": {
    "documentationSearch": {
      "type": "stdio",
      "command": "python",
      "args": ["server.py"],
      "cwd": "${workspaceFolder}/path/to/mcp-documentation-server"
    }
  }
}
```

### Option B: User Settings (Global)

Add to your VS Code user settings:

```json
{
  "mcp": {
    "servers": {
      "documentationSearch": {
        "type": "stdio", 
        "command": "python",
        "args": ["/absolute/path/to/mcp-documentation-server/server.py"],
        "cwd": "/absolute/path/to/mcp-documentation-server"
      }
    }
  }
}
```

## Step 3: Use with GitHub Copilot

1. **Open Copilot Chat** (`Ctrl+Alt+I`)
2. **Switch to Agent Mode** from the dropdown
3. **Select Tools** button to see available MCP tools
4. **Enable documentation search tools**:
   - `get_upload_info`
   - `list_documents` 
   - `search_documents`
   - `remove_document`

## Step 4: Example Usage

### Search Documentation
```
@copilot Search for information about Docker containerization in my documentation
```

### List Available Documents  
```
@copilot What documents are available in my documentation system?
```

### Get Upload Instructions
```
@copilot How do I add new documentation files to the system?
```

## Troubleshooting

### Server Not Starting
1. Run `MCP: List Servers` from Command Palette
2. Check server status and logs with `Show Output`
3. Verify Python path and server.py location

### Tools Not Appearing
1. Ensure MCP support is enabled
2. Restart VS Code after configuration changes
3. Check that server starts without errors

### Permission Issues
1. Make sure Python virtual environment is activated
2. Verify file permissions for server.py
3. Check that all dependencies are installed

## Commands Reference

- `MCP: List Servers` - View configured servers
- `MCP: Add Server` - Add new MCP server  
- `MCP: Browse Resources` - View available resources
- `F1 > Agent mode` - Switch to agent mode in chat

## Advanced Configuration

### Development Mode
Add to your MCP configuration for development:

```json
{
  "servers": {
    "documentationSearch": {
      "type": "stdio",
      "command": "python", 
      "args": ["server.py"],
      "cwd": "${workspaceFolder}",
      "dev": {
        "watch": "**/*.py",
        "debug": { "type": "python" }
      }
    }
  }
}
```

This enables auto-restart when Python files change and debugging support.
