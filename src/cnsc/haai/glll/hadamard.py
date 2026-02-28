"""
GLLL Hadamard Codec

Error-tolerant binary encoding using Hadamard matrices.

This module provides:
- HadamardMatrix: Hadamard matrix operations
- HadamardCodec: Encode/decode with Hadamard
- ErrorDetector: Error detection via syndromes

Key Features:
- Sylvester construction for Hadamard matrices
- Fast Walsh-Hadamard Transform (FWT)
- Syndrome calculation for error detection
- Error correction (up to t errors)
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from math import log2, floor
import json


class HadamardOrder(Enum):
    """Hadamard matrix order."""

    H1 = 1  # 1x1: [1]
    H2 = 2  # 2x2
    H4 = 4  # 4x4
    H8 = 8  # 8x8
    H16 = 16  # 16x16
    H32 = 32  # 32x32
    H64 = 64  # 64x64
    H128 = 128  # 128x128


@dataclass
class HadamardMatrix:
    """
    Hadamard Matrix.

    A Hadamard matrix H is a square matrix whose entries are either +1 or -1
    such that H * H^T = n * I, where n is the order of the matrix.
    """

    order: int
    matrix: List[List[int]]
    version: str = "1.0"

    def __post_init__(self):
        """Validate matrix."""
        if len(self.matrix) != self.order:
            raise ValueError(
                f"Matrix order {self.order} doesn't match actual size {len(self.matrix)}"
            )

    @classmethod
    def create_sylvester(cls, order: int, version: str = "1.0") -> "HadamardMatrix":
        """
        Create Hadamard matrix using Sylvester construction.

        H_1 = [1]
        H_2n = [H_n  H_n]
               [H_n -H_n]

        Args:
            order: Matrix order (must be power of 2)
            version: Version identifier

        Returns:
            HadamardMatrix instance
        """
        if order < 1 or (order & (order - 1)) != 0:
            raise ValueError(f"Order must be power of 2, got {order}")

        # Base case: H_1
        matrix = [[1]]

        # Sylvester construction
        while len(matrix) < order:
            n = len(matrix)
            # Create new matrix of size 2n x 2n
            new_matrix = []
            for i in range(2 * n):
                row = []
                for j in range(2 * n):
                    if i < n and j < n:
                        # Top-left: H_n
                        row.append(matrix[i][j])
                    elif i < n and j >= n:
                        # Top-right: H_n
                        row.append(matrix[i][j - n])
                    elif i >= n and j < n:
                        # Bottom-left: H_n (positive, not negative!)
                        row.append(matrix[i - n][j])
                    else:
                        # Bottom-right: -H_n
                        row.append(-matrix[i - n][j - n])
                new_matrix.append(row)
            matrix = new_matrix

        return cls(order=order, matrix=matrix, version=version)

    @classmethod
    def create_by_order(
        cls, hadamard_order: HadamardOrder, version: str = "1.0"
    ) -> "HadamardMatrix":
        """Create Hadamard matrix by enum order."""
        return cls.create_sylvester(hadamard_order.value, version)

    def get_row(self, index: int) -> List[int]:
        """Get row by index."""
        return self.matrix[index]

    def get_column(self, index: int) -> List[int]:
        """Get column by index."""
        return [self.matrix[i][index] for i in range(self.order)]

    def dot_product(self, row_idx: int, vector: List[int]) -> int:
        """
        Compute dot product of row with vector.

        Used for Walsh-Hadamard Transform.
        """
        if len(vector) != self.order:
            raise ValueError(f"Vector length {len(vector)} doesn't match order {self.order}")

        row = self.matrix[row_idx]
        return sum(row[i] * vector[i] for i in range(self.order))

    def multiply(self, vector: List[int]) -> List[int]:
        """
        Multiply matrix by vector (Hadamard transform).

        Returns transformed vector.
        """
        return [self.dot_product(i, vector) for i in range(self.order)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "order": self.order,
            "matrix": self.matrix,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HadamardMatrix":
        """Create from dictionary."""
        return cls(
            order=data["order"],
            matrix=data["matrix"],
            version=data.get("version", "1.0"),
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "HadamardMatrix":
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class SyndromeResult:
    """Result of syndrome calculation."""

    syndrome: List[int]
    has_error: bool
    error_count: int
    corrected: bool = False
    corrected_value: Optional[List[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "syndrome": self.syndrome,
            "has_error": self.has_error,
            "error_count": self.error_count,
            "corrected": self.corrected,
            "corrected_value": self.corrected_value,
        }


@dataclass
class ErrorDetector:
    """
    Error detection and correction using Hadamard codes.

    Uses syndrome decoding for error detection and correction.
    """

    hadamard: HadamardMatrix

    def __post_init__(self):
        """Initialize error detector."""
        self.n = self.hadamard.order
        # Maximum correctable errors: t = (n - k) / 2 where k = log2(n)
        # For simplicity, we use: t = floor(n / 4)
        self.max_correctable = floor(self.n / 4)

    def encode(self, data: List[int]) -> List[int]:
        """
        Encode data using Hadamard code.

        Args:
            data: Binary data to encode (length must be log2(n))

        Returns:
            Encoded Hadamard codeword
        """
        k = int(log2(self.n))
        if len(data) != k:
            raise ValueError(f"Data length {len(data)} must equal log2(n)={k}")

        # Find row index from binary data
        row_idx = 0
        for i, bit in enumerate(data):
            if bit != 0:
                row_idx += 1 << (k - 1 - i)

        return self.hadamard.get_row(row_idx)

    def decode(self, codeword: List[int]) -> Tuple[List[int], bool]:
        """
        Decode Hadamard codeword with error correction.

        Args:
            codeword: Received codeword

        Returns:
            Tuple of (decoded_data, was_corrected)
        """
        if len(codeword) != self.n:
            raise ValueError(f"Codeword length {len(codeword)} must equal n={self.n}")

        # Compute syndrome using FWT
        transformed = self.hadamard.multiply(codeword)

        # Find the row with maximum absolute value
        max_val = max(abs(x) for x in transformed)
        max_idx = (
            transformed.index(max_val) if max_val in transformed else -transformed.index(-max_val)
        )

        # Decode to binary
        k = int(log2(self.n))
        decoded = []
        for i in range(k):
            bit = (max_idx >> (k - 1 - i)) & 1
            decoded.append(bit)

        # Check if errors were detected/corrected
        # In Hadamard coding, the maximum value should be n if no errors
        # Errors reduce the maximum value
        was_corrected = max_val < self.n

        return decoded, was_corrected

    def compute_syndrome(self, received: List[int]) -> SyndromeResult:
        """
        Compute syndrome for error detection.

        Args:
            received: Received codeword

        Returns:
            SyndromeResult with detection/correction info
        """
        if len(received) != self.n:
            raise ValueError(f"Received length {len(received)} must equal n={self.n}")

        # Transform
        transformed = self.hadamard.multiply(received)

        # Syndrome is the transformed vector divided by n
        syndrome = [x // self.n for x in transformed]

        # Count errors (non-zero syndrome entries)
        # With t errors, syndrome will have non-zero entries
        error_count = sum(1 for x in syndrome if x != 0)

        has_error = error_count > 0
        corrected = False
        corrected_value = None

        if has_error and error_count <= self.max_correctable:
            # Attempt correction
            corrected = True
            corrected_value = self._correct_errors(received, syndrome)

        return SyndromeResult(
            syndrome=syndrome,
            has_error=has_error,
            error_count=error_count,
            corrected=corrected,
            corrected_value=corrected_value,
        )

    def _correct_errors(self, received: List[int], syndrome: List[int]) -> List[int]:
        """
        Attempt to correct errors.

        Simple error correction for Hadamard codes.
        """
        # Find position of maximum syndrome value
        max_syn = max(abs(x) for x in syndrome)
        if max_syn == 0:
            return received.copy()

        error_pos = syndrome.index(max_syn) if max_syn in syndrome else -syndrome.index(-max_syn)

        # Flip the bit at error position
        corrected = received.copy()
        corrected[error_pos] = -corrected[error_pos]

        return corrected

    def calculate_distance(self, codeword1: List[int], codeword2: List[int]) -> int:
        """
        Calculate Hamming distance between two codewords.

        Args:
            codeword1: First codeword
            codeword2: Second codeword

        Returns:
            Hamming distance
        """
        if len(codeword1) != len(codeword2):
            raise ValueError("Codewords must have same length")

        return sum(1 for a, b in zip(codeword1, codeword2) if a != b)

    def get_stats(self) -> Dict[str, Any]:
        """Get error detector statistics."""
        return {
            "order": self.n,
            "max_correctable": self.max_correctable,
            "code_rate": int(log2(self.n)) / self.n,
        }


@dataclass
class HadamardCodec:
    """
    High-level Hadamard codec.

    Combines encoding, decoding, and error correction.
    """

    hadamard: HadamardMatrix
    detector: ErrorDetector

    def __init__(self, order: int = 32, version: str = "1.0"):
        """Initialize codec with specified order."""
        self.hadamard = HadamardMatrix.create_sylvester(order, version)
        self.detector = ErrorDetector(self.hadamard)

    @classmethod
    def create_by_order(
        cls, hadamard_order: HadamardOrder, version: str = "1.0"
    ) -> "HadamardCodec":
        """Create codec by enum order."""
        return cls(hadamard_order.value, version)

    def encode(self, data: List[int]) -> List[int]:
        """Encode binary data to Hadamard codeword."""
        return self.detector.encode(data)

    def decode(self, codeword: List[int]) -> Tuple[List[int], bool]:
        """Decode codeword with error correction."""
        return self.detector.decode(codeword)

    def encode_with_errors(self, data: List[int], error_count: int = 0) -> List[int]:
        """
        Encode with optional simulated errors.

        Args:
            data: Data to encode
            error_count: Number of bit errors to introduce

        Returns:
            Codeword (possibly corrupted)
        """
        codeword = self.encode(data)

        # Introduce errors
        for _ in range(error_count):
            pos = hash(str(codeword) + str(_)) % len(codeword)
            codeword[pos] = -codeword[pos]

        return codeword

    def roundtrip(self, data: List[int], error_count: int = 0) -> Tuple[List[int], bool]:
        """
        Encode then decode to test error correction.

        Args:
            data: Data to encode
            error_count: Number of errors to introduce

        Returns:
            Tuple of (decoded_data, was_corrected)
        """
        codeword = self.encode_with_errors(data, error_count)
        return self.decode(codeword)

    def get_stats(self) -> Dict[str, Any]:
        """Get codec statistics."""
        return {
            "order": self.hadamard.order,
            **self.detector.get_stats(),
        }


def create_hadamard_codec(order: int = 32, version: str = "1.0") -> HadamardCodec:
    """Create new Hadamard codec."""
    return HadamardCodec(order, version)


def create_error_detector(order: int = 32, version: str = "1.0") -> ErrorDetector:
    """Create new error detector."""
    hadamard = HadamardMatrix.create_sylvester(order, version)
    return ErrorDetector(hadamard)
