"""
NPE Delta Program v1.0 - Opcode Registry

Canonical ID: coh.npe.delta.v1.0
Numeric domain: QFixed18.int64.scale2^-18.be
Byte order: big-endian unless explicitly stated
Hash: SHA-256 over raw bytes
All integers are two's complement for signed types

This module implements:
1. Certificate Types Registry (v1.0)
2. Opcode Registry (v1.0)
3. Delta Program parser with strict length checks
4. RV safety rules
"""

import struct
import hashlib
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Dict, Any, Tuple


# =============================================================================
# Certificate Types Registry (v1.0)
# =============================================================================

class CertType(IntEnum):
    """Certificate type enum (u8)"""
    CERT_BOUND_Q18 = 0x01
    CERT_VECTOR_NORM_BOUND = 0x02
    CERT_MERKLE_INCLUSION = 0x03
    CERT_RENORM_QUOTIENT_SOUNDNESS = 0x10
    CERT_RENORM_UNFOLD_SAFETY = 0x11


@dataclass
class CertBoundQ18:
    """CERT_BOUND_Q18: scalar bound"""
    bound_q18: int  # i64_be


@dataclass
class CertVectorNormBound:
    """CERT_VECTOR_NORM_BOUND: norm bound with commitment"""
    dim: int  # u32_be
    v_hash: bytes  # 32 bytes
    bound_q18: int  # i64_be (upward-rounded)


@dataclass
class CertMerkleInclusion:
    """CERT_MERKLE_INCLUSION: membership proof"""
    leaf_hash: bytes  # 32 bytes
    depth: int  # u8
    path: List[bytes]  # list of 32-byte hashes


@dataclass
class CertRenormQuotientSoundness:
    """CERT_RENORM_QUOTIENT_SOUNDNESS: Lemma 1 witness"""
    subgraph_id: bytes  # 32 bytes
    proto_id: bytes  # 32 bytes
    L_q18: int  # i64_be
    rho_max_q18: int  # i64_be
    boundary_mismatch_q18: int  # i64_be
    variance_q18: int  # i64_be


@dataclass
class CertRenormUnfoldSafety:
    """CERT_RENORM_UNFOLD_SAFETY: Lemma 2 witness"""
    proto_id: bytes  # 32 bytes
    template_id: bytes  # 32 bytes
    init_penalty_q18: int  # i64_be
    hess_lmax_q18: int  # i64_be
    boundary_mismatch_q18: int  # i64_be


# Union type for any cert
Cert = CertBoundQ18 | CertVectorNormBound | CertMerkleInclusion | CertRenormQuotientSoundness | CertRenormUnfoldSafety


def parse_cert_payload(cert_type: int, payload: bytes) -> Cert:
    """
    Parse certificate payload based on type.
    
    Args:
        cert_type: u8 certificate type
        payload: raw certificate payload bytes
        
    Returns:
        Parsed certificate dataclass
        
    Raises:
        ValueError: If parsing fails
    """
    if cert_type == CertType.CERT_BOUND_Q18:
        if len(payload) != 8:
            raise ValueError(f"CERT_BOUND_Q18: expected 8 bytes, got {len(payload)}")
        return CertBoundQ18(bound_q18=struct.unpack('>q', payload)[0])
    
    elif cert_type == CertType.CERT_VECTOR_NORM_BOUND:
        if len(payload) < 44:  # 4 + 32 + 8
            raise ValueError(f"CERT_VECTOR_NORM_BOUND: payload too short")
        dim = struct.unpack('>I', payload[0:4])[0]
        v_hash = payload[4:36]
        bound_q18 = struct.unpack('>q', payload[36:44])[0]
        return CertVectorNormBound(dim=dim, v_hash=v_hash, bound_q18=bound_q18)
    
    elif cert_type == CertType.CERT_MERKLE_INCLUSION:
        if len(payload) < 33:
            raise ValueError(f"CERT_MERKLE_INCLUSION: payload too short")
        leaf_hash = payload[0:32]
        depth = payload[32]
        path = []
        offset = 33
        for _ in range(depth):
            if offset + 32 > len(payload):
                raise ValueError(f"CERT_MERKLE_INCLUSION: incomplete path")
            path.append(payload[offset:offset+32])
            offset += 32
        return CertMerkleInclusion(leaf_hash=leaf_hash, depth=depth, path=path)
    
    elif cert_type == CertType.CERT_RENORM_QUOTIENT_SOUNDNESS:
        if len(payload) != 56:  # 32 + 32 + 8 + 8 + 8 + 8
            raise ValueError(f"CERT_RENORM_QUOTIENT_SOUNDNESS: expected 56 bytes, got {len(payload)}")
        return CertRenormQuotientSoundness(
            subgraph_id=payload[0:32],
            proto_id=payload[32:64],
            L_q18=struct.unpack('>q', payload[64:72])[0],
            rho_max_q18=struct.unpack('>q', payload[72:80])[0],
            boundary_mismatch_q18=struct.unpack('>q', payload[80:88])[0],
            variance_q18=struct.unpack('>q', payload[88:96])[0]
        )
    
    elif cert_type == CertType.CERT_RENORM_UNFOLD_SAFETY:
        if len(payload) != 48:  # 32 + 32 + 8 + 8 + 8
            raise ValueError(f"CERT_RENORM_UNFOLD_SAFETY: expected 48 bytes, got {len(payload)}")
        return CertRenormUnfoldSafety(
            proto_id=payload[0:32],
            template_id=payload[32:64],
            init_penalty_q18=struct.unpack('>q', payload[64:72])[0],
            hess_lmax_q18=struct.unpack('>q', payload[72:80])[0],
            boundary_mismatch_q18=struct.unpack('>q', payload[80:88])[0]
        )
    
    else:
        raise ValueError(f"Unknown certificate type: {cert_type}")


