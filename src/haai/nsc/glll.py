"""
GLLL (Hadamard Glyph Low-Level Language) implementation.

Implements Hadamard matrix encoding, glyph feature vectors, confidence scoring,
and error detection as defined in the GLLL specification.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import time
import logging
import json

logger = logging.getLogger(__name__)


class GLLLGlyph(Enum):
    """GLLL glyphs as defined in specification."""
    # Core glyphs
    PHI = "φ"        # introduce θ
    RHO = "↻"        # curvature coupling
    PLUS = "⊕"       # source +s
    MINUS = "⊖"      # sink -s
    CIRCLE = "◯"      # ∇²θ
    DELTA = "∆"       # close EOM
    ARROW = "⇒"      # time marker
    BOX = "□"         # boundary
    
    # Extended glyphs
    LEFT_ARROW = "⇐"  # reverse time
    CIRCLE_CCW = "↺"  # counter-clockwise
    INFINITY = "∞"    # infinity
    NABLA = "∇"      # gradient
    PARTIAL = "∂"      # partial derivative
    INTEGRAL = "∫"    # integral
    SUM = "∑"         # summation
    PRODUCT = "∏"     # product
    SQRT = "√"        # square root
    ALPHA = "α"        # alpha
    BETA = "β"         # beta
    GAMMA = "γ"        # gamma
    DELTA_GREEK = "δ"  # delta (Greek)
    EPSILON = "ε"      # epsilon
    LAMBDA = "λ"       # lambda
    MU = "μ"           # mu
    NU = "ν"           # nu
    PI = "π"           # pi
    SIGMA = "σ"        # sigma
    TAU = "τ"          # tau
    PHI_GREEK = "Φ"    # phi (Greek)
    CHI = "χ"          # chi
    PSI = "ψ"          # psi
    OMEGA = "ω"        # omega


@dataclass
class GlyphEncoding:
    """Glyph encoding with Hadamard feature vector."""
    glyph: str
    feature_vector: np.ndarray
    confidence_threshold: float = 0.8
    category: str = "core"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'glyph': self.glyph,
            'feature_vector': self.feature_vector.tolist(),
            'confidence_threshold': self.confidence_threshold,
            'category': self.category
        }

    @property
    def encoding(self) -> np.ndarray:
        """Backward-compatible alias for feature_vector used by tests."""
        return self.feature_vector


class HadamardMatrix:
    """Hadamard matrix generator for maximal glyph separation."""
    
    def __init__(self, order: int = 64):
        """
        Initialize Hadamard matrix.
        
        Args:
            order: Order of Hadamard matrix (must be power of 2)
        """
        if not self._is_power_of_2(order):
            raise ValueError(f"Order {order} is not a power of 2")
        
        self.order = order
        self.matrix = self._generate_hadamard(order)
        self.encoding_cache: Dict[str, np.ndarray] = {}
    
    def _is_power_of_2(self, n: int) -> bool:
        """Check if n is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0
    
    def _generate_hadamard(self, n: int) -> np.ndarray:
        """Generate Hadamard matrix of order n using Sylvester construction."""
        if n == 1:
            return np.array([[1]])
        elif n == 2:
            return np.array([[1, 1], [1, -1]])
        else:
            # Recursive construction
            H_half = self._generate_hadamard(n // 2)
            H = np.zeros((n, n), dtype=int)
            
            # [H  H]
            # [H -H]
            H[:n//2, :n//2] = H_half
            H[:n//2, n//2:] = H_half
            H[n//2:, :n//2] = H_half
            H[n//2:, n//2:] = -H_half
            
            return H
    
    def encode_glyph(self, glyph: str) -> np.ndarray:
        """Encode glyph using Hadamard matrix."""
        if glyph in self.encoding_cache:
            return self.encoding_cache[glyph]
        
        # Convert glyph to index
        glyph_code = sum(ord(c) for c in glyph)
        index = glyph_code % self.order
        
        # Get corresponding row from Hadamard matrix
        encoding = self.matrix[index, :]
        
        # Cache result
        self.encoding_cache[glyph] = encoding
        
        return encoding
    
    def get_separation_matrix(self) -> np.ndarray:
        """Get glyph separation matrix for confidence calculation."""
        # Compute pairwise distances between all glyph encodings
        encodings = list(self.encoding_cache.values())
        if len(encodings) < 2:
            return np.array([[0]])
        
        separation_matrix = np.zeros((len(encodings), len(encodings)))
        for i, enc1 in enumerate(encodings):
            for j, enc2 in enumerate(encodings):
                # Hamming distance for ±1 vectors
                distance = np.sum(enc1 != enc2) / len(enc1)
                separation_matrix[i, j] = distance
        
        return separation_matrix


class GlyphDictionary:
    """Dictionary for managing glyph encodings and metadata."""
    
    def __init__(self, hadamard_order: int = 64):
        self.hadamard = HadamardMatrix(hadamard_order)
        self.glyphs: Dict[str, GlyphEncoding] = {}
        self.categories: Dict[str, List[str]] = {}
        self._initialize_default_glyphs()
    
    def _initialize_default_glyphs(self) -> None:
        """Initialize default glyph encodings."""
        # Core glyphs
        core_glyphs = [glyph.value for glyph in GLLLGlyph if glyph.name in [
            'PHI', 'RHO', 'PLUS', 'MINUS', 'CIRCLE', 'DELTA', 'ARROW', 'BOX'
        ]]
        
        for glyph in core_glyphs:
            self.add_glyph(glyph, "core", 0.8)
        
        # Extended glyphs
        extended_glyphs = [glyph.value for glyph in GLLLGlyph if glyph.name not in [
            'PHI', 'RHO', 'PLUS', 'MINUS', 'CIRCLE', 'DELTA', 'ARROW', 'BOX'
        ]]
        
        for glyph in extended_glyphs:
            self.add_glyph(glyph, "extended", 0.7)
    
    def add_glyph(self, glyph: str, category: str = "custom", 
                 confidence_threshold: float = 0.8) -> None:
        """Add a new glyph to the dictionary."""
        feature_vector = self.hadamard.encode_glyph(glyph)
        
        encoding = GlyphEncoding(
            glyph=glyph,
            feature_vector=feature_vector,
            confidence_threshold=confidence_threshold,
            category=category
        )
        
        self.glyphs[glyph] = encoding
        
        # Update category
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(glyph)
        
        logger.info(f"Added glyph '{glyph}' to category '{category}'")
    
    def get_encoding(self, glyph: str) -> Optional[GlyphEncoding]:
        """Get encoding for a specific glyph."""
        return self.glyphs.get(glyph)
    
    def get_all_glyphs(self) -> List[str]:
        """Get list of all glyphs."""
        return list(self.glyphs.keys())
    
    def get_glyphs_by_category(self, category: str) -> List[str]:
        """Get glyphs by category."""
        return self.categories.get(category, [])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dictionary to JSON-serializable format."""
        return {
            'glyphs': {glyph: encoding.to_dict() for glyph, encoding in self.glyphs.items()},
            'categories': self.categories,
            'hadamard_order': self.hadamard.order
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load dictionary from JSON-serializable format."""
        self.glyphs.clear()
        self.categories.clear()
        
        for glyph, encoding_data in data['glyphs'].items():
            encoding = GlyphEncoding(
                glyph=encoding_data['glyph'],
                feature_vector=np.array(encoding_data['feature_vector']),
                confidence_threshold=encoding_data['confidence_threshold'],
                category=encoding_data['category']
            )
            self.glyphs[glyph] = encoding
        
        self.categories = data['categories']
        
        # Reinitialize Hadamard matrix if needed
        if data['hadamard_order'] != self.hadamard.order:
            self.hadamard = HadamardMatrix(data['hadamard_order'])


class GLLLEncoder:
    """GLLL encoder with confidence scoring and error detection.

    Accepts either an explicit GlyphDictionary or a hadamard_order to create
    an internal dictionary. This provides backward-compatible constructor
    parameters for tests that pass a hadamard_order kwarg.
    """

    def __init__(self, dictionary: Optional[GlyphDictionary] = None, hadamard_order: Optional[int] = None):
        if dictionary is not None:
            self.dictionary = dictionary
        else:
            order = int(hadamard_order) if hadamard_order is not None else 64
            self.dictionary = GlyphDictionary(order)

        self.encoding_history: List[Dict[str, Any]] = []
        self.error_correction_enabled = True
    
    # Convenience properties/methods
    @property
    def hadamard_matrix(self) -> np.ndarray:
        """Get the Hadamard matrix."""
        return self.dictionary.hadamard.matrix
    
    @property
    def glyph_dictionary(self) -> Dict[str, GlyphEncoding]:
        """Get the glyph dictionary."""
        return self.dictionary.glyphs
    
    @property
    def hadamard_order(self) -> int:
        """Get the Hadamard order."""
        return self.dictionary.hadamard.order
    
    def encode_glyph(self, glyph: str) -> GlyphEncoding:
        """Encode a single glyph."""
        encoding = self.dictionary.get_encoding(glyph)
        if encoding is None:
            # Create encoding for unknown glyph
            feature_vector = self.dictionary.hadamard.encode_glyph(glyph)
            encoding = GlyphEncoding(
                glyph=glyph,
                feature_vector=feature_vector,
                confidence_threshold=0.5,
                category="unknown"
            )
        return encoding
    
    def get_all_glyphs(self) -> List[str]:
        """Get all glyphs."""
        return self.dictionary.get_all_glyphs()
    
    def get_encoding(self, glyph: str) -> Optional[GlyphEncoding]:
        """Get encoding for a glyph."""
        return self.dictionary.get_encoding(glyph)
    
    def encode_sequence(self, sequence: str) -> Dict[str, Any]:
        """
        Encode a sequence of glyphs with confidence scoring.
        
        Core decode algorithm:
        - score(r) = (1/n) Σ v_j r_j
        - choose argmax score
        - compute confidence + margin
        - emit receipt when uncertain
        """
        start_time = time.time()
        
        # Extract individual glyphs from sequence
        glyphs = self._extract_glyphs(sequence)
        
        # Encode each glyph
        encodings = []
        confidences = []
        margins = []
        
        for glyph in glyphs:
            encoding_result = self._encode_glyph_with_confidence(glyph)
            encodings.append(encoding_result['encoding'])
            confidences.append(encoding_result['confidence'])
            margins.append(encoding_result['margin'])
        
        # Compute overall sequence metrics
        avg_confidence = np.mean(confidences) if confidences else 0.0
        min_margin = np.min(margins) if margins else 0.0
        
        # Check if we need to emit receipt (low confidence)
        emit_receipt = avg_confidence < 0.7 or min_margin < 0.2
        
        encoding_time = time.time() - start_time
        
        result = {
            'success': True,
            'sequence': sequence,
            'glyphs': glyphs,
            'encodings': [e.tolist() for e in encodings],
            'confidences': confidences,
            'margins': margins,
            'avg_confidence': avg_confidence,
            'min_margin': min_margin,
            'emit_receipt': emit_receipt,
            'encoding_time': encoding_time
        }
        
        # Record encoding
        self.encoding_history.append(result)
        
        return result
    
    def _extract_glyphs(self, sequence: str) -> List[str]:
        """Extract individual glyphs from sequence."""
        glyphs = []
        i = 0
        
        while i < len(sequence):
            # Try to match longest possible glyph
            found = False
            for glyph in sorted(self.dictionary.get_all_glyphs(), key=len, reverse=True):
                if sequence.startswith(glyph, i):
                    glyphs.append(glyph)
                    i += len(glyph)
                    found = True
                    break
            
            if not found:
                # Unknown character, skip
                i += 1
        
        return glyphs
    
    def _encode_glyph_with_confidence(self, glyph: str) -> Dict[str, Any]:
        """Encode single glyph with confidence scoring."""
        encoding_info = self.dictionary.get_encoding(glyph)
        
        if encoding_info is None:
            # Unknown glyph - create encoding with low confidence
            feature_vector = self.dictionary.hadamard.encode_glyph(glyph)
            return {
                'encoding': feature_vector,
                'confidence': 0.1,
                'margin': 0.0,
                'known_glyph': False
            }
        
        # Calculate confidence using score(r) = (1/n) Σ v_j r_j
        feature_vector = encoding_info.feature_vector
        
        # For confidence, we use the separation from other glyphs
        all_glyphs = self.dictionary.get_all_glyphs()
        scores = []
        
        for other_glyph in all_glyphs:
            if other_glyph == glyph:
                continue
            
            other_encoding = self.dictionary.get_encoding(other_glyph)
            if other_encoding:
                # Calculate dot product score
                score = np.dot(feature_vector, other_encoding.feature_vector) / len(feature_vector)
                scores.append(abs(score))
        
        # Confidence is based on separation from other glyphs
        if scores:
            min_score = min(scores)
            confidence = 1.0 - min_score  # Higher confidence when more separated
            margin = confidence - encoding_info.confidence_threshold
        else:
            confidence = 1.0  # Only glyph in dictionary
            margin = 1.0 - encoding_info.confidence_threshold
        
        return {
            'encoding': feature_vector,
            'confidence': confidence,
            'margin': margin,
            'known_glyph': True
        }
    
    def decode_sequence(self, encoded_sequence: List[np.ndarray]) -> Dict[str, Any]:
        """Decode encoded sequence back to glyphs."""
        start_time = time.time()
        
        decoded_glyphs = []
        confidences = []
        
        for encoding in encoded_sequence:
            decode_result = self._decode_encoding(encoding)
            decoded_glyphs.append(decode_result['glyph'])
            confidences.append(decode_result['confidence'])
        
        # Reconstruct sequence
        sequence = ''.join(decoded_glyphs)
        avg_confidence = np.mean(confidences) if confidences else 0.0
        decoding_time = time.time() - start_time
        
        return {
            'success': True,
            'sequence': sequence,
            'glyphs': decoded_glyphs,
            'confidences': confidences,
            'avg_confidence': avg_confidence,
            'decoding_time': decoding_time
        }
    
    def _decode_encoding(self, encoding: np.ndarray) -> Dict[str, Any]:
        """Decode single encoding to glyph with confidence."""
        best_glyph = None
        best_score = -1.0
        
        for glyph, glyph_info in self.dictionary.glyphs.items():
            # Calculate score using dot product
            score = np.dot(encoding, glyph_info.feature_vector) / len(encoding)
            
            if score > best_score:
                best_score = score
                best_glyph = glyph
        
        # Confidence based on best score
        confidence = max(0.0, best_score)
        
        return {
            'glyph': best_glyph or '?',
            'confidence': confidence,
            'score': best_score
        }
    
    def detect_and_correct_errors(self, encoded_sequence: List[np.ndarray]) -> Dict[str, Any]:
        """Detect and correct errors in encoded sequence."""
        if not self.error_correction_enabled:
            return {'errors_detected': 0, 'corrected_sequence': encoded_sequence}
        
        errors_detected = 0
        corrected_sequence = []
        
        for i, encoding in enumerate(encoded_sequence):
            # Check if encoding is valid (±1 values)
            if not np.all(np.isin(encoding, [-1, 1])):
                errors_detected += 1
                # Correct by rounding to nearest ±1
                corrected = np.sign(encoding)
                corrected[np.abs(corrected) < 0.5] = 1  # Handle zero case
                corrected_sequence.append(corrected)
            else:
                corrected_sequence.append(encoding)
        
        return {
            'errors_detected': errors_detected,
            'corrected_sequence': corrected_sequence,
            'error_rate': errors_detected / len(encoded_sequence) if encoded_sequence else 0.0
        }
    
    def get_encoding_statistics(self) -> Dict[str, Any]:
        """Get statistics about encoding performance."""
        if not self.encoding_history:
            return {"status": "no_history"}
        
        confidences = [h['avg_confidence'] for h in self.encoding_history]
        margins = [h['min_margin'] for h in self.encoding_history]
        encoding_times = [h['encoding_time'] for h in self.encoding_history]
        
        return {
            'total_encodings': len(self.encoding_history),
            'avg_confidence': np.mean(confidences),
            'min_confidence': np.min(confidences),
            'max_confidence': np.max(confidences),
            'avg_margin': np.mean(margins),
            'min_margin': np.min(margins),
            'avg_encoding_time': np.mean(encoding_times),
            'receipt_emission_rate': sum(1 for h in self.encoding_history if h['emit_receipt']) / len(self.encoding_history)
        }
    
    def save_dictionary(self, filepath: str) -> None:
        """Save glyph dictionary to file."""
        data = self.dictionary.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved glyph dictionary to {filepath}")
    
    def load_dictionary(self, filepath: str) -> None:
        """Load glyph dictionary from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.dictionary.from_dict(data)
        logger.info(f"Loaded glyph dictionary from {filepath}")

    async def initialize(self) -> Dict[str, Any]:
        """Initialize encoder (async for compatibility)."""
        summary = self.get_encoding_statistics()
        logger.info("GLLL Encoder initialized")
        return summary

    async def shutdown(self) -> None:
        """Shutdown encoder."""
        logger.info("GLLL Encoder shutdown")

    async def cleanup(self) -> None:
        """Cleanup encoder resources."""
        await self.shutdown()


class GLLLProcessor:
    """High-level GLLL processor that coordinates encoding and decoding."""
    
    def __init__(self, hadamard_order: int = 64):
        self.dictionary = GlyphDictionary(hadamard_order)
        self.encoder = GLLLEncoder(self.dictionary)
        self.processing_history: List[Dict[str, Any]] = []
    
    def process_text(self, text: str, operation: str = "encode") -> Dict[str, Any]:
        """Process text with specified operation."""
        start_time = time.time()
        
        try:
            if operation == "encode":
                result = self.encoder.encode_sequence(text)
            elif operation == "decode":
                # For decode, we expect the text to be a representation of encoded data
                # This is a simplified implementation
                result = {'success': False, 'error': 'Direct decode from text not implemented'}
            else:
                result = {'success': False, 'error': f'Unknown operation: {operation}'}
            
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
        except Exception as e:
            logger.error(f"GLLL processing failed: {e}")
            result = {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
        
        # Record processing
        self.processing_history.append({
            'timestamp': time.time(),
            'text': text,
            'operation': operation,
            'result': result
        })
        
        return result
    
    def get_processor_summary(self) -> Dict[str, Any]:
        """Get summary of processor state."""
        encoding_stats = self.encoder.get_encoding_statistics()
        
        return {
            'dictionary_size': len(self.dictionary.glyphs),
            'categories': list(self.dictionary.categories.keys()),
            'hadamard_order': self.dictionary.hadamard.order,
            'encoding_statistics': encoding_stats,
            'processing_history_size': len(self.processing_history)
        }
