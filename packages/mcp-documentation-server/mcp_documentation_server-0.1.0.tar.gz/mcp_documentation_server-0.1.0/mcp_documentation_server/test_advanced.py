#!/usr/bin/env python3
"""
Test Avanzato - Documentazione MCP (639KB)
Test completo con documentazione tecnica reale sui server MCP
"""

import asyncio
import sys
import time
from pathlib import Path

# Aggiungiamo il path del progetto
sys.path.insert(0, str(Path(__file__).parent))

from document_manager import DocumentManager
from search_engine import SemanticSearchEngine

class AdvancedMCPTest:
    """Test avanzato per documentazione MCP"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.embeddings_dir = Path("embeddings")
        self.metadata_file = Path("metadata.json")
        
        self.doc_manager = DocumentManager(self.data_dir, self.metadata_file)
        self.search_engine = SemanticSearchEngine(self.embeddings_dir)
        
        # Queries di test tecniche specifiche per MCP
        self.test_queries = {
            "basic_concepts": [
                "MCP Model Context Protocol",
                "server client architecture",
                "transport protocols stdio"
            ],
            "clients": [
                "Claude Desktop client",
                "Anthropic Claude implementation",
                "client feature support"
            ],
            "tools": [
                "tools implementation MCP",
                "function calling tools",
                "tool discovery mechanism"
            ],
            "resources": [
                "resources MCP protocol",
                "resource management access",
                "file system resources"
            ],
            "prompts": [
                "prompt templates MCP",
                "prompt engineering",
                "dynamic prompts generation"
            ],
            "technical": [
                "JSON-RPC protocol MCP",
                "TypeScript implementation",
                "Python MCP servers"
            ],
            "specific_features": [
                "sampling capability",
                "roots directory access",
                "discovery protocol"
            ]
        }
    
    def print_header(self, title):
        """Stampa header formattato"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Stampa sezione formattata"""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    async def setup_documents(self):
        """Setup e processamento documenti"""
        self.print_header("SETUP DOCUMENTI MCP")
        
        # Scansiona documenti
        new_docs = self.doc_manager.scan_for_new_documents()
        
        total_docs = 0
        total_size = 0
        
        for doc in new_docs:
            if doc['name'] == 'documentazione_tecnica_mcp.md':
                print(f"📄 Documento MCP trovato: {doc['name']}")
                print(f"   📊 Dimensioni: {doc['size']:,} bytes ({doc['size']/1024:.1f} KB)")
                print(f"   📝 Caratteri: {doc['char_count']:,}")
                print(f"   📃 Righe: {doc['line_count']:,}")
                
                # Processa embeddings
                print(f"🧠 Processamento embeddings...")
                start_time = time.time()
                
                self.search_engine.process_document(doc['id'], doc['content'])
                
                process_time = time.time() - start_time
                print(f"   ⏱️ Tempo processamento: {process_time:.2f} secondi")
                
                total_docs += 1
                total_size += doc['size']
        
        print(f"\n✅ Setup completato:")
        print(f"   📚 Documenti processati: {total_docs}")
        print(f"   💾 Dimensione totale: {total_size:,} bytes")
        
        return total_docs > 0
    
    def test_category_searches(self, category_name, queries, document_ids):
        """Testa una categoria di query"""
        self.print_section(f"Test {category_name.title()}")
        
        results_summary = []
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Query {i}: '{query}'")
            
            try:
                start_time = time.time()
                results = self.search_engine.search(query, document_ids, top_k=3)
                search_time = time.time() - start_time
                
                if results:
                    best_score = results[0].get('similarity_score', 0)
                    print(f"   ⚡ Tempo: {search_time*1000:.1f}ms | Top Score: {best_score:.4f}")
                    
                    # Mostra solo il miglior risultato per brevità
                    result = results[0]
                    text = result.get('text', '')[:120].replace('\n', ' ').strip()
                    if len(result.get('text', '')) > 120:
                        text += "..."
                    
                    print(f"   🎯 Miglior match: {text}")
                    
                    results_summary.append({
                        'query': query,
                        'score': best_score,
                        'time_ms': search_time * 1000,
                        'found': True
                    })
                else:
                    print(f"   ❌ Nessun risultato trovato")
                    results_summary.append({
                        'query': query,
                        'score': 0,
                        'time_ms': search_time * 1000,
                        'found': False
                    })
                    
            except Exception as e:
                print(f"   ❌ Errore: {e}")
                results_summary.append({
                    'query': query,
                    'score': 0,
                    'time_ms': 0,
                    'found': False,
                    'error': str(e)
                })
        
        return results_summary
    
    def analyze_performance(self, all_results):
        """Analizza le performance complessive"""
        self.print_header("ANALISI PERFORMANCE")
        
        total_queries = 0
        successful_queries = 0
        total_time = 0
        scores = []
        
        for category, results in all_results.items():
            for result in results:
                total_queries += 1
                total_time += result.get('time_ms', 0)
                
                if result['found']:
                    successful_queries += 1
                    scores.append(result['score'])
        
        success_rate = (successful_queries / total_queries) * 100 if total_queries > 0 else 0
        avg_time = total_time / total_queries if total_queries > 0 else 0
        avg_score = sum(scores) / len(scores) if scores else 0
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        print(f"📊 Statistiche Generali:")
        print(f"   🎯 Query totali: {total_queries}")
        print(f"   ✅ Query riuscite: {successful_queries}")
        print(f"   📈 Tasso successo: {success_rate:.1f}%")
        print(f"   ⚡ Tempo medio: {avg_time:.1f}ms")
        
        if scores:
            print(f"\n📊 Qualità Risultati:")
            print(f"   🏆 Score medio: {avg_score:.4f}")
            print(f"   🥇 Score massimo: {max_score:.4f}")
            print(f"   🥉 Score minimo: {min_score:.4f}")
        
        # Top 5 migliori risultati
        all_results_flat = []
        for category, results in all_results.items():
            for result in results:
                if result['found']:
                    all_results_flat.append({**result, 'category': category})
        
        top_results = sorted(all_results_flat, key=lambda x: x['score'], reverse=True)[:5]
        
        if top_results:
            print(f"\n🏆 Top 5 Migliori Risultati:")
            for i, result in enumerate(top_results, 1):
                print(f"   {i}. [{result['score']:.4f}] {result['query']} ({result['category']})")
    
    async def run_full_test(self):
        """Esegue il test completo"""
        start_total = time.time()
        
        # Setup
        documents_ready = await self.setup_documents()
        if not documents_ready:
            print("❌ Nessun documento MCP trovato per i test!")
            return
        
        # Ottieni document IDs
        documents = self.doc_manager.list_documents()
        document_ids = [doc['id'] for doc in documents]
        
        # Trova il documento MCP
        mcp_doc = None
        for doc in documents:
            if 'mcp' in doc['name'].lower():
                mcp_doc = doc
                break
        
        if not mcp_doc:
            print("❌ Documento MCP non trovato!")
            return
        
        print(f"\n🎯 Documento target: {mcp_doc['name']}")
        print(f"   📊 {mcp_doc['size']:,} bytes, {mcp_doc.get('char_count', 0):,} caratteri")
        
        # Esegui test per categoria
        all_results = {}
        
        for category, queries in self.test_queries.items():
            results = self.test_category_searches(category, queries, document_ids)
            all_results[category] = results
        
        # Analisi finale
        self.analyze_performance(all_results)
        
        total_time = time.time() - start_total
        print(f"\n⏱️ Tempo totale test: {total_time:.2f} secondi")
        print(f"🎉 Test avanzato completato!")

async def main():
    """Funzione principale"""
    test = AdvancedMCPTest()
    await test.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
