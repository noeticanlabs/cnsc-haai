"""
Receipts Store.

Indexes CNSC JSONL receipts for query by gate_id, reason_code, and outcome.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional

from ..core.hashing import hash_string


@dataclass
class Receipt:
    """A CNSC receipt.

    Attributes:
        receipt_id: Unique receipt identifier
        gate_id: Gate that produced this receipt
        reason_code: Reason code from the gate
        outcome: Receipt outcome (pass/fail)
        content: Full receipt content
        metadata: Additional metadata
    """

    receipt_id: str
    gate_id: str
    reason_code: str
    outcome: str
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ReceiptsStore:
    """Indexes CNSC JSONL receipts.

    Attributes:
        receipts: List of all receipts
        index_by_gate: Dict of gate_id -> receipts
        index_by_reason: Dict of reason_code -> receipts
        index_by_outcome: Dict of outcome -> receipts
    """

    def __init__(self):
        self.receipts: List[Receipt] = []
        self.index_by_gate: Dict[str, List[int]] = {}
        self.index_by_reason: Dict[str, List[int]] = {}
        self.index_by_outcome: Dict[str, List[int]] = {}

    def load_file(self, path: str) -> int:
        """Load receipts from a JSONL file.

        Args:
            path: Path to JSONL file

        Returns:
            Number of receipts loaded
        """
        count = 0

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    receipt = self._parse_receipt(data, path)
                    if receipt:
                        self._add_receipt(receipt)
                        count += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Invalid JSON in {path}: {e}")

        return count

    def load_directory(self, dir_path: str) -> int:
        """Load all receipts from a directory.

        Args:
            dir_path: Path to receipts directory

        Returns:
            Total receipts loaded
        """
        total = 0

        for filename in os.listdir(dir_path):
            if filename.endswith(".jsonl"):
                filepath = os.path.join(dir_path, filename)
                total += self.load_file(filepath)

        return total

    def _parse_receipt(self, data: Dict[str, Any], source: str) -> Optional[Receipt]:
        """Parse a receipt from JSON data.

        Args:
            data: Receipt JSON data
            source: Source file path

        Returns:
            Parsed Receipt or None
        """
        # Extract common fields
        receipt_id = data.get("receipt_id", "") or data.get("id", "")
        if not receipt_id:
            receipt_id = hash_string(json.dumps(data, sort_keys=True))

        gate_id = data.get("gate_id", "") or data.get("gate_stack_id", "")
        reason_code = data.get("reason_code", "") or data.get("reason", "")
        outcome = data.get("outcome", "unknown")

        return Receipt(
            receipt_id=receipt_id,
            gate_id=gate_id,
            reason_code=reason_code,
            outcome=outcome,
            content=data,
            metadata={"source": source},
        )

    def _add_receipt(self, receipt: Receipt) -> None:
        """Add a receipt to the store and indexes.

        Args:
            receipt: The receipt to add
        """
        idx = len(self.receipts)
        self.receipts.append(receipt)

        # Index by gate_id
        if receipt.gate_id:
            if receipt.gate_id not in self.index_by_gate:
                self.index_by_gate[receipt.gate_id] = []
            self.index_by_gate[receipt.gate_id].append(idx)

        # Index by reason_code
        if receipt.reason_code:
            if receipt.reason_code not in self.index_by_reason:
                self.index_by_reason[receipt.reason_code] = []
            self.index_by_reason[receipt.reason_code].append(idx)

        # Index by outcome
        if receipt.outcome:
            if receipt.outcome not in self.index_by_outcome:
                self.index_by_outcome[receipt.outcome] = []
            self.index_by_outcome[receipt.outcome].append(idx)

    def get_by_gate_id(self, gate_id: str) -> List[Receipt]:
        """Get receipts by gate ID.

        Args:
            gate_id: The gate identifier

        Returns:
            List of matching receipts
        """
        indices = self.index_by_gate.get(gate_id, [])
        return [self.receipts[i] for i in indices if i < len(self.receipts)]

    def get_by_reason_code(self, reason_code: str) -> List[Receipt]:
        """Get receipts by reason code.

        Args:
            reason_code: The reason code

        Returns:
            List of matching receipts
        """
        indices = self.index_by_reason.get(reason_code, [])
        return [self.receipts[i] for i in indices if i < len(self.receipts)]

    def get_by_outcome(self, outcome: str) -> List[Receipt]:
        """Get receipts by outcome.

        Args:
            outcome: The outcome (pass/fail)

        Returns:
            List of matching receipts
        """
        indices = self.index_by_outcome.get(outcome, [])
        return [self.receipts[i] for i in indices if i < len(self.receipts)]

    def get_failing_receipts(self) -> List[Receipt]:
        """Get all failing receipts.

        Returns:
            List of failing receipts
        """
        return self.get_by_outcome("fail")

    def get_passing_receipts(self) -> List[Receipt]:
        """Get all passing receipts.

        Returns:
            List of passing receipts
        """
        return self.get_by_outcome("pass")

    def search(
        self,
        gate_id: Optional[str] = None,
        reason_code: Optional[str] = None,
        outcome: Optional[str] = None,
        limit: int = 100,
    ) -> List[Receipt]:
        """Search receipts with filters.

        Args:
            gate_id: Filter by gate ID
            reason_code: Filter by reason code
            outcome: Filter by outcome
            limit: Maximum results

        Returns:
            List of matching receipts
        """
        # Start with all indices
        indices = set(range(len(self.receipts)))

        # Apply filters
        if gate_id:
            gate_indices = set(self.index_by_gate.get(gate_id, []))
            indices = indices.intersection(gate_indices)

        if reason_code:
            reason_indices = set(self.index_by_reason.get(reason_code, []))
            indices = indices.intersection(reason_indices)

        if outcome:
            outcome_indices = set(self.index_by_outcome.get(outcome, []))
            indices = indices.intersection(outcome_indices)

        # Get receipts and limit
        results = [self.receipts[i] for i in sorted(indices) if i < len(self.receipts)]
        return results[:limit]

    def get_receipt_hashes(self) -> List[str]:
        """Get sorted list of all receipt content hashes.

        Returns:
            Sorted list of hashes
        """
        hashes = []
        for receipt in self.receipts:
            content_hash = hash_string(json.dumps(receipt.content, sort_keys=True))
            hashes.append(content_hash)
        return sorted(hashes)


def load_receipts(receipts_path: str) -> ReceiptsStore:
    """Load receipts from a path.

    Args:
        receipts_path: Path to receipts file or directory

    Returns:
        Loaded ReceiptsStore
    """
    store = ReceiptsStore()

    if os.path.isdir(receipts_path):
        store.load_directory(receipts_path)
    elif os.path.isfile(receipts_path):
        store.load_file(receipts_path)

    return store
