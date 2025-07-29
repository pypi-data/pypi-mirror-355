# MCP Documentation Search Server

## 📋 Descrizione del Progetto

Il **MCP Documentation Search Server** è un server Model Context Protocol (MCP) progettato per facilitare la ricerca semantica all'interno di documentazione tecnica. Il server consente di caricare file di testo (.txt) e Markdown (.md) e di effettuare ricerche semantiche avanzate utilizzando embeddings multilingue.

## 🎯 Obiettivi

### Obiettivo Principale
Fornire un sistema di ricerca semantica efficace per consultare rapidamente documentazione tecnica distribuita in più file.

### Obiettivi Specifici
- **Caricamento Semplice**: Permettere agli utenti di caricare facilmente file di documentazione
- **Ricerca Semantica**: Implementare ricerca basata su significato, non solo parole chiave
- **Supporto Multilingue**: Supportare documentazione in italiano, inglese e altre lingue
- **Gestione Metadati**: Tracciare informazioni sui file caricati (dimensioni, date, hash)
- **Performance Ottimizzate**: Cache degli embeddings per velocizzare ricerche successive

## 🏗️ Architettura del Sistema

### Componenti Principali

1. **Server MCP** (`server.py`)
   - Server principale basato su FastMCP
   - Implementa 4 tools MCP per l'interazione client

2. **Document Manager** (`document_manager.py`)
   - Gestisce caricamento e metadati dei documenti
   - Scansione automatica della directory `data/`
   - Tracking delle modifiche tramite hash MD5

3. **Search Engine** (`search_engine.py`)
   - Motore di ricerca semantica
   - Chunking intelligente dei documenti
   - Calcolo embeddings e similarità coseno

### Tecnologie Utilizzate

- **FastMCP**: Framework per server MCP
- **Sentence Transformers**: Modello `paraphrase-multilingual-mpnet-base-v2`
- **Scikit-learn**: Calcolo similarità coseno
- **NumPy**: Operazioni sui vettori
- **Pathlib**: Gestione file system

## 🛠️ Tools MCP Implementati

1. **`get_upload_info`**
   - Mostra il path dove caricare i file
   - Fornisce istruzioni per l'uso

2. **`list_documents`**
   - Lista tutti i documenti caricati
   - Mostra metadati completi per ogni file
   - Auto-rileva e processa nuovi file

3. **`search_documents`**
   - Ricerca semantica nei documenti
   - Parametri: query, document_ids (opzionale), max_results
   - Restituisce risultati ordinati per rilevanza

4. **`remove_document`**
   - Rimuove documento dai metadati
   - Elimina embeddings associati

## 💾 Struttura Dati

### Directory
```
mcp-documentation-server/
├── server.py              # Server MCP principale
├── document_manager.py    # Gestione documenti
├── search_engine.py       # Motore ricerca semantica
├── data/                  # File .txt/.md caricati dall'utente
├── embeddings/            # Cache embeddings (file .pkl)
├── metadata.json          # Metadati documenti
├── venv/                  # Ambiente virtuale Python
└── .gitignore            # File git ignore
```

### Metadati Documento
```json
{
  "id": "path/relativo/file.md",
  "name": "file.md",
  "path": "/path/assoluto/file.md",
  "size": 1024,
  "hash": "md5_hash",
  "last_modified": "2025-06-14T00:08:33",
  "added_date": "2025-06-14T00:08:33",
  "type": "md",
  "content": "contenuto del file...",
  "char_count": 1000,
  "line_count": 50
}
```

## 🚀 Stato Attuale

### ✅ Completato
- [x] Struttura base del progetto
- [x] Ambiente virtuale configurato
- [x] Dipendenze installate
- [x] Server MCP funzionante
- [x] Sistema di gestione documenti
- [x] Motore di ricerca semantica
- [x] Tutti i 4 tools MCP implementati
- [x] Sistema di cache embeddings
- [x] Chunking intelligente documenti
- [x] Gestione metadati completa

### 🎯 Prossimi Sviluppi
- [ ] Test con documenti reali
- [ ] Ottimizzazione performance chunking
- [ ] Interfaccia web opzionale
- [ ] Supporto formati aggiuntivi (PDF, DOCX)
- [ ] Sistema di versioning documenti
- [ ] Ricerca con filtri avanzati

## 📖 Utilizzo

1. **Avvio Server**:
   ```bash
   .\venv\Scripts\python server.py
   ```

2. **Caricamento Documenti**:
   - Copiare file .txt/.md nella directory `data/`
   - Il sistema rileva automaticamente i nuovi file

3. **Ricerca**:
   - Utilizzare il tool `search_documents` con query in linguaggio naturale
   - Il sistema restituisce risultati semanticamente rilevanti

## 🔧 Configurazione

### Modello Embeddings
- **Modello**: `paraphrase-multilingual-mpnet-base-v2`
- **Supporto**: Multilingue (italiano, inglese, francese, tedesco, ecc.)
- **Dimensioni**: 768 dimensioni
- **Performance**: Bilanciamento qualità/velocità

### Chunking
- **Dimensione chunk**: 500 caratteri
- **Overlap**: 50 caratteri
- **Strategia**: Divisione intelligente su punti, spazi, a capo

## 📊 Metriche e Performance

### Cache Embeddings
- Memorizzazione su disco (file .pkl)
- Caricamento lazy del modello
- Cache in memoria durante l'esecuzione

### Ricerca
- Calcolo similarità coseno
- Ranking per rilevanza
- Risultati con contesto e posizione
