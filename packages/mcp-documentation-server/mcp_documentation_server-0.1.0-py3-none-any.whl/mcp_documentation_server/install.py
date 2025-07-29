#!/usr/bin/env python3
"""
Installation and configuration script for MCP Documentation Server.
This script helps users set up the server for different MCP clients.
"""

import json
import os
import sys
import subprocess
import venv
from pathlib import Path
from typing import Dict, Any

def get_user_config() -> Dict[str, Any]:
    """Get configuration from user input."""
    print("MCP Documentation Server Configuration")
    print("=" * 40)
    
    # Get base directory
    default_base = str(Path.home() / ".mcp-documentation-server")
    base_dir = input(f"Base directory (default: {default_base}): ").strip() or default_base
    
    # Get data directory for documents
    default_data = str(Path(base_dir) / "data")
    data_dir = input(f"Documents directory (default: {default_data}): ").strip() or default_data
    
    # Get log level
    log_level = input("Log level (DEBUG/INFO/WARNING/ERROR) [INFO]: ").strip().upper() or "INFO"
    if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        log_level = "INFO"
    
    return {
        "base_dir": base_dir,
        "data_dir": data_dir,
        "log_level": log_level
    }

def create_directories(config: Dict[str, Any]):
    """Create necessary directories."""
    base_path = Path(config["base_dir"])
    data_path = Path(config["data_dir"])
    
    # Create directories
    base_path.mkdir(parents=True, exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)
    (base_path / "embeddings").mkdir(exist_ok=True)
    
    print(f"Created directories:")
    print(f"  Base: {base_path}")
    print(f"  Data: {data_path}")
    print(f"  Embeddings: {base_path / 'embeddings'}")

def create_virtual_environment(base_path: Path) -> Path:
    """Create virtual environment and install the package."""
    venv_path = base_path / "venv"
    
    print(f"\nCreating virtual environment: {venv_path}")
    
    # Create virtual environment
    venv.create(venv_path, with_pip=True)
    
    # Get pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    print("Installing mcp-documentation-server...")
    
    # Try to install from PyPI first
    try:
        subprocess.run([
            str(pip_path), "install", "mcp-documentation-server"
        ], check=True, capture_output=True, text=True)
        print("✓ Package installed successfully from PyPI")
    except subprocess.CalledProcessError:
        # If PyPI fails, try to find and install from local wheel
        print("PyPI installation failed, trying local wheel...")
        try:
            # Look for wheel in current directory or common build locations
            import os
            current_dir = Path(os.getcwd())
            wheel_locations = [
                current_dir / "dist",
                current_dir.parent / "dist" if current_dir.name == "mcp_documentation_server" else None,
                Path(__file__).parent.parent / "dist"
            ]
            
            wheel_file = None
            for location in wheel_locations:
                if location and location.exists():
                    for file in location.glob("mcp_documentation_server-*.whl"):
                        wheel_file = file
                        break
                    if wheel_file:
                        break
            
            if wheel_file:
                subprocess.run([
                    str(pip_path), "install", str(wheel_file)
                ], check=True, capture_output=True, text=True)
                print(f"✓ Package installed successfully from local wheel: {wheel_file.name}")
            else:
                print("✗ No local wheel found. Please ensure the package is built or published.")
                print("You can build it with: python -m build")
                print("Then run the installer again.")
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install package: {e}")
            print("Manual installation options:")
            print(f"  From PyPI: {pip_path} install mcp-documentation-server")
            print(f"  From wheel: {pip_path} install path/to/mcp_documentation_server-*.whl")
    
    return venv_path

def create_wrapper_scripts(base_path: Path, venv_path: Path):
    """Create wrapper scripts for CLI commands."""
    scripts_dir = base_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    if sys.platform == "win32":
        # Windows batch scripts
        python_exe = venv_path / "Scripts" / "python.exe"
        
        # Main server script
        server_script = scripts_dir / "mcp-documentation-server.bat"
        server_script.write_text(f'@echo off\n"{python_exe}" -m mcp_documentation_server.server %*\n')
        
        # Installer script
        install_script = scripts_dir / "mcp-doc-install.bat"
        install_script.write_text(f'@echo off\n"{python_exe}" -m mcp_documentation_server.install %*\n')
        
        # Launcher script
        launcher_script = scripts_dir / "mcp-doc-launcher.bat"
        launcher_script.write_text(f'@echo off\n"{python_exe}" -m mcp_documentation_server.launcher %*\n')
        
    else:
        # Unix shell scripts
        python_exe = venv_path / "bin" / "python"
        
        # Main server script
        server_script = scripts_dir / "mcp-documentation-server"
        server_script.write_text(f'#!/bin/bash\n"{python_exe}" -m mcp_documentation_server.server "$@"\n')
        server_script.chmod(0o755)
        
        # Installer script
        install_script = scripts_dir / "mcp-doc-install"
        install_script.write_text(f'#!/bin/bash\n"{python_exe}" -m mcp_documentation_server.install "$@"\n')
        install_script.chmod(0o755)
        
        # Launcher script
        launcher_script = scripts_dir / "mcp-doc-launcher"
        launcher_script.write_text(f'#!/bin/bash\n"{python_exe}" -m mcp_documentation_server.launcher "$@"\n')
        launcher_script.chmod(0o755)
    
    print(f"\n✓ Created wrapper scripts in: {scripts_dir}")
    return scripts_dir

