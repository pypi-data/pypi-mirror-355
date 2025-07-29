import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class SemanticSearchEngine:
    """Engine per ricerca semantica usando embeddings."""
    
    def __init__(self, embeddings_dir: Path, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(exist_ok=True)
        self.model_name = model_name
        self.model = None
        self.embeddings_cache = {}
        self.chunks_cache = {}
        
    def _load_model(self):
        """Carica il modello sentence-transformers lazy loading."""
        if self.model is None:
            print(f"Caricamento modello {self.model_name}...")
            self.model = SentenceTransformer(self.model_name)
            print("Modello caricato!")
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """Divide il testo in chunks con overlap per mantenere il contesto."""
        # Pulisce il testo
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= chunk_size:
            return [{
                'text': text,
                'start_char': 0,
                'end_char': len(text),
                'chunk_id': 0
            }]
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Determina la fine del chunk
            end = min(start + chunk_size, len(text))
            
            # Se non siamo alla fine, cerca un buon punto di taglio
            if end < len(text):
                # Cerca l'ultimo spazio, punto o a capo prima della fine
                for char in ['\n\n', '\n', '. ', '! ', '? ', ' ']:
                    last_occurrence = text.rfind(char, start, end)
                    if last_occurrence > start + chunk_size // 2:  # Non tagliare troppo presto
                        end = last_occurrence + len(char)
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    'text': chunk_text,
                    'start_char': start,
                    'end_char': end,
                    'chunk_id': chunk_id
                })
                chunk_id += 1
            
            # Calcola il prossimo start con overlap
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def _get_embedding_file_path(self, doc_id: str) -> Path:
        """Restituisce il path del file di embeddings per un documento."""
        safe_filename = re.sub(r'[<>:"/\\|?*]', '_', doc_id)
        return self.embeddings_dir / f"{safe_filename}.pkl"
    
    def process_document(self, doc_id: str, content: str) -> bool:
        """Processa un documento creando chunks e embeddings."""
        try:
            self._load_model()
            
            # Crea chunks
            chunks = self._chunk_text(content)
            if not chunks:
                return False
            
            # Genera embeddings per ogni chunk
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.model.encode(chunk_texts, convert_to_numpy=True)
            
            # Salva embeddings e chunks
            embedding_data = {
                'chunks': chunks,
                'embeddings': embeddings,
                'model_name': self.model_name
            }
            
            embedding_file = self._get_embedding_file_path(doc_id)
            with open(embedding_file, 'wb') as f:
                pickle.dump(embedding_data, f)
            
            # Cache in memoria
            self.embeddings_cache[doc_id] = embeddings
            self.chunks_cache[doc_id] = chunks
            
            return True
            
        except Exception as e:
            print(f"Errore nel processare documento {doc_id}: {str(e)}")
            return False
    
    def _load_document_embeddings(self, doc_id: str) -> Optional[Tuple[np.ndarray, List[Dict]]]:
        """Carica embeddings e chunks di un documento dalla cache o da file."""
        # Controlla cache in memoria
        if doc_id in self.embeddings_cache and doc_id in self.chunks_cache:
            return self.embeddings_cache[doc_id], self.chunks_cache[doc_id]
        
        # Carica da file
        embedding_file = self._get_embedding_file_path(doc_id)
        if not embedding_file.exists():
            return None
        
        try:
            with open(embedding_file, 'rb') as f:
                data = pickle.load(f)
            
            embeddings = data['embeddings']
            chunks = data['chunks']
            
            # Aggiorna cache
            self.embeddings_cache[doc_id] = embeddings
            self.chunks_cache[doc_id] = chunks
            
            return embeddings, chunks
            
        except Exception as e:
            print(f"Errore nel caricare embeddings per {doc_id}: {str(e)}")
            return None
    
    def search(self, query: str, document_ids: List[str], top_k: int = 5) -> List[Dict]:
        """Cerca semanticamente nei documenti specificati."""
        try:
            self._load_model()
            
            # Genera embedding della query
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            
            all_results = []
            
            for doc_id in document_ids:
                # Carica embeddings del documento
                doc_data = self._load_document_embeddings(doc_id)
                if doc_data is None:
                    continue
                
                doc_embeddings, chunks = doc_data
                
                # Calcola similarità
                similarities = cosine_similarity(query_embedding, doc_embeddings)[0]
                
                # Crea risultati per questo documento
                for i, similarity in enumerate(similarities):
                    chunk = chunks[i]
                    all_results.append({
                        'document_id': doc_id,
                        'chunk_id': chunk['chunk_id'],
                        'text': chunk['text'],
                        'start_char': chunk['start_char'],
                        'end_char': chunk['end_char'],
                        'similarity_score': float(similarity),
                        'relevance': f"{similarity:.2f}"
                    })
            
            # Ordina per similarità e prendi i top_k
            all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            print(f"Errore nella ricerca: {str(e)}")
            return []
    
    def remove_document_embeddings(self, doc_id: str) -> bool:
        """Rimuove gli embeddings di un documento."""
        try:
            # Rimuovi dalla cache
            self.embeddings_cache.pop(doc_id, None)
            self.chunks_cache.pop(doc_id, None)
            
            # Rimuovi file
            embedding_file = self._get_embedding_file_path(doc_id)
            if embedding_file.exists():
                embedding_file.unlink()
            
            return True
            
        except Exception as e:
            print(f"Errore nella rimozione embeddings per {doc_id}: {str(e)}")
            return False
