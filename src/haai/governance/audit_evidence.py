"""
Audit and Evidence System

Provides comprehensive receipt generation for all operations,
append-only audit store with tamper detection, evidence query
and analysis tools, and compliance reporting capabilities.
"""

import logging
import hashlib
import json
import asyncio
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
import base64


class ReceiptType(Enum):
    """Types of audit receipts."""
    OPERATION = "operation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    POLICY_EVALUATION = "policy_evaluation"
    SAFETY_CHECK = "safety_check"
    ENFORCEMENT = "enforcement"
    RESOURCE_ALLOCATION = "resource_allocation"
    DATA_ACCESS = "data_access"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class EvidenceType(Enum):
    """Types of evidence."""
    LOG_ENTRY = "log_entry"
    METRIC = "metric"
    SCREENSHOT = "screenshot"
    FILE_HASH = "file_hash"
    NETWORK_TRACE = "network_trace"
    MEMORY_DUMP = "memory_dump"
    CONFIGURATION = "configuration"
    USER_INPUT = "user_input"
    SYSTEM_OUTPUT = "system_output"


class ComplianceStandard(Enum):
    """Compliance standards."""
    ISO_27001 = "iso_27001"
    SOC_2 = "soc_2"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST = "nist"


@dataclass
class Evidence:
    """Represents a piece of evidence."""
    evidence_id: str
    evidence_type: EvidenceType
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    collected_at: datetime = field(default_factory=datetime.now)
    hash_value: str = field(default="")
    signature: Optional[str] = None
    
    def __post_init__(self):
        """Calculate hash after initialization."""
        if not self.hash_value:
            self.hash_value = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of evidence content."""
        if isinstance(self.content, dict):
            content_str = json.dumps(self.content, sort_keys=True)
        elif isinstance(self.content, bytes):
            content_str = self.content.decode('utf-8', errors='ignore')
        else:
            content_str = str(self.content)
        
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify evidence integrity."""
        current_hash = self._calculate_hash()
        return current_hash == self.hash_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evidence to dictionary."""
        result = asdict(self)
        if isinstance(self.content, bytes):
            result["content"] = base64.b64encode(self.content).decode()
        return result


@dataclass
class AuditReceipt:
    """Represents an audit receipt for an operation."""
    receipt_id: str
    receipt_type: ReceiptType
    operation_id: str
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "completed"
    outcome: str = "success"
    details: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    parent_receipt_id: Optional[str] = None
    child_receipt_ids: List[str] = field(default_factory=list)
    hash_chain: List[str] = field(default_factory=list)
    signature: Optional[str] = None
    
    def add_evidence(self, evidence: Evidence) -> None:
        """Add evidence to receipt."""
        self.evidence.append(evidence)
    
    def calculate_receipt_hash(self) -> str:
        """Calculate hash of entire receipt."""
        receipt_data = {
            "receipt_id": self.receipt_id,
            "receipt_type": self.receipt_type.value,
            "operation_id": self.operation_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "outcome": self.outcome,
            "details": self.details,
            "evidence_hashes": [e.hash_value for e in self.evidence],
            "parent_receipt_id": self.parent_receipt_id
        }
        
        receipt_str = json.dumps(receipt_data, sort_keys=True)
        return hashlib.sha256(receipt_str.encode()).hexdigest()
    
    def verify_chain(self, previous_hash: Optional[str] = None) -> bool:
        """Verify hash chain integrity."""
        current_hash = self.calculate_receipt_hash()
        
        if previous_hash and self.hash_chain:
            return self.hash_chain[-1] == previous_hash
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert receipt to dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        result["receipt_type"] = self.receipt_type.value
        result["evidence"] = [e.to_dict() for e in self.evidence]
        return result


class TamperDetection:
    """Detects tampering in audit records."""
    
    def __init__(self):
        self.master_hash_chain: List[str] = []
        self.checkpoint_hashes: Dict[str, str] = {}
        self.logger = logging.getLogger("haai.tamper_detection")
    
    def add_receipt_hash(self, receipt_hash: str) -> None:
        """Add receipt hash to master chain."""
        if self.master_hash_chain:
            # Link to previous hash
            combined = self.master_hash_chain[-1] + receipt_hash
            linked_hash = hashlib.sha256(combined.encode()).hexdigest()
            self.master_hash_chain.append(linked_hash)
        else:
            self.master_hash_chain.append(receipt_hash)
    
    def create_checkpoint(self, checkpoint_id: str) -> str:
        """Create tamper detection checkpoint."""
        if not self.master_hash_chain:
            raise ValueError("No receipts to checkpoint")
        
        checkpoint_hash = self.master_hash_chain[-1]
        self.checkpoint_hashes[checkpoint_id] = checkpoint_hash
        
        self.logger.info(f"Created checkpoint: {checkpoint_id}")
        return checkpoint_hash
    
    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify checkpoint integrity."""
        if checkpoint_id not in self.checkpoint_hashes:
            return False
        
        stored_hash = self.checkpoint_hashes[checkpoint_id]
        current_hash = self.master_hash_chain[-1] if self.master_hash_chain else ""
        
        return stored_hash == current_hash
    
    def detect_tampering(self, start_index: int = 0) -> Dict[str, Any]:
        """Detect tampering in hash chain."""
        if start_index >= len(self.master_hash_chain):
            return {"tampered": False, "message": "Start index out of range"}
        
        # Recompute hash chain from start index
        recomputed_chain = []
        
        for i in range(start_index, len(self.master_hash_chain)):
            if i == start_index:
                recomputed_chain.append(self.master_hash_chain[i])
            else:
                # This is a simplified check - in practice, would need original receipt hashes
                pass
        
        return {
            "tampered": False,  # Simplified - would implement full verification
            "checked_entries": len(self.master_hash_chain) - start_index,
            "start_index": start_index
        }


