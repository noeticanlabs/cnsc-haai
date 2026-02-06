"""
GLLL Packetization

Data packetization for transmission.

This module provides:
- Packet: Transmission packet
- Packetizer: Data segmentation
- Depacketizer: Data reassembly

Key Features:
- Fixed-size packet creation
- Sequence numbering
- Checksum validation
- Reassembly
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import json
import hashlib


class PacketType(Enum):
    """Type of packet."""
    DATA = auto()
    CONTROL = auto()
    ACK = auto()
    NACK = auto()
    SYNC = auto()


class PacketStatus(Enum):
    """Packet transmission status."""
    PENDING = auto()
    SENT = auto()
    RECEIVED = auto()
    ACKNOWLEDGED = auto()
    FAILED = auto()


@dataclass
class Packet:
    """
    Transmission packet.
    
    Contains payload, metadata, and integrity information.
    """
    packet_id: str
    packet_type: PacketType
    sequence_number: int
    total_packets: int
    payload: bytes
    checksum: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: PacketStatus = PacketStatus.PENDING
    
    def __post_init__(self):
        """Validate packet."""
        if self.sequence_number < 0:
            raise ValueError("Sequence number cannot be negative")
        if self.sequence_number >= self.total_packets:
            raise ValueError("Sequence number must be less than total packets")
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Compute packet checksum."""
        data = {
            "packet_id": self.packet_id,
            "packet_type": self.packet_type.name,
            "sequence_number": self.sequence_number,
            "total_packets": self.total_packets,
            "payload": self.payload.decode('latin-1') if self.payload else "",
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]
    
    def verify_checksum(self) -> bool:
        """Verify packet checksum."""
        return self.checksum == self._compute_checksum()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "packet_id": self.packet_id,
            "packet_type": self.packet_type.name,
            "sequence_number": self.sequence_number,
            "total_packets": self.total_packets,
            "payload": self.payload.decode('latin-1') if self.payload else "",
            "checksum": self.checksum,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "status": self.status.name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Packet':
        """Create from dictionary."""
        return cls(
            packet_id=data["packet_id"],
            packet_type=PacketType[data["packet_type"]],
            sequence_number=data["sequence_number"],
            total_packets=data["total_packets"],
            payload=data.get("payload", "").encode('latin-1'),
            checksum=data["checksum"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            status=PacketStatus[data.get("status", "PENDING")],
        )
    
    def to_bytes(self) -> bytes:
        """Convert to bytes for transmission."""
        return json.dumps(self.to_dict()).encode('utf-8')
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Packet':
        """Create from bytes."""
        return cls.from_dict(json.loads(data.decode('utf-8')))


@dataclass
class Packetizer:
    """
    Data packetization.
    
    Segments data into fixed-size packets for transmission.
    """
    packet_size: int
    max_payload_size: int
    stream_id: str
    
    def __init__(
        self,
        packet_size: int = 512,
        max_payload_ratio: float = 0.9,
        stream_id: Optional[str] = None,
    ):
        """
        Initialize packetizer.
        
        Args:
            packet_size: Maximum packet size in bytes
            max_payload_ratio: Ratio of packet size for payload
            stream_id: Optional stream identifier
        """
        self.packet_size = packet_size
        self.max_payload_size = int(packet_size * max_payload_ratio)
        self.stream_id = stream_id or str(uuid4())[:8]
    
    def packetize(self, data: bytes, packet_type: PacketType = PacketType.DATA) -> List[Packet]:
        """
        Segment data into packets.
        
        Args:
            data: Data to packetize
            packet_type: Type of packets to create
            
        Returns:
            List of packets
        """
        packets = []
        total_packets = (len(data) + self.max_payload_size - 1) // self.max_payload_size
        
        for i in range(total_packets):
            start = i * self.max_payload_size
            end = min(start + self.max_payload_size, len(data))
            payload = data[start:end]
            
            packet = Packet(
                packet_id=str(uuid4())[:12],
                packet_type=packet_type,
                sequence_number=i,
                total_packets=total_packets,
                payload=payload,
                checksum="",  # Will be computed
                timestamp=datetime.utcnow(),
                metadata={"stream_id": self.stream_id},
            )
            packets.append(packet)
        
        return packets
    
    def depacketize(self, packets: List[Packet]) -> Tuple[bytes, bool]:
        """
        Reassemble packets into data.
        
        Args:
            packets: List of packets to reassemble
            
        Returns:
            Tuple of (reassembled data, is_valid)
        """
        if not packets:
            return b"", True
        
        # Sort by sequence number
        sorted_packets = sorted(packets, key=lambda p: p.sequence_number)
        
        # Verify all packets present
        expected_count = sorted_packets[0].total_packets
        if len(sorted_packets) != expected_count:
            return b"", False
        
        # Verify checksums
        for packet in sorted_packets:
            if not packet.verify_checksum():
                return b"", False
        
        # Reassemble payload
        data = b"".join(p.payload for p in sorted_packets)
        
        return data, True
    
    def get_packet_stats(self, packets: List[Packet]) -> Dict[str, Any]:
        """Get statistics for packets."""
        if not packets:
            return {}
        
        return {
            "total_packets": len(packets),
            "packet_size": self.packet_size,
            "total_data_size": sum(len(p.payload) for p in packets),
            "stream_id": self.stream_id,
        }


@dataclass
class Depacketizer:
    """
    Data reassembly.
    
    Reassembles packets back into original data.
    """
    received_packets: Dict[int, Packet]
    expected_count: int
    stream_id: str
    
    def __init__(self, stream_id: Optional[str] = None):
        """Initialize depacketizer."""
        self.received_packets = {}
        self.expected_count = 0
        self.stream_id = stream_id or str(uuid4())[:8]
    
    def add_packet(self, packet: Packet) -> bool:
        """
        Add packet to reassembly buffer.
        
        Args:
            packet: Packet to add
            
        Returns:
            True if packet accepted
        """
        # Verify stream ID
        if packet.metadata.get("stream_id") != self.stream_id:
            # Try to switch stream
            if not self.received_packets:
                self.stream_id = packet.metadata.get("stream_id", self.stream_id)
            else:
                return False
        
        # Update expected count
        if self.expected_count == 0:
            self.expected_count = packet.total_packets
        elif packet.total_packets != self.expected_count:
            return False
        
        # Check bounds
        if packet.sequence_number >= packet.total_packets:
            return False
        
        # Verify checksum
        if not packet.verify_checksum():
            return False
        
        self.received_packets[packet.sequence_number] = packet
        return True
    
    def is_complete(self) -> bool:
        """Check if all packets received."""
        return len(self.received_packets) == self.expected_count
    
    def get_missing(self) -> List[int]:
        """Get list of missing sequence numbers."""
        return [i for i in range(self.expected_count) if i not in self.received_packets]
    
    def reassemble(self) -> Tuple[bytes, bool]:
        """
        Reassemble packets.
        
        Returns:
            Tuple of (reassembled data, is_valid)
        """
        if not self.is_complete():
            return b"", False
        
        sorted_packets = [self.received_packets[i] for i in range(self.expected_count)]
        data = b"".join(p.payload for p in sorted_packets)
        
        return data, True
    
    def clear(self) -> None:
        """Clear received packets."""
        self.received_packets.clear()
        self.expected_count = 0


@dataclass
class SequenceTracker:
    """Track packet sequence for reliability."""
    
    expected_sequence: int
    received_sequences: set
    max_sequence: int
    
    def __init__(self):
        """Initialize tracker."""
        self.expected_sequence = 0
        self.received_sequences = set()
        self.max_sequence = 0
    
    def add(self, sequence_number: int) -> bool:
        """
        Add received sequence number.
        
        Returns:
            True if sequence is expected or already received
        """
        self.received_sequences.add(sequence_number)
        self.max_sequence = max(self.max_sequence, sequence_number)
        return True
    
    def get_missing(self) -> List[int]:
        """Get missing sequence numbers."""
        return [i for i in range(self.expected_sequence, self.max_sequence + 1) 
                if i not in self.received_sequences]
    
    def reset(self) -> None:
        """Reset tracker."""
        self.expected_sequence = 0
        self.received_sequences.clear()
        self.max_sequence = 0


def create_packetizer(
    packet_size: int = 512,
    max_payload_ratio: float = 0.9,
    stream_id: Optional[str] = None,
) -> Packetizer:
    """Create new packetizer."""
    return Packetizer(packet_size, max_payload_ratio, stream_id)


def create_depacketizer(stream_id: Optional[str] = None) -> Depacketizer:
    """Create new depacketizer."""
    return Depacketizer(stream_id)


def create_sequence_tracker() -> SequenceTracker:
    """Create new sequence tracker."""
    return SequenceTracker()