def compute_cert_hash(cert_type: int, cert_flags: int, payload: bytes) -> bytes:
    """
    Compute SHA-256 hash of certificate.
    
    Args:
        cert_type: u8 certificate type
        cert_flags: u8 (must be 0x00 in v1.0)
        payload: raw certificate payload bytes
        
    Returns:
        32-byte SHA-256 hash
    """
    preimage = bytes([cert_type, cert_flags]) + struct.pack('>H', len(payload)) + payload
    return hashlib.sha256(preimage).digest()


def verify_cert_hash(cert_type: int, cert_flags: int, payload: bytes, expected_hash: bytes) -> bool:
    """
    Verify certificate hash.
    
    Args:
        cert_type: u8 certificate type
        cert_flags: u8
        payload: raw certificate payload bytes
        expected_hash: 32-byte expected hash
        
    Returns:
        True if hash matches
    """
    return compute_cert_hash(cert_type, cert_flags, payload) == expected_hash


# =============================================================================
# Opcode Registry (v1.0)
# =============================================================================

class Opcode(IntEnum):
    """Opcode enum"""
    # Z-domain opcodes (kind 0x00 or bundle)
    Z_SPARSE_ADD = 0x01
    Z_CLIP_NORM = 0x02
    Z_PROJ_K = 0x03
    Z_AFFINE_DIAG_BIAS = 0x04
    
    # A-domain opcodes (kind 0x01 or bundle)
    A_RENORM_QUOTIENT = 0x20
    A_RENORM_UNFOLD = 0x21
    A_EDIT_EDGE = 0x22
    
    # M-domain opcodes (kind 0x02 or bundle)
    M_PATCH_PREDICTOR_AFFINE = 0x40
    
    # Combinator opcodes
    SEQ_BARRIER = 0xF0
    IF_CERT = 0xF1


class DeltaKind(IntEnum):
    """Delta envelope kinds"""
    DELTA_Z = 0x00  # Z-domain
    DELTA_A = 0x01  # A-domain (renorm/unfold)
    DELTA_M = 0x02  # M-domain (model patches)
    DELTA_BUNDLE = 0x03  # Mixed domains


class ClipMode(IntEnum):
    """Clip mode for Z_CLIP_NORM"""
    L2 = 0x00  # L2 (policy-W)
    LINF = 0x01  # L-infinity


class BarrierKind(IntEnum):
    """Barrier kinds for SEQ_BARRIER"""
    NONE = 0x00
    CLIP_WINDOW_RESET = 0x01
    PROJ_REQUIRED = 0x02


class EditType(IntEnum):
    """Edge edit types for A_EDIT_EDGE"""
    ADD = 0x00
    REMOVE = 0x01


@dataclass
class Op:
    """Generic operation"""
    opcode: int
    flags: int
    arg_bytes: bytes


@dataclass
class OpZSparseAdd:
    """Z_SPARSE_ADD operation"""
    k: int  # number of updates
    updates: List[Tuple[int, int]]  # list of (idx, delta_q18)


