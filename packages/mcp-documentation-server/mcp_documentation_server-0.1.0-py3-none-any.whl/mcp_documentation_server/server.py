#!/usr/bin/env python3
"""
MCP Server for semantic search over technical documentation.
Supports .txt and .md files with multilingual semantic search.
"""

import asyncio
import os
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from fastmcp import FastMCP
from .document_manager import DocumentManager
from .search_engine import SemanticSearchEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
def get_config():
    """Get configuration from environment variables or defaults."""
    base_dir = Path(os.getenv("MCP_DOC_BASE_DIR", Path(__file__).parent))
    
    return {
        "base_dir": base_dir,
        "data_dir": base_dir / os.getenv("MCP_DOC_DATA_DIR", "data"),
        "embeddings_dir": base_dir / os.getenv("MCP_DOC_EMBEDDINGS_DIR", "embeddings"),
        "metadata_file": base_dir / os.getenv("MCP_DOC_METADATA_FILE", "metadata.json"),
        "log_level": os.getenv("MCP_DOC_LOG_LEVEL", "INFO"),
        "cache_size": int(os.getenv("MCP_DOC_CACHE_SIZE", "1000")),
    }

# Get configuration
config = get_config()

# Set log level
logger.setLevel(getattr(logging, config["log_level"].upper()))

# Initialize components
doc_manager = DocumentManager(config["data_dir"], config["metadata_file"])
search_engine = SemanticSearchEngine(config["embeddings_dir"])

# Create MCP server
mcp = FastMCP("Documentation Search Server")


@mcp.tool()
async def get_upload_info() -> str:
    """
    Restituisce le informazioni su dove caricare i file di documentazione.
    Supporta file .txt e .md per la ricerca semantica.
    """
    upload_path = doc_manager.get_upload_path()
    
    return f"""
**Upload Path**: `{upload_path}`

**Istruzioni**:
1. Copia i tuoi file .txt o .md nella directory sopra indicata
2. I file verranno automaticamente rilevati e processati
3. Usa `list_documents` per vedere i documenti caricati
4. Usa `search_documents` per cercare nei contenuti

**Formati supportati**: .txt, .md
**Encoding**: UTF-8
**Lingue**: Multilingue (italiano, inglese, ecc.)
"""


@mcp.tool()
async def list_documents() -> str:
    """
    Lista tutti i documenti caricati con i loro metadati.
    Mostra informazioni su nome, dimensione, data di caricamento, ecc.
    """
    # Scansiona per nuovi documenti
    new_docs = doc_manager.scan_for_new_documents()
    
    # Processa nuovi documenti
    for doc in new_docs:
        if 'content' in doc:
            success = search_engine.process_document(doc['id'], doc['content'])
            if success:
                print(f"Processato: {doc['name']}")
            else:
                print(f"Errore nel processare: {doc['name']}")
    
    # Lista tutti i documenti
    documents = doc_manager.list_documents()
    
    if not documents:
        return "Nessun documento trovato. Usa `get_upload_info` per vedere dove caricare i file."
    
    result = "**Documenti Caricati**:\n\n"
    
    for doc in documents:
        result += f" **{doc['name']}**\n"
        result += f"   ID: `{doc['id']}`\n"
        result += f"   Tipo: {doc['type'].upper()}\n"
        result += f"   Dimensione: {doc['size']:,} bytes\n"
        result += f"   Caratteri: {doc.get('char_count', 'N/A'):,}\n"
        result += f"   Righe: {doc.get('line_count', 'N/A'):,}\n"
        result += f"   Aggiunto: {doc['added_date'][:19]}\n"
        if 'error' in doc:
            result += f"   Errore: {doc['error']}\n"
        result += "\n"
    
    return result


@mcp.tool()
async def search_documents(
    query: str,
    document_ids: Optional[str] = None,
    max_results: int = 5
) -> str:
    """
    Cerca semanticamente nei documenti specificati.
    
    Args:
        query: La query di ricerca (può essere in italiano o inglese)
        document_ids: ID dei documenti dove cercare (separati da virgola). Se None, cerca in tutti.
        max_results: Numero massimo di risultati da restituire (default: 5)
    """
    if not query.strip():
        return "Errore: Query di ricerca vuota."
    
    # Ottieni lista documenti
    all_documents = doc_manager.list_documents()
    if not all_documents:
        return "Nessun documento disponibile. Carica prima alcuni file."
    
    # Determina in quali documenti cercare
    if document_ids:
        # Parsa gli ID specificati
        target_ids = [id_.strip() for id_ in document_ids.split(',')]
        # Verifica che esistano
        available_ids = [doc['id'] for doc in all_documents]
        target_ids = [id_ for id_ in target_ids if id_ in available_ids]
        
        if not target_ids:
            return f"Errore: Nessuno degli ID specificati è valido.\nID disponibili: {', '.join(available_ids)}"
    else:
        # Cerca in tutti i documenti
        target_ids = [doc['id'] for doc in all_documents]
    
    # Esegui ricerca
    results = search_engine.search(query, target_ids, max_results)
    
    if not results:
        return f"No results found for: '{query}'\nTry different or more general terms."
    
    # Formatta risultati
    response = f"**Search Results for**: '{query}'\n"
    response += f"**Trovati**: {len(results)} risultati\n\n"
    
    for i, result in enumerate(results, 1):
        doc_name = next((doc['name'] for doc in all_documents if doc['id'] == result['document_id']), result['document_id'])
        
        response += f"**{i}. {doc_name}**\n"
        response += f"**Rilevanza**: {result['relevance']}/1.00\n"
        response += f"**Posizione**: caratteri {result['start_char']}-{result['end_char']}\n"
        response += f"**Contenuto**:\n```\n{result['text'][:300]}{'...' if len(result['text']) > 300 else ''}\n```\n\n"
    
    return response


@mcp.tool()
async def remove_document(document_id: str) -> str:
    """
    Rimuove un documento dal sistema (metadati ed embeddings).
    
    Args:
        document_id: L'ID del documento da rimuovere
    """
    if not document_id.strip():
        return "Errore: ID documento non specificato."
    
    # Verifica che il documento esista
    doc = doc_manager.get_document(document_id)
    if not doc:
        available_docs = doc_manager.list_documents()
        available_ids = [d['id'] for d in available_docs]
        return f"Documento non trovato: '{document_id}'\nID disponibili: {', '.join(available_ids)}"
    
    # Rimuovi embeddings
    search_engine.remove_document_embeddings(document_id)
    
    # Rimuovi metadati
    success = doc_manager.remove_document(document_id)
    
    if success:
        return f"Documento rimosso con successo: '{doc['name']}'\nIl file fisico rimane nella directory data."
    else:
        return f"Errore nella rimozione del documento: '{document_id}'"


def main():
    """Main function to start the MCP server."""
    logger.info("Starting MCP Documentation Server")
    logger.info(f"Configuration: {config}")
    logger.info(f"Data directory: {config['data_dir']}")
    logger.info(f"Embeddings directory: {config['embeddings_dir']}")
    logger.info("Model: paraphrase-multilingual-mpnet-base-v2")
    
    # Ensure directories exist
    config["data_dir"].mkdir(exist_ok=True)
    config["embeddings_dir"].mkdir(exist_ok=True)
    
    # Start the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
