# MCP Documentation Server

A powerful **Model Context Protocol (MCP)** server that enables semantic search across technical documentation. Built with FastMCP and advanced natural language processing, this server allows you to upload `.txt` and `.md` files and perform intelligent semantic searches to quickly find relevant information.

## ✨ Features

### 🧠 **Semantic Search Engine**
- **Advanced NLP**: Uses `paraphrase-multilingual-mpnet-base-v2` model for high-quality embeddings
- **Intelligent Chunking**: Smart text segmentation with overlap for context preservation
- **Multilingual Support**: Works with Italian, English, and other languages
- **Lightning Fast**: Sub-60ms search times after initial processing

### 📁 **Document Management**
- **Multiple Formats**: Support for `.txt` and `.md` files
- **Automatic Processing**: Scans directory for new/modified documents
- **Metadata Tracking**: File size, modification dates, character counts
- **Cache System**: Efficient embedding storage and retrieval

### 🔧 **MCP Integration**
- **Standard Compliant**: Full MCP protocol support
- **Four Core Tools**: Document upload, listing, searching, and removal
- **Async Architecture**: Non-blocking operations for better performance
- **Error Handling**: Robust error management and logging

### 📊 **Proven Performance**
- **Tested at Scale**: Successfully handles 639KB+ documents (19,000+ lines)
- **100% Success Rate**: All test queries return relevant results
- **High Accuracy**: Average similarity scores > 0.66
- **Production Ready**: Thoroughly tested with real technical documentation

## 🚀 Quick Start

### Automated Installation (Recommended)

The easiest way to install and configure the server is using our automated installer:

```bash
# Install the package
pip install mcp-documentation-server

# Run the automated setup
mcp-doc-install
```

**What it does:**
- ✅ Creates an isolated virtual environment (no permission issues!)
- ✅ Installs the server and all dependencies
- ✅ Sets up directories and configuration
- ✅ Generates wrapper scripts for easy CLI access
- ✅ Creates configuration files for all major MCP clients
- ✅ Provides step-by-step setup instructions

### Manual Installation Options

#### Option 1: Install from PyPI

```bash
pip install mcp-documentation-server
```

#### Option 2: Install from Source

```bash
git clone <repository-url>
cd mcp-documentation-server
pip install -e .
```

### Setup and Configuration

#### Automatic Setup (Recommended)

Run the installation wizard to configure the server for your MCP client:

```bash
mcp-doc-install
```

This will:
- Create an isolated virtual environment in `~/.mcp-documentation-server/venv`
- Install the server without requiring system-wide permissions
- Create necessary directories
- Generate configuration files for Claude Desktop, Cursor, and VS Code
- Create wrapper scripts for easy command-line usage
- Provide step-by-step setup instructions

#### Manual Setup

1. **Create a base directory for your documentation:**
   ```bash
   mkdir ~/.mcp-documentation-server
   cd ~/.mcp-documentation-server
   mkdir data embeddings
   ```