@dataclass
class OpZClipNorm:
    """Z_CLIP_NORM operation"""
    cap_q18: int
    mode: int  # ClipMode


@dataclass
class OpZProjK:
    """Z_PROJ_K operation"""
    proj_id: bytes  # 32 bytes


@dataclass
class OpZAffineDiagBias:
    """Z_AFFINE_DIAG_BIAS operation"""
    diag_k: int
    diag_entries: List[Tuple[int, int]]  # (idx, scale_q18)
    bias_k: int
    bias_entries: List[Tuple[int, int]]  # (idx, bias_q18)


@dataclass
class OpARenormQuotient:
    """A_RENORM_QUOTIENT operation"""
    subgraph_id: bytes  # 32 bytes
    proto_id: bytes  # 32 bytes
    cert_sound_idx: int  # u16


@dataclass
class OpARenormUnfold:
    """A_RENORM_UNFOLD operation"""
    proto_id: bytes  # 32 bytes
    template_id: bytes  # 32 bytes
    cert_unfold_idx: int  # u16


@dataclass
class OpAEditEdge:
    """A_EDIT_EDGE operation"""
    edit_type: int  # EditType
    src: int  # u32
    dst: int  # u32
    edge_kind: int  # u8


@dataclass
class OpMPatchPredictorAffine:
    """M_PATCH_PREDICTOR_AFFINE operation"""
    patch_id: bytes  # 32 bytes
    cert_idx: int  # u16


@dataclass
class OpSeqBarrier:
    """SEQ_BARRIER operation"""
    barrier_kind: int  # BarrierKind


@dataclass
class OpIfCert:
    """IF_CERT operation"""
    pred_cert_idx: int  # u16
    then_bytes: bytes
    else_bytes: bytes


