#!/usr/bin/env python3
"""
Test Rapido - Verifica Risultati Ricerca Semantica
"""

import asyncio
import sys
from pathlib import Path

# Aggiungiamo il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from document_manager import DocumentManager
from search_engine import SemanticSearchEngine

def test_search_results():
    """Test rapido per verificare i risultati di ricerca"""
    
    print("🔍 Test Rapido - Ricerca Semantica")
    print("=" * 40)
    
    # Inizializzazione
    data_dir = Path("data")
    embeddings_dir = Path("embeddings")
    metadata_file = Path("metadata.json")
    
    doc_manager = DocumentManager(data_dir, metadata_file)
    search_engine = SemanticSearchEngine(embeddings_dir)
    
    # Ottieni documenti disponibili
    documents = doc_manager.list_documents()
    if not documents:
        print("❌ Nessun documento trovato!")
        return
    
    document_ids = [doc['id'] for doc in documents]
    print(f"📄 Documento: {documents[0]['name']}")
    
    # Test con query specifiche
    test_queries = [
        "Docker containerizzazione",
        "microservizi comunicazione",
        "JWT token sicurezza",
        "machine learning algoritmi"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        
        try:
            results = search_engine.search(query, document_ids, top_k=2)
            
            if results:
                print(f"   ✅ {len(results)} risultati trovati:")
                for i, result in enumerate(results, 1):
                    score = result.get('similarity_score', 0)
                    text = result.get('text', '')
                    
                    # Mostra solo i primi 150 caratteri
                    display_text = text[:150].replace('\n', ' ').strip()
                    if len(text) > 150:
                        display_text += "..."
                    
                    print(f"   {i}. Score: {score:.4f}")
                    print(f"      📝 {display_text}")
            else:
                print("   ❌ Nessun risultato")
                
        except Exception as e:
            print(f"   ❌ Errore: {e}")
    
    print("\n" + "=" * 40)
    print("🎯 Test completato!")

if __name__ == "__main__":
    test_search_results()
