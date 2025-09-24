# backend/autopilot/knowledge.py
"""
Autopilot Knowledge - Continuous Knowledge Base Ingest
Sammelt und verarbeitet Wissen kontinuierlich
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from sqlmodel import Session, select
from .metrics import get_metrics_writer

# ------------------------------------------------------------
# Datenmodelle
# ------------------------------------------------------------

@dataclass
class KnowledgeSource:
    """Wissensquelle"""
    id: str
    type: str  # "file", "web", "api", "manual"
    path: str
    last_modified: datetime
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class KnowledgeChunk:
    """Wissens-Chunk"""
    id: str
    source_id: str
    content: str
    chunk_type: str  # "text", "code", "markdown", "summary"
    tags: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()

@dataclass
class KnowledgeSummary:
    """Wissens-Zusammenfassung"""
    id: str
    topic: str
    summary: str
    sources: List[str]
    confidence: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

# ------------------------------------------------------------
# Knowledge Base Manager
# ------------------------------------------------------------

class KnowledgeBaseManager:
    """Verwaltet die Wissensbasis"""
    
    def __init__(self, base_path: str = "data/autopilot/kb"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.sources_file = self.base_path / "sources.json"
        self.chunks_file = self.base_path / "chunks.json"
        self.summaries_file = self.base_path / "summaries.json"
        
        # Lade bestehende Daten
        self.sources = self._load_sources()
        self.chunks = self._load_chunks()
        self.summaries = self._load_summaries()
    
    def _load_sources(self) -> Dict[str, KnowledgeSource]:
        """Lädt Quellen aus Datei"""
        if not self.sources_file.exists():
            return {}
        
        try:
            with open(self.sources_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    k: KnowledgeSource(**v) for k, v in data.items()
                }
        except Exception:
            return {}
    
    def _load_chunks(self) -> Dict[str, KnowledgeChunk]:
        """Lädt Chunks aus Datei"""
        if not self.chunks_file.exists():
            return {}
        
        try:
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    k: KnowledgeChunk(**v) for k, v in data.items()
                }
        except Exception:
            return {}
    
    def _load_summaries(self) -> Dict[str, KnowledgeSummary]:
        """Lädt Zusammenfassungen aus Datei"""
        if not self.summaries_file.exists():
            return {}
        
        try:
            with open(self.summaries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    k: KnowledgeSummary(**v) for k, v in data.items()
                }
        except Exception:
            return {}
    
    def _save_sources(self):
        """Speichert Quellen"""
        data = {k: {
            "id": v.id,
            "type": v.type,
            "path": v.path,
            "last_modified": v.last_modified.isoformat(),
            "size_bytes": v.size_bytes,
            "checksum": v.checksum,
            "metadata": v.metadata
        } for k, v in self.sources.items()}
        
        with open(self.sources_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_chunks(self):
        """Speichert Chunks"""
        data = {k: {
            "id": v.id,
            "source_id": v.source_id,
            "content": v.content,
            "chunk_type": v.chunk_type,
            "tags": v.tags,
            "created_at": v.created_at.isoformat()
        } for k, v in self.chunks.items()}
        
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_summaries(self):
        """Speichert Zusammenfassungen"""
        data = {k: {
            "id": v.id,
            "topic": v.topic,
            "summary": v.summary,
            "sources": v.sources,
            "confidence": v.confidence,
            "created_at": v.created_at.isoformat()
        } for k, v in self.summaries.items()}
        
        with open(self.summaries_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_source(self, source: KnowledgeSource) -> bool:
        """Fügt neue Quelle hinzu"""
        self.sources[source.id] = source
        self._save_sources()
        return True
    
    def add_chunk(self, chunk: KnowledgeChunk) -> bool:
        """Fügt neuen Chunk hinzu"""
        self.chunks[chunk.id] = chunk
        self._save_chunks()
        return True
    
    def add_summary(self, summary: KnowledgeSummary) -> bool:
        """Fügt neue Zusammenfassung hinzu"""
        self.summaries[summary.id] = summary
        self._save_summaries()
        return True
    
    def get_sources_by_type(self, source_type: str) -> List[KnowledgeSource]:
        """Gibt Quellen nach Typ zurück"""
        return [s for s in self.sources.values() if s.type == source_type]
    
    def get_chunks_by_source(self, source_id: str) -> List[KnowledgeChunk]:
        """Gibt Chunks einer Quelle zurück"""
        return [c for c in self.chunks.values() if c.source_id == source_id]
    
    def search_chunks(self, query: str, limit: int = 10) -> List[KnowledgeChunk]:
        """Sucht Chunks nach Query"""
        query_lower = query.lower()
        matches = []
        
        for chunk in self.chunks.values():
            if query_lower in chunk.content.lower():
                matches.append(chunk)
        
        # Sortiere nach Relevanz (einfache Implementierung)
        matches.sort(key=lambda c: c.content.lower().count(query_lower), reverse=True)
        return matches[:limit]

# ------------------------------------------------------------
# File Ingestor
# ------------------------------------------------------------

class FileIngestor:
    """Verarbeitet Dateien für die Wissensbasis"""
    
    def __init__(self, kb_manager: KnowledgeBaseManager):
        self.kb_manager = kb_manager
    
    def ingest_directory(self, directory_path: str, file_types: List[str] = None) -> Dict[str, Any]:
        """Verarbeitet ein Verzeichnis"""
        
        if file_types is None:
            file_types = ['.md', '.txt', '.py', '.json', '.yaml', '.yml']
        
        directory = Path(directory_path)
        if not directory.exists():
            return {"error": f"Directory {directory_path} not found"}
        
        results = {
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "sources": [],
            "chunks": []
        }
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                try:
                    source_result = self._ingest_file(file_path)
                    if source_result:
                        results["processed"] += 1
                        results["sources"].append(source_result["source_id"])
                        results["chunks"].extend(source_result["chunk_ids"])
                    else:
                        results["skipped"] += 1
                except Exception as e:
                    results["errors"] += 1
                    print(f"Error processing {file_path}: {e}")
        
        return results
    
    def _ingest_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Verarbeitet eine einzelne Datei"""
        
        # Prüfe ob Datei bereits verarbeitet
        file_stat = file_path.stat()
        checksum = self._calculate_checksum(file_path)
        
        # Suche nach bestehender Quelle
        existing_source = None
        for source in self.kb_manager.sources.values():
            if source.path == str(file_path) and source.checksum == checksum:
                existing_source = source
                break
        
        if existing_source:
            return None  # Bereits verarbeitet
        
        # Erstelle neue Quelle
        source_id = f"file_{file_path.stem}_{int(datetime.utcnow().timestamp())}"
        source = KnowledgeSource(
            id=source_id,
            type="file",
            path=str(file_path),
            last_modified=datetime.fromtimestamp(file_stat.st_mtime),
            size_bytes=file_stat.st_size,
            checksum=checksum,
            metadata={
                "extension": file_path.suffix,
                "name": file_path.name
            }
        )
        
        self.kb_manager.add_source(source)
        
        # Verarbeite Inhalt
        chunks = self._chunk_file_content(file_path, source_id)
        chunk_ids = []
        
        for chunk in chunks:
            self.kb_manager.add_chunk(chunk)
            chunk_ids.append(chunk.id)
        
        return {
            "source_id": source_id,
            "chunk_ids": chunk_ids
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Berechnet Checksum einer Datei"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _chunk_file_content(self, file_path: Path, source_id: str) -> List[KnowledgeChunk]:
        """Chunkt Dateiinhalt"""
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Versuche andere Encodings
            try:
                content = file_path.read_text(encoding='latin-1')
            except:
                return []  # Überspringe Datei
        
        chunks = []
        
        if file_path.suffix.lower() == '.md':
            # Markdown-spezifisches Chunking
            chunks = self._chunk_markdown(content, source_id)
        elif file_path.suffix.lower() in ['.py', '.js', '.ts']:
            # Code-spezifisches Chunking
            chunks = self._chunk_code(content, source_id)
        else:
            # Allgemeines Text-Chunking
            chunks = self._chunk_text(content, source_id)
        
        return chunks
    
    def _chunk_markdown(self, content: str, source_id: str) -> List[KnowledgeChunk]:
        """Chunkt Markdown-Inhalt"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_title = ""
        
        for line in lines:
            if line.startswith('#'):
                # Neuer Abschnitt
                if current_chunk:
                    chunk_content = '\n'.join(current_chunk)
                    if chunk_content.strip():
                        chunk = KnowledgeChunk(
                            id=f"{source_id}_chunk_{len(chunks)}",
                            source_id=source_id,
                            content=chunk_content,
                            chunk_type="markdown",
                            tags=["markdown", current_title.lower().replace(' ', '_')]
                        )
                        chunks.append(chunk)
                
                current_chunk = [line]
                current_title = line.lstrip('#').strip()
            else:
                current_chunk.append(line)
        
        # Letzter Chunk
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunk = KnowledgeChunk(
                    id=f"{source_id}_chunk_{len(chunks)}",
                    source_id=source_id,
                    content=chunk_content,
                    chunk_type="markdown",
                    tags=["markdown", current_title.lower().replace(' ', '_')]
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_code(self, content: str, source_id: str) -> List[KnowledgeChunk]:
        """Chunkt Code-Inhalt"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        in_function = False
        function_name = ""
        
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('def ') or stripped.startswith('class '):
                # Neue Funktion/Klasse
                if current_chunk and in_function:
                    chunk_content = '\n'.join(current_chunk)
                    if chunk_content.strip():
                        chunk = KnowledgeChunk(
                            id=f"{source_id}_chunk_{len(chunks)}",
                            source_id=source_id,
                            content=chunk_content,
                            chunk_type="code",
                            tags=["code", function_name]
                        )
                        chunks.append(chunk)
                
                current_chunk = [line]
                in_function = True
                function_name = stripped.split('(')[0].split()[-1]
            else:
                current_chunk.append(line)
        
        # Letzter Chunk
        if current_chunk and in_function:
            chunk_content = '\n'.join(current_chunk)
            if chunk_content.strip():
                chunk = KnowledgeChunk(
                    id=f"{source_id}_chunk_{len(chunks)}",
                    source_id=source_id,
                    content=chunk_content,
                    chunk_type="code",
                    tags=["code", function_name]
                )
                chunks.append(chunk)
        
        return chunks
    
    def _chunk_text(self, content: str, source_id: str) -> List[KnowledgeChunk]:
        """Chunkt allgemeinen Text"""
        chunks = []
        paragraphs = content.split('\n\n')
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                chunk = KnowledgeChunk(
                    id=f"{source_id}_chunk_{i}",
                    source_id=source_id,
                    content=paragraph.strip(),
                    chunk_type="text",
                    tags=["text"]
                )
                chunks.append(chunk)
        
        return chunks

# ------------------------------------------------------------
# Knowledge Summarizer
# ------------------------------------------------------------

class KnowledgeSummarizer:
    """Erstellt Zusammenfassungen aus Wissens-Chunks"""
    
    def __init__(self, kb_manager: KnowledgeBaseManager):
        self.kb_manager = kb_manager
    
    def create_topic_summaries(self, topics: List[str] = None) -> List[KnowledgeSummary]:
        """Erstellt Zusammenfassungen für Themen"""
        
        if topics is None:
            topics = self._extract_topics()
        
        summaries = []
        
        for topic in topics:
            # Finde relevante Chunks
            relevant_chunks = self._find_chunks_for_topic(topic)
            
            if not relevant_chunks:
                continue
            
            # Erstelle Zusammenfassung
            summary = self._summarize_chunks(topic, relevant_chunks)
            if summary:
                summaries.append(summary)
                self.kb_manager.add_summary(summary)
        
        return summaries
    
    def _extract_topics(self) -> List[str]:
        """Extrahiert Themen aus Chunks"""
        # Einfache Implementierung - in Realität würde man NLP verwenden
        topics = set()
        
        for chunk in self.kb_manager.chunks.values():
            if chunk.chunk_type == "markdown":
                # Extrahiere Themen aus Markdown-Headern
                lines = chunk.content.split('\n')
                for line in lines:
                    if line.startswith('#'):
                        topic = line.lstrip('#').strip().lower()
                        if len(topic) > 3:
                            topics.add(topic)
        
        return list(topics)
    
    def _find_chunks_for_topic(self, topic: str) -> List[KnowledgeChunk]:
        """Findet Chunks für ein Thema"""
        relevant_chunks = []
        topic_lower = topic.lower()
        
        for chunk in self.kb_manager.chunks.values():
            if (topic_lower in chunk.content.lower() or 
                any(topic_lower in tag for tag in chunk.tags)):
                relevant_chunks.append(chunk)
        
        return relevant_chunks
    
    def _summarize_chunks(self, topic: str, chunks: List[KnowledgeChunk]) -> Optional[KnowledgeSummary]:
        """Erstellt Zusammenfassung aus Chunks"""
        
        if not chunks:
            return None
        
        # Einfache Zusammenfassung (in Realität würde man LLM verwenden)
        content_pieces = []
        sources = []
        
        for chunk in chunks[:5]:  # Maximal 5 Chunks
            content_pieces.append(chunk.content[:200])  # Erste 200 Zeichen
            sources.append(chunk.source_id)
        
        summary_text = f"Zusammenfassung zu '{topic}':\n\n" + "\n\n".join(content_pieces)
        
        summary = KnowledgeSummary(
            id=f"summary_{topic}_{int(datetime.utcnow().timestamp())}",
            topic=topic,
            summary=summary_text,
            sources=list(set(sources)),
            confidence=0.7  # Mittlere Konfidenz
        )
        
        return summary

# ------------------------------------------------------------
# Continuous Ingest Manager
# ------------------------------------------------------------

class ContinuousIngestManager:
    """Verwaltet kontinuierliche Wissensaufnahme"""
    
    def __init__(self):
        self.kb_manager = KnowledgeBaseManager()
        self.file_ingestor = FileIngestor(self.kb_manager)
        self.summarizer = KnowledgeSummarizer(self.kb_manager)
    
    def run_daily_ingest(self, 
                        docs_path: str = "docs",
                        results_path: str = "data/results") -> Dict[str, Any]:
        """Führt tägliche Wissensaufnahme durch"""
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "docs_processed": {},
            "results_processed": {},
            "summaries_created": 0,
            "errors": []
        }
        
        try:
            # Verarbeite Docs-Verzeichnis
            if os.path.exists(docs_path):
                docs_result = self.file_ingestor.ingest_directory(docs_path)
                results["docs_processed"] = docs_result
            
            # Verarbeite Results-Verzeichnis
            if os.path.exists(results_path):
                results_result = self.file_ingestor.ingest_directory(results_path)
                results["results_processed"] = results_result
            
            # Erstelle Zusammenfassungen
            summaries = self.summarizer.create_topic_summaries()
            results["summaries_created"] = len(summaries)
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def get_knowledge_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken der Wissensbasis zurück"""
        
        return {
            "total_sources": len(self.kb_manager.sources),
            "total_chunks": len(self.kb_manager.chunks),
            "total_summaries": len(self.kb_manager.summaries),
            "sources_by_type": {
                source_type: len(self.kb_manager.get_sources_by_type(source_type))
                for source_type in set(s.type for s in self.kb_manager.sources.values())
            },
            "chunks_by_type": {
                chunk_type: len([c for c in self.kb_manager.chunks.values() if c.chunk_type == chunk_type])
                for chunk_type in set(c.chunk_type for c in self.kb_manager.chunks.values())
            }
        }

# ------------------------------------------------------------
# Globale Instanzen
# ------------------------------------------------------------

_kb_manager: Optional[KnowledgeBaseManager] = None
_ingest_manager: Optional[ContinuousIngestManager] = None

def get_kb_manager() -> KnowledgeBaseManager:
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager

def get_ingest_manager() -> ContinuousIngestManager:
    global _ingest_manager
    if _ingest_manager is None:
        _ingest_manager = ContinuousIngestManager()
    return _ingest_manager
