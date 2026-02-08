"""
Index Building and Snapshot Hashing.

Builds corpus index and computes snapshot hashes.
"""

import json
import os
from typing import Any, Dict, List, Optional

from ..core.hashing import hash_corpus_snapshot, hash_receipts_snapshot
from .corpus_store import CorpusStore, load_corpus
from .receipts_store import ReceiptsStore, load_receipts


class IndexBuilder:
    """Builds and manages the retrieval index."""
    
    def __init__(self):
        self.corpus_store: Optional[CorpusStore] = None
        self.receipts_store: Optional[ReceiptsStore] = None
        self._corpus_snapshot_hash: Optional[str] = None
        self._receipts_snapshot_hash: Optional[str] = None
    
    def build_corpus_index(
        self,
        corpus_path: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build corpus index from directory.
        
        Args:
            corpus_path: Path to corpus directory
            output_path: Optional path to save index
            
        Returns:
            Index data dict
        """
        self.corpus_store = load_corpus(corpus_path)
        
        # Get sorted chunk hashes
        chunk_hashes = self.corpus_store.get_chunk_hashes()
        
        # Compute snapshot hash
        self._corpus_snapshot_hash = hash_corpus_snapshot(chunk_hashes)
        
        # Build index data
        index_data = {
            "spec": "NPE-INDEX-1.0",
            "corpus_snapshot_hash": self._corpus_snapshot_hash,
            "chunk_count": len(self.corpus_store.chunks),
            "chunks": [],
        }
        
        # Add chunk metadata
        for chunk_id, chunk in sorted(self.corpus_store.chunks.items()):
            index_data["chunks"].append({
                "chunk_id": chunk_id,
                "source_path": chunk.source_path,
                "chunk_index": chunk.chunk_index,
                "char_range": list(chunk.char_range),
                "content_hash": chunk_id.split(":")[-1],
            })
        
        # Save if output path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        return index_data
    
    def build_receipts_index(
        self,
        receipts_path: str,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build receipts index from directory.
        
        Args:
            receipts_path: Path to receipts directory
            output_path: Optional path to save index
            
        Returns:
            Index data dict
        """
        self.receipts_store = load_receipts(receipts_path)
        
        # Get sorted receipt hashes
        receipt_hashes = self.receipts_store.get_receipt_hashes()
        
        # Compute snapshot hash
        self._receipts_snapshot_hash = hash_receipts_snapshot(receipt_hashes)
        
        # Build index data
        index_data = {
            "spec": "NPE-RECEIPTS-INDEX-1.0",
            "receipts_snapshot_hash": self._receipts_snapshot_hash,
            "receipt_count": len(self.receipts_store.receipts),
            "index": {
                "by_gate": self.receipts_store.index_by_gate,
                "by_reason": self.receipts_store.index_by_reason,
                "by_outcome": self.receipts_store.index_by_outcome,
            },
        }
        
        # Save if output path provided
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        return index_data
    
    def build_full_index(
        self,
        corpus_path: str,
        receipts_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build both corpus and receipts indexes.
        
        Args:
            corpus_path: Path to corpus directory
            receipts_path: Path to receipts directory
            output_dir: Optional output directory
            
        Returns:
            Combined index data
        """
        corpus_index = self.build_corpus_index(
            corpus_path,
            os.path.join(output_dir, "corpus_index.json") if output_dir else None,
        )
        
        receipts_index = self.build_receipts_index(
            receipts_path,
            os.path.join(output_dir, "receipts_index.json") if output_dir else None,
        )
        
        combined_index = {
            "spec": "NPE-COMBINED-INDEX-1.0",
            "corpus_snapshot_hash": self._corpus_snapshot_hash,
            "receipts_snapshot_hash": self._receipts_snapshot_hash,
            "corpus": corpus_index,
            "receipts": receipts_index,
        }
        
        # Save combined index
        if output_dir:
            with open(os.path.join(output_dir, "combined_index.json"), "w", encoding="utf-8") as f:
                json.dump(combined_index, f, indent=2, ensure_ascii=False)
        
        return combined_index
    
    @property
    def corpus_snapshot_hash(self) -> str:
        """Get corpus snapshot hash."""
        if self._corpus_snapshot_hash is None:
            if self.corpus_store:
                chunk_hashes = self.corpus_store.get_chunk_hashes()
                self._corpus_snapshot_hash = hash_corpus_snapshot(chunk_hashes)
            else:
                raise RuntimeError("Corpus index not built")
        return self._corpus_snapshot_hash
    
    @property
    def receipts_snapshot_hash(self) -> str:
        """Get receipts snapshot hash."""
        if self._receipts_snapshot_hash is None:
            if self.receipts_store:
                receipt_hashes = self.receipts_store.get_receipt_hashes()
                self._receipts_snapshot_hash = hash_receipts_snapshot(receipt_hashes)
            else:
                raise RuntimeError("Receipts index not built")
        return self._receipts_snapshot_hash


def build_index(
    corpus_path: str,
    receipts_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> IndexBuilder:
    """Build retrieval index from paths.
    
    Args:
        corpus_path: Path to corpus directory
        receipts_path: Optional path to receipts directory
        output_dir: Optional output directory
        
    Returns:
        IndexBuilder with built indexes
    """
    builder = IndexBuilder()
    
    if receipts_path:
        builder.build_full_index(corpus_path, receipts_path, output_dir)
    else:
        builder.build_corpus_index(corpus_path, output_dir)
    
    return builder


def save_index(index_data: Dict[str, Any], path: str) -> None:
    """Save index data to file.
    
    Args:
        index_data: Index data to save
        path: Output file path
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)


def load_index(path: str) -> Dict[str, Any]:
    """Load index data from file.
    
    Args:
        path: Path to index file
        
    Returns:
        Loaded index data
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
