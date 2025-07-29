#!/usr/bin/env python3
"""
Test diretto delle funzionalità del server MCP Documentation
Questo script testa direttamente i moduli senza passare per il protocollo MCP
"""

import asyncio
import sys
import os
from pathlib import Path

# Aggiungiamo il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from document_manager import DocumentManager
from search_engine import SemanticSearchEngine

async def test_direct():
    """Test diretto delle funzionalità"""
    
    print("🧪 Test Diretto - MCP Documentation Server")
    print("=" * 50)
      # Inizializzazione
    data_dir = Path("data")
    embeddings_dir = Path("embeddings")
    metadata_file = Path("metadata.json")
    
    doc_manager = DocumentManager(data_dir, metadata_file)
    search_engine = SemanticSearchEngine(embeddings_dir)
    
    print(f"📁 Data directory: {data_dir.absolute()}")
    print(f"🧠 Embeddings directory: {embeddings_dir.absolute()}")
    print()
      # Test 1: Scansiona e processa documenti
    print("📋 Test 1: Scansione e Processamento Documenti")
    print("-" * 40)
    try:
        # Prima scansiona per nuovi documenti
        new_docs = doc_manager.scan_for_new_documents()
        print(f"📥 Trovati {len(new_docs)} nuovi documenti da processare:")
        
        for doc in new_docs:
            print(f"  - {doc['name']} ({doc['size']} bytes)")
            
            # Processa il documento per la ricerca semantica
            doc_id = doc['id']
            content = doc['content']
            
            print(f"🧠 Processamento embeddings per {doc['name']}...")
            search_engine.process_document(doc_id, content)
            print(f"✅ Completato!")
        
        # Lista tutti i documenti
        documents = doc_manager.list_documents()
        print(f"\n📚 Totale documenti disponibili: {len(documents)}")
        for doc in documents:
            print(f"  - {doc['name']} ({doc['size']} bytes, {doc.get('char_count', 0)} caratteri)")
        print()
    except Exception as e:
        print(f"❌ Errore: {e}")
        return
      # Test 2: Ricerche semantiche
    print("🔍 Test 2: Ricerche Semantiche")
    print("-" * 30)
    
    # Ottieni la lista degli ID dei documenti per la ricerca
    documents = doc_manager.list_documents()
    if not documents:
        print("❌ Nessun documento disponibile per i test di ricerca")
        return
    
    document_ids = [doc['id'] for doc in documents]
    print(f"📄 Documenti disponibili per ricerca: {[doc['name'] for doc in documents]}")
    
    queries = [
        "microservizi architettura",
        "database NoSQL esempi", 
        "Docker container",
        "machine learning algoritmi",
        "JWT autenticazione",
        "Kubernetes deployment"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: '{query}'")
        try:
            results = search_engine.search(query, document_ids, top_k=3)
            
            if results:
                print(f"   📊 Trovati {len(results)} risultati:")
                for j, result in enumerate(results, 1):
                    score = result.get('similarity', 0)
                    text = result.get('text', '')[:100] + "..."
                    doc_id = result.get('document_id', 'unknown')
                    print(f"   {j}. [{score:.3f}] {doc_id}")
                    print(f"      💬 {text}")
            else:
                print("   ❌ Nessun risultato trovato")
                
        except Exception as e:
            print(f"   ❌ Errore ricerca: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Test completati!")

if __name__ == "__main__":
    asyncio.run(test_direct())
