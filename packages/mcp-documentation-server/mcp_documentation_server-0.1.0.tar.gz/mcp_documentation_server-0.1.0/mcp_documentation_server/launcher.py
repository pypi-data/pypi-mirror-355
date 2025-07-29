#!/usr/bin/env python3
"""
Standalone launcher for MCP Documentation Server.
This script can be used to start the server directly.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

def setup_logging(level: str):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp-documentation-server.log')
        ]
    )

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="MCP Documentation Server - Semantic search over technical documentation"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=os.getenv("MCP_DOC_BASE_DIR", str(Path.cwd())),
        help="Base directory for the server (default: current directory)"
    )
    parser.add_argument(
        "--data-dir", 
        type=str,
        default=os.getenv("MCP_DOC_DATA_DIR", "data"),
        help="Directory containing documentation files (default: data)"
    )
    parser.add_argument(
        "--embeddings-dir",
        type=str, 
        default=os.getenv("MCP_DOC_EMBEDDINGS_DIR", "embeddings"),
        help="Directory for embeddings cache (default: embeddings)"
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default=os.getenv("MCP_DOC_METADATA_FILE", "metadata.json"),
        help="Metadata file path (default: metadata.json)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=os.getenv("MCP_DOC_LOG_LEVEL", "INFO"),
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Run installation and configuration wizard"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="MCP Documentation Server 0.1.0"
    )
    
    args = parser.parse_args()
      # Handle installation mode
    if args.install:
        try:
            from .install import main as install_main
            install_main()
            return
        except ImportError:
            print("Error: install.py not found. Please ensure it's in the same directory.")
            sys.exit(1)
    
    # Setup environment variables
    os.environ["MCP_DOC_BASE_DIR"] = args.base_dir
    os.environ["MCP_DOC_DATA_DIR"] = args.data_dir
    os.environ["MCP_DOC_EMBEDDINGS_DIR"] = args.embeddings_dir
    os.environ["MCP_DOC_METADATA_FILE"] = args.metadata_file
    os.environ["MCP_DOC_LOG_LEVEL"] = args.log_level
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Start the server
    try:
        from .server import main as server_main
        print(f"Starting MCP Documentation Server...")
        print(f"Base directory: {args.base_dir}")
        print(f"Data directory: {args.data_dir}")
        print(f"Log level: {args.log_level}")
        print("Press Ctrl+C to stop the server")
        server_main()
    except ImportError as e:
        print(f"Error: Could not import server module: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
