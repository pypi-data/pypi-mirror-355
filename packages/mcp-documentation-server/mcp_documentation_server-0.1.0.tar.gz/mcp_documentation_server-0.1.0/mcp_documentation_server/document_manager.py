import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib


class DocumentManager:
    """Gestisce il caricamento, salvataggio e metadati dei documenti."""
    
    def __init__(self, data_dir: Path, metadata_file: Path):
        self.data_dir = Path(data_dir)
        self.metadata_file = Path(metadata_file)
        self.data_dir.mkdir(exist_ok=True)
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Carica i metadati dai file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self):
        """Salva i metadati su file."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Calcola l'hash MD5 di un file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def scan_for_new_documents(self) -> List[Dict]:
        """Scansiona la directory data per nuovi documenti .txt e .md."""
        new_documents = []
        
        for file_path in self.data_dir.rglob("*"):
            if file_path.suffix.lower() in ['.txt', '.md'] and file_path.is_file():
                file_id = str(file_path.relative_to(self.data_dir))
                file_hash = self._get_file_hash(file_path)
                
                # Controlla se il file è nuovo o modificato
                if (file_id not in self.metadata or 
                    self.metadata[file_id].get('hash') != file_hash):
                    
                    doc_info = {
                        'id': file_id,
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'hash': file_hash,
                        'last_modified': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        'added_date': datetime.now().isoformat(),
                        'type': file_path.suffix.lower()[1:]  # rimuove il punto
                    }
                    
                    # Leggi il contenuto
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        doc_info['content'] = content
                        doc_info['char_count'] = len(content)
                        doc_info['line_count'] = len(content.splitlines())
                    except Exception as e:
                        doc_info['error'] = f"Errore lettura file: {str(e)}"
                        continue
                    
                    new_documents.append(doc_info)
                    self.metadata[file_id] = doc_info
        
        if new_documents:
            self._save_metadata()
        
        return new_documents
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Restituisce i metadati di un documento specifico."""
        return self.metadata.get(doc_id)
    
    def list_documents(self) -> List[Dict]:
        """Restituisce la lista di tutti i documenti con metadati."""
        return list(self.metadata.values())
    
    def remove_document(self, doc_id: str) -> bool:
        """Rimuove un documento dai metadati."""
        if doc_id in self.metadata:
            del self.metadata[doc_id]
            self._save_metadata()
            return True
        return False
    
    def get_upload_path(self) -> str:
        """Restituisce il path dove caricare i documenti."""
        return str(self.data_dir.absolute())
