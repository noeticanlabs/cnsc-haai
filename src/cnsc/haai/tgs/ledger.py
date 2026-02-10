"""
Governance Ledger

Append-only ledger for TGS receipts. Provides:
- Append: Add receipts to the ledger
- Get: Retrieve receipts by index or ID
- Verify: Check hash chain integrity
- Replay: Replay receipts for verification
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import os
import sqlite3


@dataclass
class GovernanceLedger:
    """
    Append-only ledger for TGS receipts.
    
    The ledger maintains:
    - Sequential receipt storage
    - Hash chain for integrity verification
    - Persistent storage (SQLite)
    
    Attributes:
        storage_path: Path to ledger storage
        _connection: SQLite connection
        _initialized: Whether ledger is initialized
    """
    storage_path: str = "tgs_ledger.db"
    _connection: Optional[sqlite3.Connection] = field(default=None, repr=False)
    _initialized: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        """Initialize ledger connection and schema."""
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize ledger database and schema."""
        if self._initialized:
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path) if os.path.dirname(self.storage_path) else ".", exist_ok=True)
        
        self._connection = sqlite3.connect(self.storage_path)
        self._connection.row_factory = sqlite3.Row
        
        # Create schema
        cursor = self._connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                seq_num INTEGER PRIMARY KEY,
                receipt_id TEXT NOT NULL UNIQUE,
                parent_hash TEXT NOT NULL,
                receipt_hash TEXT NOT NULL,
                receipt_data TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_receipt_id
            ON ledger(receipt_id)
        """)
        
        self._connection.commit()
        self._initialized = True
    
    def append(self, receipt: 'TGSReceipt') -> str:
        """
        Append receipt to ledger.
        
        Args:
            receipt: Receipt to append
            
        Returns:
            Receipt ID (hex string)
        """
        cursor = self._connection.cursor()
        
        # Get current seq_num
        cursor.execute("SELECT MAX(seq_num) as max_seq FROM ledger")
        result = cursor.fetchone()
        current_seq = result["max_seq"] + 1 if result["max_seq"] is not None else 0
        
        # Get parent hash
        parent_hash = ""
        if current_seq > 0:
            cursor.execute("SELECT receipt_hash FROM ledger WHERE seq_num = ?", (current_seq - 1,))
            parent_result = cursor.fetchone()
            parent_hash = parent_result["receipt_hash"] if parent_result else ""
        
        # Serialize receipt
        receipt_dict = receipt.to_dict()
        receipt_data = json.dumps(receipt_dict, sort_keys=True)
        
        # Compute receipt hash (includes parent hash for chain)
        hash_input = f"{parent_hash}:{receipt_data}"
        receipt_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Insert
        cursor.execute("""
            INSERT INTO ledger (seq_num, receipt_id, parent_hash, receipt_hash, receipt_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            current_seq,
            str(receipt.attempt_id),
            parent_hash,
            receipt_hash,
            receipt_data,
            receipt.timestamp.timestamp(),
        ))
        
        self._connection.commit()
        
        return str(receipt.attempt_id)
    
    def get(self, seq_num: int) -> Optional['TGSReceipt']:
        """
        Retrieve receipt by ledger seq_num.
        
        Args:
            seq_num: Ledger sequence number
            
        Returns:
            Receipt if found, None otherwise
        """
        cursor = self._connection.cursor()
        
        cursor.execute("SELECT receipt_data FROM ledger WHERE seq_num = ?", (seq_num,))
        result = cursor.fetchone()
        
        if result is None:
            return None
        
        from cnsc.haai.tgs.receipt import TGSReceipt
        return TGSReceipt.from_json(result["receipt_data"])
    
    def get_by_id(self, receipt_id: str) -> Optional['TGSReceipt']:
        """
        Retrieve receipt by receipt ID.
        
        Args:
            receipt_id: Receipt attempt_id
            
        Returns:
            Receipt if found, None otherwise
        """
        cursor = self._connection.cursor()
        
        cursor.execute("SELECT receipt_data FROM ledger WHERE receipt_id = ?", (receipt_id,))
        result = cursor.fetchone()
        
        if result is None:
            return None
        
        from cnsc.haai.tgs.receipt import TGSReceipt
        return TGSReceipt.from_json(result["receipt_data"])
    
    def get_latest(self) -> Optional['TGSReceipt']:
        """
        Get most recent receipt.
        
        Returns:
            Latest receipt if exists, None otherwise
        """
        cursor = self._connection.cursor()
        
        cursor.execute("SELECT MAX(seq_num) as max_seq FROM ledger")
        result = cursor.fetchone()
        
        if result["max_seq"] is None:
            return None
        
        return self.get(result["max_seq"])
    
    def get_length(self) -> int:
        """
        Get number of receipts in ledger.
        
        Returns:
            Ledger length
        """
        cursor = self._connection.cursor()
        
        cursor.execute("SELECT MAX(seq_num) as max_seq FROM ledger")
        result = cursor.fetchone()
        
        return result["max_seq"] + 1 if result["max_seq"] is not None else 0
    
    def verify_chain(self, from_seq: int = 0) -> bool:
        """
        Verify hash chain integrity from seq_num.
        
        Args:
            from_seq: Starting sequence number for verification
            
        Returns:
            True if chain is valid, False otherwise
        """
        cursor = self._connection.cursor()
        
        cursor.execute("SELECT seq_num FROM ledger ORDER BY seq_num")
        seq_nums = [row["seq_num"] for row in cursor.fetchall()]
        
        if not seq_nums or from_seq >= len(seq_nums):
            return True
        
        # Filter to seq_nums >= from_seq
        relevant_seqs = [i for i in seq_nums if i >= from_seq]
        
        for i in range(len(relevant_seqs)):
            current_seq = relevant_seqs[i]
            
            cursor.execute("SELECT receipt_hash, parent_hash, receipt_data FROM ledger WHERE seq_num = ?", (current_seq,))
            result = cursor.fetchone()
            
            if result is None:
                return False
            
            stored_parent_hash = result["parent_hash"]
            stored_receipt_hash = result["receipt_hash"]
            receipt_data = result["receipt_data"]
            
            # Verify parent hash
            if i == 0:
                # First receipt should have empty parent hash or match last before from_seq
                if from_seq > 0:
                    cursor.execute("SELECT receipt_hash FROM ledger WHERE seq_num = ?", (from_seq - 1,))
                    prev_result = cursor.fetchone()
                    if prev_result and stored_parent_hash != prev_result["receipt_hash"]:
                        return False
            else:
                # Verify parent chain
                prev_seq = relevant_seqs[i - 1]
                cursor.execute("SELECT receipt_hash FROM ledger WHERE seq_num = ?", (prev_seq,))
                prev_result = cursor.fetchone()
                if prev_result and stored_parent_hash != prev_result["receipt_hash"]:
                    return False
            
            # Verify receipt hash
            hash_input = f"{stored_parent_hash}:{receipt_data}"
            computed_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            if computed_hash != stored_receipt_hash:
                return False
        
        return True
    
    def get_hash_chain(self, from_seq: int = 0) -> List[Dict[str, Any]]:
        """
        Get hash chain for audit purposes.
        
        Args:
            from_seq: Starting sequence number
            
        Returns:
            List of chain entries with hashes
        """
        cursor = self._connection.cursor()
        
        cursor.execute("""
            SELECT seq_num, receipt_id, parent_hash, receipt_hash, timestamp
            FROM ledger
            WHERE seq_num >= ?
            ORDER BY seq_num
        """, (from_seq,))
        
        return [
            {
                "seq_num": row["seq_num"],
                "receipt_id": row["receipt_id"],
                "parent_hash": row["parent_hash"],
                "receipt_hash": row["receipt_hash"],
                "timestamp": row["timestamp"],
            }
            for row in cursor.fetchall()
        ]
    
    def close(self) -> None:
        """Close ledger connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._initialized = False
    
    def __enter__(self) -> 'GovernanceLedger':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


# Import TGSReceipt for type hints
from cnsc.haai.tgs.receipt import TGSReceipt
