"""
File-based Corpus Store.

Provides chunked storage and retrieval from file-based corpus.
"""

import hashlib
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from ..core.hashing import hash_string


# Chunk configuration
CHUNK_SIZE = 1200  # Characters
CHUNK_OVERLAP = 200  # Characters


@dataclass
class Chunk:
    """A chunk from the corpus.
    
    Attributes:
        chunk_id: Unique chunk identifier
        content: The chunk content
        source_path: Source file path
        chunk_index: Index within source
        char_range: Character range (start, end)
    """
    chunk_id: str
    content: str
    source_path: str
    chunk_index: int
    char_range: Tuple[int, int]


@dataclass
class CorpusStore:
    """File-based corpus storage with chunking.
    
    Attributes:
        chunks: Dict of chunk_id -> Chunk
        index: Reverse index for search
    """
    
    chunks: Dict[str, Chunk] = None
    index: Dict[str, List[str]] = None
    
    def __init__(self):
        self.chunks = {}
        self.index = {}
    
    def add_file(self, path: str, content: str) -> List[Chunk]:
        """Add a file to the corpus with chunking.
        
        Args:
            path: File path
            content: File content
            
        Returns:
            List of created chunks
        """
        created_chunks = []
        
        # Split into chunks with overlap
        chunks = self._split_into_chunks(content, CHUNK_SIZE, CHUNK_OVERLAP)
        
        for idx, chunk_content in enumerate(chunks):
            # Compute chunk ID
            content_hash = hash_string(chunk_content)
            chunk_id = f"chunk:{os.path.basename(path)}:{idx}:{content_hash[:16]}"
            
            # Compute character range
            start = idx * (CHUNK_SIZE - CHUNK_OVERLAP)
            end = start + len(chunk_content)
            
            chunk = Chunk(
                chunk_id=chunk_id,
                content=chunk_content,
                source_path=path,
                chunk_index=idx,
                char_range=(start, end),
            )
            
            self.chunks[chunk_id] = chunk
            created_chunks.append(chunk)
            
            # Build index (tokenize and index)
            self._index_chunk(chunk)
        
        return created_chunks
    
    def add_directory(self, dir_path: str, extensions: Tuple[str] = (".md", ".txt")) -> int:
        """Add all files from a directory.
        
        Args:
            dir_path: Directory path
            extensions: File extensions to include
            
        Returns:
            Number of files processed
        """
        count = 0
        
        for root, _, files in os.walk(dir_path):
            for filename in files:
                if filename.endswith(extensions):
                    filepath = os.path.join(root, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.add_file(filepath, content)
                        count += 1
                    except (IOError, UnicodeDecodeError) as e:
                        print(f"Warning: Could not read {filepath}: {e}")
        
        return count
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Get a chunk by ID.
        
        Args:
            chunk_id: The chunk identifier
            
        Returns:
            Chunk or None if not found
        """
        return self.chunks.get(chunk_id)
    
    def search(self, query: str, limit: int = 10) -> List[Chunk]:
        """Search corpus by keyword.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching chunks
        """
        query_tokens = self._tokenize(query)
        results = []
        
        for token in query_tokens:
            if token in self.index:
                for chunk_id in self.index[token]:
                    if chunk_id in self.chunks:
                        results.append(self.chunks[chunk_id])
        
        # Deduplicate and limit
        seen = set()
        unique_results = []
        for chunk in results:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                unique_results.append(chunk)
                if len(unique_results) >= limit:
                    break
        
        return unique_results
    
    def get_all_chunks(self) -> List[Chunk]:
        """Get all chunks.
        
        Returns:
            List of all chunks
        """
        return list(self.chunks.values())
    
    def get_chunk_hashes(self) -> List[str]:
        """Get sorted list of all chunk content hashes.
        
        Returns:
            Sorted list of content hashes
        """
        hashes = []
        for chunk in self.chunks.values():
            content_hash = hash_string(chunk.content)
            hashes.append(content_hash)
        return sorted(hashes)
    
    def get_snapshot_hash(self) -> str:
        """Compute a snapshot hash of the entire corpus.
        
        This creates a deterministic hash based on all chunk content,
        providing a unique identifier for the current corpus state.
        
        Returns:
            SHA-256 hash of all chunk content hashes combined
        """
        chunk_hashes = self.get_chunk_hashes()
        if not chunk_hashes:
            return hashlib.sha256(b"empty_corpus").hexdigest()
        
        # Combine all hashes and compute final hash
        combined = "".join(chunk_hashes).encode('utf-8')
        return hashlib.sha256(combined).hexdigest()
    
    def _split_into_chunks(
        self,
        content: str,
        size: int,
        overlap: int,
    ) -> List[str]:
        """Split content into overlapping chunks.
        
        Args:
            content: Text to split
            size: Target chunk size
            overlap: Overlap between chunks
            
        Returns:
            List of chunks
        """
        if len(content) <= size:
            return [content] if content.strip() else []
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + size, len(content))
            chunk = content[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            if end >= len(content):
                break
            
            # Move start forward with overlap
            start = end - overlap
        
        return chunks
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of lowercase tokens
        """
        import re
        # Simple word tokenization
        tokens = re.findall(r'\b\w+\b', text.lower())
        # Filter short tokens
        return [t for t in tokens if len(t) >= 2]
    
    def _index_chunk(self, chunk: Chunk) -> None:
        """Index a chunk.
        
        Args:
            chunk: The chunk to index
        """
        tokens = self._tokenize(chunk.content)
        for token in tokens:
            if token not in self.index:
                self.index[token] = []
            if chunk.chunk_id not in self.index[token]:
                self.index[token].append(chunk.chunk_id)


def load_corpus(corpus_path: str) -> CorpusStore:
    """Load a corpus from a directory.
    
    Args:
        corpus_path: Path to corpus directory
        
    Returns:
        Loaded CorpusStore
    """
    store = CorpusStore()
    
    if os.path.isdir(corpus_path):
        store.add_directory(corpus_path)
    elif os.path.isfile(corpus_path):
        with open(corpus_path, "r", encoding="utf-8") as f:
            content = f.read()
        store.add_file(corpus_path, content)
    
    return store