def parse_op(opcode: int, flags: int, arg_bytes: bytes) -> Any:
    """
    Parse operation based on opcode.
    
    Args:
        opcode: u8 opcode
        flags: u8 flags
        arg_bytes: raw argument bytes
        
    Returns:
        Parsed operation dataclass
        
    Raises:
        ValueError: If parsing fails
    """
    offset = 0
    
    if opcode == Opcode.Z_SPARSE_ADD:
        if len(arg_bytes) < 2:
            raise ValueError("Z_SPARSE_ADD: args too short")
        k = struct.unpack('>H', arg_bytes[0:2])[0]
        offset = 2
        updates = []
        for _ in range(k):
            if offset + 12 > len(arg_bytes):
                raise ValueError("Z_SPARSE_ADD: incomplete args")
            idx = struct.unpack('>I', arg_bytes[offset:offset+4])[0]
            delta_q18 = struct.unpack('>q', arg_bytes[offset+4:offset+12])[0]
            updates.append((idx, delta_q18))
            offset += 12
        return OpZSparseAdd(k=k, updates=updates)
    
    elif opcode == Opcode.Z_CLIP_NORM:
        if len(arg_bytes) < 9:
            raise ValueError("Z_CLIP_NORM: args too short")
        cap_q18 = struct.unpack('>q', arg_bytes[0:8])[0]
        mode = arg_bytes[8]
        return OpZClipNorm(cap_q18=cap_q18, mode=mode)
    
    elif opcode == Opcode.Z_PROJ_K:
        if len(arg_bytes) != 32:
            raise ValueError(f"Z_PROJ_K: expected 32 bytes, got {len(arg_bytes)}")
        return OpZProjK(proj_id=arg_bytes)
    
    elif opcode == Opcode.Z_AFFINE_DIAG_BIAS:
        if len(arg_bytes) < 4:
            raise ValueError("Z_AFFINE_DIAG_BIAS: args too short")
        diag_k = struct.unpack('>H', arg_bytes[0:2])[0]
        bias_k = struct.unpack('>H', arg_bytes[2:4])[0]
        offset = 4
        diag_entries = []
        for _ in range(diag_k):
            if offset + 12 > len(arg_bytes):
                raise ValueError("Z_AFFINE_DIAG_BIAS: incomplete diag entries")
            idx = struct.unpack('>I', arg_bytes[offset:offset+4])[0]
            scale_q18 = struct.unpack('>q', arg_bytes[offset+4:offset+12])[0]
            diag_entries.append((idx, scale_q18))
            offset += 12
        bias_entries = []
        for _ in range(bias_k):
            if offset + 12 > len(arg_bytes):
                raise ValueError("Z_AFFINE_DIAG_BIAS: incomplete bias entries")
            idx = struct.unpack('>I', arg_bytes[offset:offset+4])[0]
            bias_q18 = struct.unpack('>q', arg_bytes[offset+4:offset+12])[0]
            bias_entries.append((idx, bias_q18))
            offset += 12
        return OpZAffineDiagBias(diag_k=diag_k, diag_entries=diag_entries, bias_k=bias_k, bias_entries=bias_entries)
    
    elif opcode == Opcode.A_RENORM_QUOTIENT:
        if len(arg_bytes) != 68:  # 32 + 32 + 4
            raise ValueError(f"A_RENORM_QUOTIENT: expected 68 bytes, got {len(arg_bytes)}")
        return OpARenormQuotient(
            subgraph_id=arg_bytes[0:32],
            proto_id=arg_bytes[32:64],
            cert_sound_idx=struct.unpack('>H', arg_bytes[64:66])[0]
        )
    
    elif opcode == Opcode.A_RENORM_UNFOLD:
        if len(arg_bytes) != 68:  # 32 + 32 + 4
            raise ValueError(f"A_RENORM_UNFOLD: expected 68 bytes, got {len(arg_bytes)}")
        return OpARenormUnfold(
            proto_id=arg_bytes[0:32],
            template_id=arg_bytes[32:64],
            cert_unfold_idx=struct.unpack('>H', arg_bytes[64:66])[0]
        )
    
    elif opcode == Opcode.A_EDIT_EDGE:
        if len(arg_bytes) != 10:
            raise ValueError(f"A_EDIT_EDGE: expected 10 bytes, got {len(arg_bytes)}")
        return OpAEditEdge(
            edit_type=arg_bytes[0],
            src=struct.unpack('>I', arg_bytes[1:5])[0],
            dst=struct.unpack('>I', arg_bytes[5:9])[0],
            edge_kind=arg_bytes[9]
        )
    
    elif opcode == Opcode.M_PATCH_PREDICTOR_AFFINE:
        if len(arg_bytes) != 34:  # 32 + 2
            raise ValueError(f"M_PATCH_PREDICTOR_AFFINE: expected 34 bytes, got {len(arg_bytes)}")
        return OpMPatchPredictorAffine(
            patch_id=arg_bytes[0:32],
            cert_idx=struct.unpack('>H', arg_bytes[32:34])[0]
        )
    
    elif opcode == Opcode.SEQ_BARRIER:
        if len(arg_bytes) != 1:
            raise ValueError(f"SEQ_BARRIER: expected 1 byte, got {len(arg_bytes)}")
        return OpSeqBarrier(barrier_kind=arg_bytes[0])
    
    elif opcode == Opcode.IF_CERT:
        if len(arg_bytes) < 6:
            raise ValueError("IF_CERT: args too short")
        pred_cert_idx = struct.unpack('>H', arg_bytes[0:2])[0]
        then_len = struct.unpack('>H', arg_bytes[2:4])[0]
        offset = 4
        if offset + then_len > len(arg_bytes):
            raise ValueError("IF_CERT: incomplete then branch")
        then_bytes = arg_bytes[offset:offset+then_len]
        offset += then_len
        if offset + 2 > len(arg_bytes):
            raise ValueError("IF_CERT: missing else length")
        else_len = struct.unpack('>H', arg_bytes[offset:offset+2])[0]
        offset += 2
        if offset + else_len > len(arg_bytes):
            raise ValueError("IF_CERT: incomplete else branch")
        else_bytes = arg_bytes[offset:offset+else_len]
        return OpIfCert(pred_cert_idx=pred_cert_idx, then_bytes=then_bytes, else_bytes=else_bytes)
    
    else:
        raise ValueError(f"Unknown opcode: {opcode}")


# =============================================================================
# Delta Program Parser (v1.0)
# =============================================================================

DELTA_VERSION = 0x01


@dataclass
class CertEntry:
    """Parsed certificate entry"""
    cert_type: int
    cert_flags: int
    payload: bytes
    cert_hash: bytes  # 32 bytes


@dataclass
class DeltaProgram:
    """Parsed delta program"""
    version: int
    kind: int  # DeltaKind
    ops: List[Op]
    certs: List[CertEntry]