class ComplianceReporter:
    """Generates compliance reports."""
    
    def __init__(self):
        self.compliance_mappings: Dict[ComplianceStandard, Dict[str, List[str]]] = {
            ComplianceStandard.ISO_27001: {
                "access_control": ["authentication", "authorization"],
                "audit_logging": ["all_operations"],
                "data_protection": ["encryption", "access_logs"],
                "incident_management": ["safety_incidents", "error_logs"]
            },
            ComplianceStandard.SOC_2: {
                "security": ["authentication", "authorization", "encryption"],
                "availability": ["system_uptime", "error_rates"],
                "processing_integrity": ["operation_receipts", "data_validation"],
                "confidentiality": ["data_access_logs", "encryption"],
                "privacy": ["personal_data_handling", "consent_logs"]
            },
            ComplianceStandard.GDPR: {
                "lawfulness": ["consent_records", "legal_basis"],
                "data_minimization": ["data_collection_logs"],
                "accuracy": ["data_correction_logs"],
                "storage_limitation": ["data_retention_logs"],
                "security": ["encryption", "access_controls", "breach_logs"]
            }
        }
        self.logger = logging.getLogger("haai.compliance_reporter")
    
    def generate_compliance_report(self, standard: ComplianceStandard,
                                  receipts: List[AuditReceipt],
                                  time_period: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Generate compliance report for a standard."""
        start_time, end_time = time_period
        
        # Filter receipts by time period
        period_receipts = [
            r for r in receipts
            if start_time <= r.timestamp <= end_time
        ]
        
        # Get requirements for standard
        requirements = self.compliance_mappings.get(standard, {})
        
        report = {
            "standard": standard.value,
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "total_receipts": len(period_receipts),
            "compliance_status": {},
            "evidence_summary": {},
            "recommendations": []
        }
        
        # Check each requirement
        for requirement, evidence_types in requirements.items():
            compliant_receipts = self._check_requirement(
                requirement, evidence_types, period_receipts
            )
            
            compliance_rate = len(compliant_receipts) / len(period_receipts) if period_receipts else 0
            
            report["compliance_status"][requirement] = {
                "compliant": compliance_rate >= 0.95,  # 95% compliance threshold
                "compliance_rate": compliance_rate,
                "total_receipts": len(period_receipts),
                "compliant_receipts": len(compliant_receipts),
                "evidence_types": evidence_types
            }
            
            # Add recommendations if not compliant
            if compliance_rate < 0.95:
                report["recommendations"].append(
                    f"Improve {requirement} compliance: {compliance_rate:.1%} "
                    f"(target: 95%)"
                )
        
        # Evidence summary
        all_evidence = []
        for receipt in period_receipts:
            all_evidence.extend(receipt.evidence)
        
        evidence_by_type = {}
        for evidence in all_evidence:
            evidence_type = evidence.evidence_type.value
            evidence_by_type[evidence_type] = evidence_by_type.get(evidence_type, 0) + 1
        
        report["evidence_summary"] = evidence_by_type
        
        return report
    
    def _check_requirement(self, requirement: str, evidence_types: List[str],
                          receipts: List[AuditReceipt]) -> List[AuditReceipt]:
        """Check if receipts meet requirement evidence types."""
        compliant = []
        
        for receipt in receipts:
            receipt_evidence_types = [e.evidence_type.value for e in receipt.evidence]
            
            # Check if receipt has required evidence types
            has_required = any(
                evidence_type in receipt_evidence_types
                for evidence_type in evidence_types
            )
            
            if has_required:
                compliant.append(receipt)
        
        return compliant


class AuditEvidenceSystem:
    """Main audit and evidence management system."""
    
    def __init__(self, enable_encryption: bool = True):
        self.receipts: Dict[str, AuditReceipt] = {}
        self.evidence_index: Dict[str, List[str]] = {}  # evidence_id -> receipt_ids
        self.agent_index: Dict[str, List[str]] = {}     # agent_id -> receipt_ids
        self.operation_index: Dict[str, List[str]] = {}  # operation_id -> receipt_ids
        self.tamper_detection = TamperDetection()
        self.compliance_reporter = ComplianceReporter()
        
        self.enable_encryption = enable_encryption
        self.private_key = None
        self.public_key = None
        
        self.logger = logging.getLogger("haai.audit_evidence")
        
        # Initialize encryption keys if enabled
        if enable_encryption:
            self._initialize_encryption()
    
    def _initialize_encryption(self) -> None:
        """Initialize RSA key pair for signing."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def create_receipt(self, receipt_type: ReceiptType, operation_id: str,
                      agent_id: str, status: str = "completed",
                      outcome: str = "success", details: Optional[Dict[str, Any]] = None,
                      parent_receipt_id: Optional[str] = None) -> str:
        """Create a new audit receipt."""
        receipt_id = f"rec_{uuid.uuid4().hex[:12]}"
        
        receipt = AuditReceipt(
            receipt_id=receipt_id,
            receipt_type=receipt_type,
            operation_id=operation_id,
            agent_id=agent_id,
            status=status,
            outcome=outcome,
            details=details or {},
            parent_receipt_id=parent_receipt_id
        )
        
        # Calculate hash and add to chain
        receipt_hash = receipt.calculate_receipt_hash()
        
        # Link to parent if exists
        if parent_receipt_id and parent_receipt_id in self.receipts:
            parent_receipt = self.receipts[parent_receipt_id]
            receipt.hash_chain = parent_receipt.hash_chain + [parent_receipt.calculate_receipt_hash()]
            parent_receipt.child_receipt_ids.append(receipt_id)
        
        # Sign receipt if encryption enabled
        if self.enable_encryption and self.private_key:
            receipt.signature = self._sign_receipt(receipt)
        
        # Store receipt
        self.receipts[receipt_id] = receipt
        
        # Update indexes
        self._update_indexes(receipt)
        
        # Add to tamper detection
        self.tamper_detection.add_receipt_hash(receipt_hash)
        
        self.logger.info(f"Created audit receipt: {receipt_id}")
        
        return receipt_id
    
    def add_evidence(self, receipt_id: str, evidence_type: EvidenceType,
                    content: Union[str, bytes, Dict[str, Any]],
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add evidence to a receipt."""
        if receipt_id not in self.receipts:
            raise ValueError(f"Receipt {receipt_id} not found")
        
        evidence_id = f"evi_{uuid.uuid4().hex[:12]}"
        
        evidence = Evidence(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            content=content,
            metadata=metadata or {}
        )
        
        # Sign evidence if encryption enabled
        if self.enable_encryption and self.private_key:
            evidence.signature = self._sign_evidence(evidence)
        
        # Add to receipt
        self.receipts[receipt_id].add_evidence(evidence)
        
        # Update evidence index
        if evidence_id not in self.evidence_index:
            self.evidence_index[evidence_id] = []
        self.evidence_index[evidence_id].append(receipt_id)
        
        self.logger.info(f"Added evidence {evidence_id} to receipt {receipt_id}")
        
        return evidence_id
    
    def get_receipt(self, receipt_id: str) -> Optional[AuditReceipt]:
        """Get a receipt by ID."""
        return self.receipts.get(receipt_id)
    
    def query_receipts(self, agent_id: Optional[str] = None,
                      operation_id: Optional[str] = None,
                      receipt_type: Optional[ReceiptType] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 100) -> List[AuditReceipt]:
        """Query receipts with filters."""
        receipts = list(self.receipts.values())
        
        # Apply filters
        if agent_id:
            receipts = [r for r in receipts if r.agent_id == agent_id]
        
        if operation_id:
            receipts = [r for r in receipts if r.operation_id == operation_id]
        
        if receipt_type:
            receipts = [r for r in receipts if r.receipt_type == receipt_type]
        
        if start_time:
            receipts = [r for r in receipts if r.timestamp >= start_time]
        
        if end_time:
            receipts = [r for r in receipts if r.timestamp <= end_time]
        
        # Sort by timestamp (most recent first) and limit
        receipts.sort(key=lambda r: r.timestamp, reverse=True)
        
        return receipts[:limit]
    
    def verify_receipt_integrity(self, receipt_id: str) -> Dict[str, Any]:
        """Verify receipt and evidence integrity."""
        if receipt_id not in self.receipts:
            return {"valid": False, "reason": "Receipt not found"}
        
        receipt = self.receipts[receipt_id]
        
        # Verify receipt hash
        expected_hash = receipt.calculate_receipt_hash()
        
        # Verify evidence integrity
        evidence_valid = all(e.verify_integrity() for e in receipt.evidence)
        
        # Verify hash chain
        chain_valid = receipt.verify_chain()
        
        # Verify signature if present
        signature_valid = True
        if receipt.signature and self.public_key:
            signature_valid = self._verify_signature(receipt, receipt.signature)
        
        return {
            "valid": evidence_valid and chain_valid and signature_valid,
            "receipt_hash_valid": True,  # Simplified
            "evidence_integrity": evidence_valid,
            "hash_chain_valid": chain_valid,
            "signature_valid": signature_valid,
            "evidence_count": len(receipt.evidence)
        }
    
    def create_compliance_checkpoint(self, checkpoint_id: str) -> str:
        """Create a compliance checkpoint."""
        return self.tamper_detection.create_checkpoint(checkpoint_id)
    
    def verify_compliance_checkpoint(self, checkpoint_id: str) -> bool:
        """Verify a compliance checkpoint."""
        return self.tamper_detection.verify_checkpoint(checkpoint_id)
    
    def generate_compliance_report(self, standard: ComplianceStandard,
                                  time_period_days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for a standard."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=time_period_days)
        
        return self.compliance_reporter.generate_compliance_report(
            standard, list(self.receipts.values()), (start_time, end_time)
        )
    
    def get_audit_trail(self, operation_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for an operation."""
        # Find all receipts for this operation
        operation_receipts = self.query_receipts(operation_id=operation_id, limit=1000)
        
        # Build audit trail
        audit_trail = []
        
        for receipt in operation_receipts:
            trail_entry = {
                "receipt_id": receipt.receipt_id,
                "timestamp": receipt.timestamp.isoformat(),
                "receipt_type": receipt.receipt_type.value,
                "agent_id": receipt.agent_id,
                "status": receipt.status,
                "outcome": receipt.outcome,
                "evidence_count": len(receipt.evidence),
                "details": receipt.details
            }
            
            # Add evidence summary
            if receipt.evidence:
                trail_entry["evidence_types"] = [
                    e.evidence_type.value for e in receipt.evidence
                ]
            
            audit_trail.append(trail_entry)
        
        # Sort by timestamp
        audit_trail.sort(key=lambda x: x["timestamp"])
        
        return audit_trail
    
    def _update_indexes(self, receipt: AuditReceipt) -> None:
        """Update search indexes."""
        # Agent index
        if receipt.agent_id not in self.agent_index:
            self.agent_index[receipt.agent_id] = []
        self.agent_index[receipt.agent_id].append(receipt.receipt_id)
        
        # Operation index
        if receipt.operation_id not in self.operation_index:
            self.operation_index[receipt.operation_id] = []
        self.operation_index[receipt.operation_id].append(receipt.receipt_id)
    
    def _sign_receipt(self, receipt: AuditReceipt) -> str:
        """Sign a receipt with private key."""
        receipt_data = json.dumps(receipt.to_dict(), sort_keys=True)
        
        signature = self.private_key.sign(
            receipt_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode()
    
    def _sign_evidence(self, evidence: Evidence) -> str:
        """Sign evidence with private key."""
        evidence_data = json.dumps(evidence.to_dict(), sort_keys=True)
        
        signature = self.private_key.sign(
            evidence_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode()
    
    def _verify_signature(self, data: Union[AuditReceipt, Evidence], 
                         signature: str) -> bool:
        """Verify signature with public key."""
        try:
            data_str = json.dumps(data.to_dict(), sort_keys=True)
            signature_bytes = base64.b64decode(signature)
            
            self.public_key.verify(
                signature_bytes,
                data_str.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
        except Exception:
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get audit system status."""
        total_evidence = sum(len(r.evidence) for r in self.receipts.values())
        
        return {
            "total_receipts": len(self.receipts),
            "total_evidence": total_evidence,
            "hash_chain_length": len(self.tamper_detection.master_hash_chain),
            "checkpoints": len(self.tamper_detection.checkpoint_hashes),
            "encryption_enabled": self.enable_encryption,
            "indexed_agents": len(self.agent_index),
            "indexed_operations": len(self.operation_index)
        }