def generate_claude_config(config: Dict[str, Any], scripts_dir: Path) -> str:
    """Generate Claude Desktop configuration."""
    server_cmd = str(scripts_dir / ("mcp-documentation-server.bat" if sys.platform == "win32" else "mcp-documentation-server"))
    claude_config = {
        "mcpServers": {
            "documentation": {
                "command": server_cmd,
                "env": {
                    "MCP_DOC_BASE_DIR": config["base_dir"],
                    "MCP_DOC_DATA_DIR": "data",
                    "MCP_DOC_LOG_LEVEL": config["log_level"]
                }
            }
        }
    }
    return json.dumps(claude_config, indent=2)

def generate_cursor_config(config: Dict[str, Any], scripts_dir: Path) -> str:
    """Generate Cursor MCP configuration."""
    server_cmd = str(scripts_dir / ("mcp-documentation-server.bat" if sys.platform == "win32" else "mcp-documentation-server"))
    cursor_config = {
        "mcpServers": {
            "documentation": {
                "command": server_cmd,
                "env": {
                    "MCP_DOC_BASE_DIR": config["base_dir"],
                    "MCP_DOC_DATA_DIR": "data",
                    "MCP_DOC_LOG_LEVEL": config["log_level"]
                }
            }
        }
    }
    return json.dumps(cursor_config, indent=2)

def generate_vscode_config(config: Dict[str, Any], scripts_dir: Path) -> str:
    """Generate VS Code MCP configuration."""
    server_cmd = str(scripts_dir / ("mcp-documentation-server.bat" if sys.platform == "win32" else "mcp-documentation-server"))
    vscode_config = {
        "mcpServers": {
            "documentation": {
                "command": server_cmd,
                "env": {
                    "MCP_DOC_BASE_DIR": config["base_dir"],
                    "MCP_DOC_DATA_DIR": "data", 
                    "MCP_DOC_LOG_LEVEL": config["log_level"]
                }
            }
        }
    }
    return json.dumps(vscode_config, indent=2)

def save_configs(config: Dict[str, Any], base_path: Path, scripts_dir: Path):
    """Save configuration files."""
    configs_dir = base_path / "configs"
    configs_dir.mkdir(exist_ok=True)
    
    # Save Claude config
    claude_config = generate_claude_config(config, scripts_dir)
    (configs_dir / "claude_desktop_config.json").write_text(claude_config)
    
    # Save Cursor config  
    cursor_config = generate_cursor_config(config, scripts_dir)
    (configs_dir / "cursor_mcp_config.json").write_text(cursor_config)
    
    # Save VS Code config
    vscode_config = generate_vscode_config(config, scripts_dir)
    (configs_dir / "vscode_mcp_config.json").write_text(vscode_config)
    
    print(f"\n✓ Configuration files saved to: {configs_dir}")
    print(f"  Claude Desktop: claude_desktop_config.json")
    print(f"  Cursor: cursor_mcp_config.json")
    print(f"  VS Code: vscode_mcp_config.json")

def print_setup_instructions(config: Dict[str, Any], base_path: Path, scripts_dir: Path):
    """Print setup instructions for different clients."""
    configs_dir = base_path / "configs"
    
    print("\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    
    print("\n1. CLAUDE DESKTOP SETUP:")
    print("   Copy the contents of:", configs_dir / "claude_desktop_config.json")
    if sys.platform == "win32":
        print("   To: %APPDATA%\\Claude\\claude_desktop_config.json")
    elif sys.platform == "darwin":
        print("   To: ~/Library/Application Support/Claude/claude_desktop_config.json")
    else:
        print("   To: ~/.config/claude/claude_desktop_config.json")
    
    print("\n2. CURSOR SETUP:")
    print("   Copy the contents of:", configs_dir / "cursor_mcp_config.json")
    print("   To your Cursor MCP configuration file")
    
    print("\n3. VS CODE SETUP:")
    print("   Copy the contents of:", configs_dir / "vscode_mcp_config.json")
    print("   To your VS Code MCP configuration file")
    
    print(f"\n4. DOCUMENT MANAGEMENT:")
    print(f"   Add your documentation files to: {config['data_dir']}")
    print("   Supported formats: .txt, .md")
    
    print("\n5. CLI USAGE (Optional):")
    print(f"   You can also use the CLI scripts directly:")
    if sys.platform == "win32":
        print(f"   - Server: {scripts_dir}\\mcp-documentation-server.bat")
        print(f"   - Install: {scripts_dir}\\mcp-doc-install.bat")
        print(f"   - Launcher: {scripts_dir}\\mcp-doc-launcher.bat")
    else:
        print(f"   - Server: {scripts_dir}/mcp-documentation-server")
        print(f"   - Install: {scripts_dir}/mcp-doc-install")
        print(f"   - Launcher: {scripts_dir}/mcp-doc-launcher")
    
    print("\n6. MCP TOOLS AVAILABLE:")
    print("   After setup, you can use these MCP tools:")
    print("   - get_upload_info: Get upload instructions")
    print("   - list_documents: List all documents") 
    print("   - search_documents: Search in documents")
    print("   - remove_document: Remove a document")

def main():
    """Main installation function."""
    print("MCP Documentation Server - Installation & Configuration")
    print("=" * 60)
    
    # Get user configuration
    config = get_user_config()
    base_path = Path(config["base_dir"])
    
    # Create directories
    create_directories(config)
    
    # Create virtual environment and install package
    venv_path = create_virtual_environment(base_path)
    
    # Create wrapper scripts
    scripts_dir = create_wrapper_scripts(base_path, venv_path)
    
    # Save configuration files
    save_configs(config, base_path, scripts_dir)
    
    # Print setup instructions
    print_setup_instructions(config, base_path, scripts_dir)
    
    print("\n" + "=" * 60)
    print("Installation completed successfully!")
    print("The server is now installed in an isolated virtual environment.")
    print("Follow the setup instructions above to configure your MCP client.")
    print("=" * 60)

if __name__ == "__main__":
    main()