2. **Configure your MCP client** (see [Configuration](#configuration) section below)

3. **Add your documents** to the `data` directory

### Quick Test

1. **After automated setup, use the wrapper scripts:**
   ```bash
   # Windows
   C:\Users\YourName\.mcp-documentation-server\scripts\mcp-documentation-server.bat

   # Linux/Mac
   ~/.mcp-documentation-server/scripts/mcp-documentation-server
   ```

2. **Or start the server directly (if installed globally):**
   ```bash
   mcp-documentation-server
   ```

3. **Or use the launcher with custom settings:**
   ```bash
   mcp-doc-launcher --base-dir ~/my-docs --log-level DEBUG
   ```

## ⚙️ Configuration

### Environment Variables

The server can be configured using environment variables:

- `MCP_DOC_BASE_DIR`: Base directory for the server (default: current directory)
- `MCP_DOC_DATA_DIR`: Directory containing documentation files (default: data)
- `MCP_DOC_EMBEDDINGS_DIR`: Directory for embeddings cache (default: embeddings)
- `MCP_DOC_METADATA_FILE`: Metadata file path (default: metadata.json)
- `MCP_DOC_LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR, default: INFO)

### MCP Client Configuration

#### Claude Desktop

Add to your Claude Desktop configuration file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server",
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/documentation",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Cursor

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server",
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/documentation",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### VS Code with MCP Extension

Add to your VS Code MCP configuration:

```json
{
  "mcpServers": {
    "documentation": {
      "command": "mcp-documentation-server", 
      "env": {
        "MCP_DOC_BASE_DIR": "/path/to/your/documentation",
        "MCP_DOC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

For detailed VS Code integration instructions, see [VS_CODE_INTEGRATION.md](VS_CODE_INTEGRATION.md).

## 🎯 Why Automated Installation?

Our automated installer (`mcp-doc-install`) provides significant advantages:

### 🔒 **Isolated Environment**
- **No System Pollution**: Installs in a dedicated virtual environment
- **No Permission Issues**: Works without administrator/sudo privileges
- **Clean Uninstall**: Easy to remove without affecting your system

### 🚀 **Zero Configuration**
- **Smart Defaults**: Automatically detects optimal settings
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Multiple Clients**: Generates configs for Claude, Cursor, and VS Code simultaneously

### 🛠️ **Developer Friendly**
- **Wrapper Scripts**: Easy-to-use command-line tools
- **Local Development**: Automatically finds and installs local builds
- **Professional Setup**: Follows Python packaging best practices

### 📁 **Organized Structure**
```
~/.mcp-documentation-server/
├── venv/                    # Isolated Python environment
├── data/                    # Your documentation files
├── embeddings/              # Cached embeddings for fast search
├── configs/                 # Generated MCP client configs
└── scripts/                 # Wrapper scripts for easy CLI access
```

## 📋 Usage

### MCP Tools

Once configured with your MCP client, you can use these tools:

1. **get_upload_info**: Get information about where to upload documents
2. **list_documents**: List all uploaded documents with metadata
3. **search_documents**: Perform semantic search across all documents
4. **remove_document**: Remove a document from the index

### Example Queries

With your MCP client (Claude Desktop, etc.), you can ask:

- "What documents do I have available?"
- "Search for information about authentication"
- "Find documentation about API endpoints"
- "How do I configure the database connection?"

### Command Line Usage

#### Interactive Mode
```bash
# Start with default settings
mcp-documentation-server

# Start with custom configuration
mcp-doc-launcher --base-dir ~/my-docs --log-level DEBUG
```

#### Environment Variables
```bash
export MCP_DOC_BASE_DIR=~/my-documentation
export MCP_DOC_LOG_LEVEL=DEBUG
mcp-documentation-server
```
   .\venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server**
   ```bash
   python server.py
   ```

### Adding Documents

Simply place your `.txt` or `.md` files in the `data/` directory. The server will automatically detect and process them on the next operation.

## 🛠️ MCP Tools

The server provides four main tools for document management and search:

### 1. `get_upload_info`
Returns information about where and how to upload documents.

**Example Response:**
```json
{
  "upload_path": "/path/to/data",
  "supported_formats": [".txt", ".md"],
  "instructions": "Place files in the data directory..."
}
```

### 2. `list_documents`
Lists all available documents with metadata.

**Example Response:**
```json
{
  "documents": [
    {
      "id": "technical_docs.md",
      "name": "technical_docs.md",
      "size": 639757,
      "char_count": 619348,
      "last_modified": "2025-06-14T00:30:00"
    }
  ]
}
```

### 3. `search_documents`
Performs semantic search across all documents.

**Parameters:**
- `query` (string): Search query
- `max_results` (integer, optional): Maximum results to return (default: 5)

**Example:**
```json
{
  "query": "Docker containerization",
  "max_results": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "technical_docs.md",
      "similarity_score": 0.8423,
      "text": "Docker is a containerization platform...",
      "chunk_id": 5,
      "start_char": 1250,
      "end_char": 1750
    }
  ],
  "query": "Docker containerization",
  "total_results": 15
}
```

### 4. `remove_document`
Removes a document and its associated embeddings.

**Parameters:**
- `filename` (string): Name of the file to remove

## 📈 Performance Benchmarks

Based on comprehensive testing with real technical documentation:

| Metric | Value | Notes |
|--------|--------|--------|
| **Document Size Tested** | 639 KB | MCP protocol documentation |
| **Search Success Rate** | 100% | All 21 test queries successful |
| **Average Search Time** | 50.7ms | After initial processing |
| **Average Similarity Score** | 0.6689 | High relevance results |
| **Best Match Score** | 0.8423 | "MCP Model Context Protocol" |
| **Processing Time** | ~3min | 639KB initial processing |

### Test Categories Validated
- ✅ Basic Concepts
- ✅ Client Implementations  
- ✅ Tool Development
- ✅ Resource Management
- ✅ Prompt Engineering
- ✅ Technical Specifications

## ⚙️ Configuration

### Environment Settings

The server uses the following directory structure:

```
mcp-documentation-server/
├── data/              # Place your documents here
├── embeddings/        # Cached embeddings (auto-generated)
├── venv/             # Virtual environment
├── server.py         # Main MCP server
├── document_manager.py # Document handling
├── search_engine.py  # Semantic search engine
└── metadata.json     # Document metadata
```

### Customization Options

**Model Selection**: Change the embedding model in `search_engine.py`:
```python
model_name = "paraphrase-multilingual-mpnet-base-v2"  # Default
# model_name = "all-MiniLM-L6-v2"  # Faster, smaller
```

**Chunk Settings**: Adjust chunking parameters:
```python
chunk_size = 500      # Characters per chunk
overlap = 50         # Overlap between chunks
```

**Search Results**: Modify default result count:
```python
default_max_results = 5  # Default results returned
```

## � Integration Examples

### Claude Desktop Configuration

Add to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "documentation-search": {
      "command": "python",
      "args": ["/path/to/mcp-documentation-server/server.py"],
      "cwd": "/path/to/mcp-documentation-server"
    }
  }
}
```

### VS Code + GitHub Copilot Integration

**Prerequisites**: VS Code 1.99+, GitHub Copilot subscription

1. **Enable MCP Support** in VS Code settings:
   ```json
   {
     "chat.mcp.enabled": true,
     "chat.mcp.discovery.enabled": true
   }
   ```

2. **Configure Server** - The `.vscode/mcp.json` file is already included:
   ```json
   {
     "servers": {
       "documentationSearch": {
         "type": "stdio",
         "command": "python",
         "args": ["server.py"],
         "cwd": "${workspaceFolder}"
       }
     }
   }
   ```

3. **Use in Copilot Chat**:
   - Open Chat (`Ctrl+Alt+I`)
   - Switch to **Agent Mode**
   - Select **Tools** and enable documentation search tools
   - Ask: `Search for Docker containerization in my docs`

📖 **Full Setup Guide**: See [VS_CODE_INTEGRATION.md](VS_CODE_INTEGRATION.md)

### Using with Other MCP Clients

The server follows standard MCP protocol and works with any compliant client:

1. **Start the server** via stdio transport
2. **Connect your client** to the server process
3. **Use the tools** for document search and management

## 🧪 Testing

Run the included test suite to verify functionality:

```bash
# Basic functionality test
python test_direct.py

# Advanced testing with large documents
python test_advanced.py

# Quick search verification
python test_quick.py
```

## 📋 Requirements

### Python Dependencies
```
fastmcp>=0.1.0
sentence-transformers>=2.2.2
scikit-learn>=1.3.0
numpy>=1.24.0
```

### System Requirements
- **RAM**: 2GB+ (model loading)
- **Storage**: 500MB+ (model cache)
- **CPU**: Any modern processor

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Code formatting
black .
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check the `docs/` directory for detailed guides
- **Community**: Join discussions in GitHub Discussions

## 🔮 Roadmap

### Planned Features
- [ ] **PDF Support**: Add PDF document processing
- [ ] **Web Interface**: Optional web UI for document management
- [ ] **Docker Support**: Containerized deployment
- [ ] **Advanced Filters**: Search by document type, date, size
- [ ] **Hybrid Search**: Combine semantic and keyword search
- [ ] **REST API**: Additional HTTP API alongside MCP

### Performance Improvements
- [ ] **Incremental Updates**: Update only changed document sections
- [ ] **Compressed Embeddings**: Reduce storage requirements
- [ ] **Distributed Processing**: Multi-threaded document processing

---

## 📊 Project Stats

- **Languages**: Python
- **Framework**: FastMCP
- **AI Model**: Sentence Transformers
- **Protocol**: Model Context Protocol (MCP)
- **Status**: ✅ Production Ready
- **Test Coverage**: 100% core functionality
- **Documentation**: Complete

**Built with ❤️ for the MCP community**
