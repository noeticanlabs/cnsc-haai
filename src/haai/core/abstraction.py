"""
Hierarchical abstraction framework implementation.

Implements the core hierarchical abstraction system with levels, cross-level mappings,
and state management as defined in the HAAI specification.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class LevelState:
    """State representation at a specific abstraction level."""
    level: int
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    provenance: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'level': self.level,
            'data': self.data.tolist() if isinstance(self.data, np.ndarray) else self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'provenance': self.provenance
        }


class CrossLevelMap(ABC):
    """Abstract base class for cross-level mappings."""
    
    def __init__(self, source_level: int, target_level: int, name: str):
        self.source_level = source_level
        self.target_level = target_level
        self.name = name
        self.is_trained = False
        self.training_history: List[Dict[str, Any]] = []
    
    @abstractmethod
    def forward(self, state: LevelState) -> LevelState:
        """Map from source level to target level."""
        pass
    
    @abstractmethod
    def backward(self, state: LevelState) -> LevelState:
        """Map from target level back to source level."""
        pass
    
    def train(self, source_states: List[LevelState], target_states: List[LevelState]) -> None:
        """Train the mapping on paired examples."""
        # Default implementation - subclasses should override
        self.is_trained = True
        self.training_history.append({
            'timestamp': time.time(),
            'num_examples': len(source_states),
            'source_level': self.source_level,
            'target_level': self.target_level
        })


class LinearAbstractionMap(CrossLevelMap):
    """Linear abstraction map using dimensionality reduction."""
    
    def __init__(self, source_level: int, target_level: int, compression_ratio: float = 0.5):
        super().__init__(source_level, target_level, f"linear_{source_level}_to_{target_level}")
        self.compression_ratio = compression_ratio
        self.weights: Optional[np.ndarray] = None
        self.bias: Optional[np.ndarray] = None
        self.inv_weights: Optional[np.ndarray] = None
        self.inv_bias: Optional[np.ndarray] = None
    
    def forward(self, state: LevelState) -> LevelState:
        """Compress data using linear transformation."""
        if not self.is_trained:
            logger.warning(f"Map {self.name} not trained, returning input with identity transform")
            # Return input unchanged with warning metadata
            return LevelState(
                level=state.level,
                data=state.data,
                metadata={
                    **state.metadata,
                    'warning': f"Map {self.name} not trained, identity transform applied",
                    'identity_fallback': True
                },
                provenance=state.provenance + [f"identity_fallback_{self.name}"]
            )
        
        data = state.data.flatten()
        compressed = np.dot(self.weights, data) + self.bias
        
        # Reshape to appropriate dimensions
        target_dim = int(len(data) * self.compression_ratio)
        compressed_data = compressed.reshape(-1)
        
        return LevelState(
            level=self.target_level,
            data=compressed_data,
            metadata={
                **state.metadata,
                'source_level': self.source_level,
                'compression_ratio': self.compression_ratio,
                'map_name': self.name
            },
            provenance=state.provenance + [f"abstracted_via_{self.name}"]
        )
    
    def backward(self, state: LevelState) -> LevelState:
        """Decompress data using inverse transformation."""
        if not self.is_trained:
            logger.warning(f"Map {self.name} not trained for backward, returning input")
            return LevelState(
                level=state.level,
                data=state.data,
                metadata={
                    **state.metadata,
                    'warning': f"Map {self.name} not trained, identity fallback applied",
                    'identity_fallback': True
                },
                provenance=state.provenance + [f"identity_fallback_{self.name}"]
            )
        
        data = state.data.flatten()
        decompressed = np.dot(self.inv_weights, data) + self.inv_bias
        
        return LevelState(
            level=self.source_level,
            data=decompressed,
            metadata={
                **state.metadata,
                'target_level': self.target_level,
                'map_name': self.name
            },
            provenance=state.provenance + [f"grounded_via_{self.name}"]
        )
    
    def train(self, source_states: List[LevelState], target_states: List[LevelState]) -> None:
        """Train linear mapping using least squares."""
        if len(source_states) != len(target_states):
            raise ValueError("Source and target states must have same length")
        
        # Prepare training data
        X = np.array([s.data.flatten() for s in source_states])
        Y = np.array([s.data.flatten() for s in target_states])
        
        # Solve for weights and bias
        ones = np.ones((X.shape[0], 1))
        X_aug = np.hstack([X, ones])
        
        # Least squares solution
        solution, _, _, _ = np.linalg.lstsq(X_aug, Y, rcond=None)
        self.weights = solution[:-1, :].T  # Transpose for correct orientation
        self.bias = solution[-1, :]
        
        # Compute pseudo-inverse for backward mapping
        Y_aug = np.hstack([Y, ones])
        inv_solution, _, _, _ = np.linalg.lstsq(Y_aug, X, rcond=None)
        self.inv_weights = inv_solution[:-1, :].T
        self.inv_bias = inv_solution[-1, :]
        
        self.is_trained = True
        super().train(source_states, target_states)
        
        logger.info(f"Trained linear map {self.name} with {len(source_states)} examples")


class SymbolicAbstractionMap(CrossLevelMap):
    """Symbolic abstraction map using pattern matching and rule-based transformation."""
    
    def __init__(self, source_level: int, target_level: int, symbol_rules: Dict[str, Any]):
        super().__init__(source_level, target_level, f"symbolic_{source_level}_to_{target_level}")
        self.symbol_rules = symbol_rules
        self.pattern_cache: Dict[str, Any] = {}
    
    def forward(self, state: LevelState) -> LevelState:
        """Apply symbolic rules to create abstraction."""
        data = state.data
        
        # Convert data to symbolic representation
        if isinstance(data, np.ndarray):
            symbolic_data = self._array_to_symbols(data)
        else:
            symbolic_data = str(data)
        
        # Apply transformation rules
        transformed = self._apply_rules(symbolic_data)
        
        # Convert back to numerical representation
        if isinstance(transformed, str):
            result_data = self._symbols_to_array(transformed, data.shape if hasattr(data, 'shape') else (len(transformed),))
        else:
            result_data = np.array(transformed)
        
        return LevelState(
            level=self.target_level,
            data=result_data,
            metadata={
                **state.metadata,
                'transformation_rules': list(self.symbol_rules.keys()),
                'map_name': self.name
            },
            provenance=state.provenance + [f"symbolic_abstracted_via_{self.name}"]
        )
    
    def backward(self, state: LevelState) -> LevelState:
        """Apply inverse symbolic rules for grounding."""
        data = state.data
        symbolic_data = self._array_to_symbols(data)
        
        # Apply inverse rules (simplified - would need proper rule inversion)
        grounded = self._apply_inverse_rules(symbolic_data)
        result_data = self._symbols_to_array(grounded, data.shape if hasattr(data, 'shape') else (len(grounded),))
        
        return LevelState(
            level=self.source_level,
            data=result_data,
            metadata={
                **state.metadata,
                'inverse_transformation': True,
                'map_name': self.name
            },
            provenance=state.provenance + [f"symbolic_grounded_via_{self.name}"]
        )
    
    def _array_to_symbols(self, data: np.ndarray) -> str:
        """Convert numerical array to symbolic representation."""
        # Simple quantization-based symbolization
        if len(data.shape) > 1:
            flattened = data.flatten()
        else:
            flattened = data
        
        # Discretize into symbols
        quantized = np.digitize(flattened, bins=np.linspace(flattened.min(), flattened.max(), 10))
        symbols = ''.join([chr(ord('A') + int(x)) for x in quantized])
        
        return symbols
    
    def _symbols_to_array(self, symbols: str, shape: Tuple[int, ...]) -> np.ndarray:
        """Convert symbolic representation back to numerical array."""
        # Reverse the symbolization
        numerical = [ord(c) - ord('A') for c in symbols]
        return np.array(numerical).reshape(shape)
    
    def _apply_rules(self, symbols: str) -> str:
        """Apply transformation rules to symbols."""
        result = symbols
        for pattern, replacement in self.symbol_rules.items():
            result = result.replace(pattern, replacement)
        return result
    
    def _apply_inverse_rules(self, symbols: str) -> str:
        """Apply inverse transformation rules."""
        # Simplified inverse - would need proper rule inversion
        result = symbols
        for replacement, pattern in self.symbol_rules.items():
            result = result.replace(replacement, pattern)
        return result


class LevelManager:
    """Manages hierarchical abstraction levels."""
    
    def __init__(self, max_levels: int = 5):
        self.max_levels = max_levels
        self.levels: Dict[int, LevelState] = {}
        self.level_configs: Dict[int, Dict[str, Any]] = {}
        self.level_dependencies: Dict[int, List[int]] = {}
        
        # Initialize default level configurations
        for level in range(max_levels):
            self.level_configs[level] = {
                'name': f'level_{level}',
                'description': f'Abstraction level {level}',
                'data_type': 'numerical',
                'compression_ratio': 0.8 ** level,
                'active': True
            }
            self.level_dependencies[level] = [level - 1] if level > 0 else []
    
    def create_level(self, level: int, initial_data: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> LevelState:
        """Create a new abstraction level with initial data."""
        if level >= self.max_levels:
            raise ValueError(f"Level {level} exceeds max levels {self.max_levels}")
        
        state = LevelState(
            level=level,
            data=initial_data,
            metadata=metadata or self.level_configs[level].copy(),
            provenance=[f"created_level_{level}"]
        )
        
        self.levels[level] = state
        logger.info(f"Created level {level} with data shape {initial_data.shape}")
        return state
    
    def get_level(self, level: int) -> Optional[LevelState]:
        """Get the state of a specific level."""
        return self.levels.get(level)
    
    def update_level(self, level: int, data: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> LevelState:
        """Update the state of a specific level."""
        if level not in self.levels:
            raise ValueError(f"Level {level} not found")
        
        old_state = self.levels[level]
        new_state = LevelState(
            level=level,
            data=data,
            metadata=metadata or old_state.metadata,
            provenance=old_state.provenance + [f"updated_level_{level}"]
        )
        
        self.levels[level] = new_state
        return new_state
    
    def get_active_levels(self) -> List[int]:
        """Get list of currently active levels."""
        return [level for level, config in self.level_configs.items() if config.get('active', True)]
    
    def set_level_config(self, level: int, config: Dict[str, Any]) -> None:
        """Update configuration for a specific level."""
        self.level_configs[level].update(config)
    
    def get_level_hierarchy(self) -> Dict[int, List[int]]:
        """Get the hierarchical dependencies between levels."""
        return self.level_dependencies.copy()


class CrossLevelMapManager:
    """Manages cross-level mappings between abstraction levels."""
    
    def __init__(self):
        self.up_maps: Dict[int, CrossLevelMap] = {}  # E_ℓ: z_{ℓ-1} → z_ℓ
        self.down_maps: Dict[int, CrossLevelMap] = {}  # D_ℓ: z_ℓ → z_{ℓ-1}
        self.map_registry: Dict[str, CrossLevelMap] = {}
    
    def register_up_map(self, target_level: int, map_obj: CrossLevelMap) -> None:
        """Register an upward abstraction map."""
        self.up_maps[target_level] = map_obj
        self.map_registry[map_obj.name] = map_obj
        logger.info(f"Registered up map for level {target_level}: {map_obj.name}")
    
    def register_down_map(self, target_level: int, map_obj: CrossLevelMap) -> None:
        """Register a downward grounding map."""
        self.down_maps[target_level] = map_obj
        self.map_registry[map_obj.name] = map_obj
        logger.info(f"Registered down map for level {target_level}: {map_obj.name}")
    
    def get_up_map(self, target_level: int) -> Optional[CrossLevelMap]:
        """Get upward map to target level."""
        return self.up_maps.get(target_level)
    
    def get_down_map(self, target_level: int) -> Optional[CrossLevelMap]:
        """Get downward map from target level."""
        return self.down_maps.get(target_level)
    
    def abstract_up(self, source_state: LevelState) -> Optional[LevelState]:
        """Abstract state to next higher level."""
        target_level = source_state.level + 1
        up_map = self.get_up_map(target_level)
        
        if up_map is None:
            logger.warning(f"No up map found for level {target_level}")
            return None
        
        return up_map.forward(source_state)
    
    def ground_down(self, target_state: LevelState) -> Optional[LevelState]:
        """Ground state to next lower level."""
        down_map = self.get_down_map(target_state.level)
        
        if down_map is None:
            logger.warning(f"No down map found for level {target_state.level}")
            return None
        
        return down_map.backward(target_state)
    
    def train_maps(self, training_data: Dict[int, List[LevelState]]) -> None:
        """Train all registered maps with provided data."""
        for target_level, up_map in self.up_maps.items():
            source_level = target_level - 1
            if source_level in training_data and target_level in training_data:
                source_states = training_data[source_level]
                target_states = training_data[target_level]
                up_map.train(source_states, target_states)
        
        for target_level, down_map in self.down_maps.items():
            source_level = target_level - 1
            if source_level in training_data and target_level in training_data:
                source_states = training_data[source_level]
                target_states = training_data[target_level]
                down_map.train(target_states, source_states)  # Reverse order for down maps


class HierarchicalAbstraction:
    """
    Main hierarchical abstraction system that integrates level management
    and cross-level mappings.
    """
    
    def __init__(self, max_levels: int = 5):
        self.level_manager = LevelManager(max_levels)
        self.map_manager = CrossLevelMapManager()
        self.abstraction_history: List[Dict[str, Any]] = []
        
        # Initialize default maps for each level
        self._initialize_default_maps()
    
    def _initialize_default_maps(self) -> None:
        """Initialize default linear abstraction maps for all levels."""
        for level in range(1, self.level_manager.max_levels):
            # Create up map (abstraction)
            up_map = LinearAbstractionMap(
                source_level=level - 1,
                target_level=level,
                compression_ratio=0.8
            )
            self.map_manager.register_up_map(level, up_map)
            
            # Create down map (grounding)
            down_map = LinearAbstractionMap(
                source_level=level,
                target_level=level - 1,
                compression_ratio=1.25  # Inverse of up map
            )
            self.map_manager.register_down_map(level, down_map)
    
    def add_ground_level(self, data: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> LevelState:
        """Add ground truth level (level 0)."""
        return self.level_manager.create_level(0, data, metadata)
    
    def abstract_to_level(self, source_level: int, target_level: int) -> Optional[LevelState]:
        """Abstract from source level to target level."""
        if source_level >= target_level:
            raise ValueError(f"Target level {target_level} must be higher than source level {source_level}")
        
        current_state = self.level_manager.get_level(source_level)
        if current_state is None:
            logger.error(f"Source level {source_level} not found")
            return None
        
        # Apply successive up maps
        for level in range(source_level + 1, target_level + 1):
            current_state = self.map_manager.abstract_up(current_state)
            if current_state is None:
                logger.error(f"Failed to abstract to level {level}")
                return None
            
            # Store intermediate result
            self.level_manager.levels[level] = current_state
        
        # Record abstraction operation
        self.abstraction_history.append({
            'timestamp': time.time(),
            'operation': 'abstract',
            'source_level': source_level,
            'target_level': target_level,
            'success': True
        })
        
        return current_state
    
    def ground_to_level(self, source_level: int, target_level: int) -> Optional[LevelState]:
        """Ground from source level to target level."""
        if source_level <= target_level:
            raise ValueError(f"Target level {target_level} must be lower than source level {source_level}")
        
        current_state = self.level_manager.get_level(source_level)
        if current_state is None:
            logger.error(f"Source level {source_level} not found")
            return None
        
        # Apply successive down maps
        for level in range(source_level, target_level, -1):
            current_state = self.map_manager.ground_down(current_state)
            if current_state is None:
                logger.error(f"Failed to ground to level {level - 1}")
                return None
        
        # Record grounding operation
        self.abstraction_history.append({
            'timestamp': time.time(),
            'operation': 'ground',
            'source_level': source_level,
            'target_level': target_level,
            'success': True
        })
        
        return current_state
    
    def get_abstraction_summary(self) -> Dict[str, Any]:
        """Get summary of current abstraction state."""
        active_levels = self.level_manager.get_active_levels()
        level_states = {}
        
        for level in active_levels:
            state = self.level_manager.get_level(level)
            if state:
                level_states[level] = {
                    'data_shape': state.data.shape if hasattr(state.data, 'shape') else len(state.data),
                    'metadata': state.metadata,
                    'provenance_length': len(state.provenance),
                    'timestamp': state.timestamp
                }
        
        return {
            'active_levels': active_levels,
            'level_states': level_states,
            'abstraction_history_count': len(self.abstraction_history),
            'map_count': len(self.map_manager.map_registry),
            'max_levels': self.level_manager.max_levels
        }

    async def initialize(self) -> Dict[str, Any]:
        """Initialize abstraction framework (async for compatibility)."""
        summary = self.get_abstraction_summary()
        logger.info("Hierarchical Abstraction initialized")
        return summary

    async def shutdown(self) -> None:
        """Shutdown abstraction framework."""
        logger.info("Hierarchical Abstraction shutdown")

    async def cleanup(self) -> None:
        """Cleanup abstraction framework resources."""
        await self.shutdown()
