"""
Abstraction System for CNHAAI

This module provides the core abstraction infrastructure including:
- Abstraction: A first-class computational entity representing a simplified model
- AbstractionLayer: Manages multiple abstractions with hierarchy support
- AbstractionType: Enum for different abstraction types
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from uuid import uuid4


class AbstractionType(Enum):
    """Types of abstractions supported in CNHAAI."""

    DESCRIPTIVE = auto()  # Describes what is (observational)
    MECHANISTIC = auto()  # Describes how it works (causal)
    NORMATIVE = auto()  # Describes what should be (prescriptive)
    COMPARATIVE = auto()  # Describes relationships between entities


@dataclass
class Abstraction:
    """
    A first-class computational entity representing a simplified model.

    An abstraction captures essential features while ignoring irrelevant details,
    enabling efficient reasoning and decision-making.

    Attributes:
        type: The type of abstraction (descriptive, mechanistic, normative, comparative)
        evidence: Set of evidence supporting this abstraction
        scope: Contexts where this abstraction is applicable
        validity: Validity constraints and boundaries
        content: The semantic content of the abstraction
        id: Unique identifier for this abstraction
        timestamp: When this abstraction was created
        parent_id: ID of the parent abstraction (if hierarchical)
        children_ids: IDs of child abstractions (if hierarchical)
        metadata: Additional metadata for extensibility
    """

    type: AbstractionType
    evidence: Set[str]
    scope: Set[str]
    validity: Dict[str, Any]
    content: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert abstraction to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.name,
            "evidence": list(self.evidence),
            "scope": list(self.scope),
            "validity": self.validity,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Abstraction":
        """Create abstraction from dictionary representation."""
        return cls(
            id=data.get("id", str(uuid4())),
            type=AbstractionType[data.get("type", "DESCRIPTIVE")],
            evidence=set(data.get("evidence", [])),
            scope=set(data.get("scope", [])),
            validity=data.get("validity", {}),
            content=data.get("content", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.utcnow()
            ),
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            metadata=data.get("metadata", {}),
        )

    def is_valid_for_context(self, context: str) -> bool:
        """Check if abstraction is valid for the given context."""
        return context in self.scope

    def is_valid_for_scope(self, scope: Set[str]) -> bool:
        """Check if abstraction is valid for the given scope."""
        return bool(scope.intersection(self.scope))


@dataclass
class AbstractionLayer:
    """
    Manages multiple abstractions with hierarchy support.

    An abstraction layer provides organization and lookup capabilities
    for abstractions, supporting hierarchical relationships and
    efficient querying.

    Attributes:
        abstractions: Dictionary of abstractions by ID
        by_type: Dictionary mapping types to sets of abstraction IDs
        by_scope: Dictionary mapping scopes to sets of abstraction IDs
        root_ids: IDs of root abstractions (no parent)
        max_levels: Maximum hierarchy depth
    """

    abstractions: Dict[str, Abstraction] = field(default_factory=dict)
    by_type: Dict[AbstractionType, Set[str]] = field(default_factory=dict)
    by_scope: Dict[str, Set[str]] = field(default_factory=dict)
    root_ids: Set[str] = field(default_factory=set)
    max_levels: int = 3

    def add(self, abstraction: Abstraction) -> bool:
        """
        Add an abstraction to the layer.

        Args:
            abstraction: The abstraction to add

        Returns:
            True if added successfully, False if already exists
        """
        if abstraction.id in self.abstractions:
            return False

        self.abstractions[abstraction.id] = abstraction

        # Index by type
        if abstraction.type not in self.by_type:
            self.by_type[abstraction.type] = set()
        self.by_type[abstraction.type].add(abstraction.id)

        # Index by scope
        for scope in abstraction.scope:
            if scope not in self.by_scope:
                self.by_scope[scope] = set()
            self.by_scope[scope].add(abstraction.id)

        # Handle hierarchy
        if abstraction.parent_id is None:
            self.root_ids.add(abstraction.id)
        else:
            self.root_ids.discard(abstraction.id)
            if abstraction.parent_id in self.abstractions:
                self.abstractions[abstraction.parent_id].children_ids.append(abstraction.id)

        return True

    def get(self, abstraction_id: str) -> Optional[Abstraction]:
        """Get an abstraction by ID."""
        return self.abstractions.get(abstraction_id)

    def get_by_type(self, abstraction_type: AbstractionType) -> List[Abstraction]:
        """Get all abstractions of a given type."""
        ids = self.by_type.get(abstraction_type, set())
        return [self.abstractions[id_] for id_ in ids if id_ in self.abstractions]

    def get_by_scope(self, scope: str) -> List[Abstraction]:
        """Get all abstractions valid for a given scope."""
        ids = self.by_scope.get(scope, set())
        return [self.abstractions[id_] for id_ in ids if id_ in self.abstractions]

    def get_roots(self) -> List[Abstraction]:
        """Get all root abstractions."""
        return [self.abstractions[id_] for id_ in self.root_ids if id_ in self.abstractions]

    def get_children(self, abstraction_id: str) -> List[Abstraction]:
        """Get all direct children of an abstraction."""
        abstraction = self.abstractions.get(abstraction_id)
        if not abstraction:
            return []
        return [
            self.abstractions[id_] for id_ in abstraction.children_ids if id_ in self.abstractions
        ]

    def get_descendants(self, abstraction_id: str) -> List[Abstraction]:
        """Get all descendants of an abstraction recursively."""
        result = []
        children = self.get_children(abstraction_id)
        for child in children:
            result.append(child)
            result.extend(self.get_descendants(child.id))
        return result

    def get_ancestors(self, abstraction_id: str) -> List[Abstraction]:
        """Get all ancestors of an abstraction recursively."""
        result = []
        abstraction = self.abstractions.get(abstraction_id)
        if not abstraction or not abstraction.parent_id:
            return result
        parent = self.abstractions.get(abstraction.parent_id)
        if parent:
            result.append(parent)
            result.extend(self.get_ancestors(parent.id))
        return result

    def validate_hierarchy(self) -> bool:
        """
        Validate the abstraction hierarchy.

        Returns:
            True if hierarchy is valid, False otherwise
        """
        for abstraction in self.abstractions.values():
            # Check parent exists
            if abstraction.parent_id and abstraction.parent_id not in self.abstractions:
                return False

            # Check hierarchy depth
            depth = 0
            current = abstraction
            while current.parent_id and current.parent_id in self.abstractions:
                depth += 1
                current = self.abstractions[current.parent_id]
                if depth > self.max_levels:
                    return False

        return True

    def create_abstraction(
        self,
        type: AbstractionType,
        evidence: Set[str],
        scope: Set[str],
        validity: Dict[str, Any],
        content: Dict[str, Any],
        parent_id: Optional[str] = None,
    ) -> Abstraction:
        """
        Create and add a new abstraction.

        Args:
            type: The type of abstraction
            evidence: Evidence supporting this abstraction
            scope: Contexts where applicable
            validity: Validity constraints
            content: Semantic content
            parent_id: Optional parent abstraction ID

        Returns:
            The created abstraction
        """
        abstraction = Abstraction(
            type=type,
            evidence=evidence,
            scope=scope,
            validity=validity,
            content=content,
            parent_id=parent_id,
        )
        self.add(abstraction)
        return abstraction

    def find_common_abstractions(self, scope1: str, scope2: str) -> List[Abstraction]:
        """Find abstractions valid for both scopes."""
        ids1 = self.by_scope.get(scope1, set())
        ids2 = self.by_scope.get(scope2, set())
        common_ids = ids1.intersection(ids2)
        return [self.abstractions[id_] for id_ in common_ids if id_ in self.abstractions]