def parse_delta_program(data: bytes) -> DeltaProgram:
    """
    Parse delta program with strict length checks.
    
    Implements RV safety rules:
    1. Decode base64 → bytes (caller does this)
    2. Parse delta_program with strict length checks
    3. Reject if unknown version/kind
    4. Reject if certs_len doesn't match trailing bytes
    5. Parse cert block, verify each cert_hash
    
    Args:
        data: Raw delta program bytes
        
    Returns:
        Parsed DeltaProgram
        
    Raises:
        ValueError: If parsing fails (fork-proof)
    """
    offset = 0
    
    # 1. Version (u8)
    if len(data) < 1:
        raise ValueError("Delta program: insufficient data for version")
    version = data[0]
    offset = 1
    
    if version != DELTA_VERSION:
        raise ValueError(f"Delta program: unknown version {version}, expected {DELTA_VERSION}")
    
    # 2. Kind (u8)
    if len(data) < offset + 1:
        raise ValueError("Delta program: insufficient data for kind")
    kind = data[offset]
    offset += 1
    
    if kind not in [0x00, 0x01, 0x02, 0x03]:
        raise ValueError(f"Delta program: unknown kind {kind}")
    
    # 3. op_count (u16_be)
    if len(data) < offset + 2:
        raise ValueError("Delta program: insufficient data for op_count")
    op_count = struct.unpack('>H', data[offset:offset+2])[0]
    offset += 2
    
    # 4. Parse ops
    ops = []
    for _ in range(op_count):
        # opcode (u8)
        if offset + 1 > len(data):
            raise ValueError("Delta program: insufficient data for opcode")
        opcode = data[offset]
        offset += 1
        
        # flags (u8)
        if offset + 1 > len(data):
            raise ValueError("Delta program: insufficient data for flags")
        flags = data[offset]
        offset += 1
        
        # arg_len (u16_be)
        if offset + 2 > len(data):
            raise ValueError("Delta program: insufficient data for arg_len")
        arg_len = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        # arg_bytes
        if offset + arg_len > len(data):
            raise ValueError(f"Delta program: insufficient data for args (need {arg_len}, have {len(data)-offset})")
        arg_bytes = data[offset:offset+arg_len]
        offset += arg_len
        
        # Parse the op
        try:
            parsed_op = parse_op(opcode, flags, arg_bytes)
            ops.append(Op(opcode=opcode, flags=flags, arg_bytes=arg_bytes))
        except Exception as e:
            raise ValueError(f"Delta program: failed to parse op {opcode}: {e}")
    
    # 5. certs_len (u32_be)
    if offset + 4 > len(data):
        raise ValueError("Delta program: insufficient data for certs_len")
    certs_len = struct.unpack('>I', data[offset:offset+4])[0]
    offset += 4
    
    # 6. Verify certs_len matches remaining bytes
    if offset + certs_len != len(data):
        raise ValueError(
            f"Delta program: certs_len mismatch: declared {certs_len}, "
            f"actual trailing bytes {len(data)-offset}"
        )
    
    # 7. Parse certs block
    certs = []
    if certs_len > 0:
        # cert_count (u16_be)
        if offset + 2 > len(data):
            raise ValueError("Delta program: insufficient data for cert_count")
        cert_count = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        
        for _ in range(cert_count):
            # cert_type (u8)
            if offset + 1 > len(data):
                raise ValueError("Delta program: insufficient data for cert_type")
            cert_type = data[offset]
            offset += 1
            
            # cert_flags (u8)
            if offset + 1 > len(data):
                raise ValueError("Delta program: insufficient data for cert_flags")
            cert_flags = data[offset]
            offset += 1
            
            # cert_payload_len (u16_be)
            if offset + 2 > len(data):
                raise ValueError("Delta program: insufficient data for cert_payload_len")
            cert_payload_len = struct.unpack('>H', data[offset:offset+2])[0]
            offset += 2
            
            # cert_payload
            if offset + cert_payload_len > len(data):
                raise ValueError("Delta program: insufficient data for cert_payload")
            cert_payload = data[offset:offset+cert_payload_len]
            offset += cert_payload_len
            
            # cert_hash (32 bytes)
            if offset + 32 > len(data):
                raise ValueError("Delta program: insufficient data for cert_hash")
            cert_hash = data[offset:offset+32]
            offset += 32
            
            # Verify cert_hash
            if not verify_cert_hash(cert_type, cert_flags, cert_payload, cert_hash):
                raise ValueError(f"Delta program: cert_hash mismatch")
            
            certs.append(CertEntry(
                cert_type=cert_type,
                cert_flags=cert_flags,
                payload=cert_payload,
                cert_hash=cert_hash
            ))
    
    return DeltaProgram(version=version, kind=kind, ops=ops, certs=certs)


# =============================================================================
# Opcode Domain Mapping
# =============================================================================

# Map opcodes to their valid domains
OPCODE_DOMAINS: Dict[int, List[int]] = {
    # Z-domain opcodes
    Opcode.Z_SPARSE_ADD: [DeltaKind.DELTA_Z, DeltaKind.DELTA_BUNDLE],
    Opcode.Z_CLIP_NORM: [DeltaKind.DELTA_Z, DeltaKind.DELTA_BUNDLE],
    Opcode.Z_PROJ_K: [DeltaKind.DELTA_Z, DeltaKind.DELTA_BUNDLE],
    Opcode.Z_AFFINE_DIAG_BIAS: [DeltaKind.DELTA_Z, DeltaKind.DELTA_BUNDLE],
    # A-domain opcodes
    Opcode.A_RENORM_QUOTIENT: [DeltaKind.DELTA_A, DeltaKind.DELTA_BUNDLE],
    Opcode.A_RENORM_UNFOLD: [DeltaKind.DELTA_A, DeltaKind.DELTA_BUNDLE],
    Opcode.A_EDIT_EDGE: [DeltaKind.DELTA_A, DeltaKind.DELTA_BUNDLE],
    # M-domain opcodes
    Opcode.M_PATCH_PREDICTOR_AFFINE: [DeltaKind.DELTA_M, DeltaKind.DELTA_BUNDLE],
    # Combinator opcodes (allowed in any bundle)
    Opcode.SEQ_BARRIER: [DeltaKind.DELTA_BUNDLE],
    Opcode.IF_CERT: [DeltaKind.DELTA_BUNDLE],
}


def validate_opcode_domain(opcode: int, kind: int) -> bool:
    """
    Validate that opcode is allowed in the given kind.
    
    Args:
        opcode: u8 opcode
        kind: DeltaKind
        
    Returns:
        True if allowed
    """
    if kind == DeltaKind.DELTA_BUNDLE:
        # In bundle mode, most opcodes are allowed
        return True
    
    allowed_domains = OPCODE_DOMAINS.get(opcode, [])
    return kind in allowed_domains


# =============================================================================
# Required Certs Mapping
# =============================================================================

# Map opcodes to their required cert types (by index in certs list)
OPCODE_REQUIRED_CERTS: Dict[int, Dict[str, int]] = {
    Opcode.A_RENORM_QUOTIENT: {"cert_sound_idx": CertType.CERT_RENORM_QUOTIENT_SOUNDNESS},
    Opcode.A_RENORM_UNFOLD: {"cert_unfold_idx": CertType.CERT_RENORM_UNFOLD_SAFETY},
    Opcode.M_PATCH_PREDICTOR_AFFINE: {"cert_idx": None},  # Requires custom cert type
}


def validate_required_certs(op: Op, certs: List[CertEntry]) -> Tuple[bool, str]:
    """
    Validate that required certs are present and have correct types.
    
    Args:
        op: Parsed operation
        certs: List of certificate entries
        
    Returns:
        (is_valid, error_message)
    """
    required = OPCODE_REQUIRED_CERTS.get(op.opcode, {})
    if not required:
        return True, ""
    
    # Parse the operation to get cert indices
    try:
        parsed = parse_op(op.opcode, op.flags, op.arg_bytes)
    except Exception as e:
        return False, f"Failed to parse op {op.opcode}: {e}"
    
    for idx_name, expected_cert_type in required.items():
        # Get the cert index from the parsed op
        cert_idx = getattr(parsed, idx_name, None)
        if cert_idx is None:
            return False, f"Missing cert index {idx_name} in op {op.opcode}"
        
        if cert_idx >= len(certs):
            return False, f"Cert index {cert_idx} out of range"
        
        actual_cert_type = certs[cert_idx].cert_type
        
        if expected_cert_type is not None and actual_cert_type != expected_cert_type:
            return False, (
                f"Wrong cert type for {idx_name}: "
                f"expected {CertType(expected_cert_type).name}, "
                f"got {CertType(actual_cert_type).name}"
            )
    
    return True, ""
