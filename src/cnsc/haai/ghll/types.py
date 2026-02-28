"""
GHLL Type System

This module provides the type system for GHLL including:
- GHLLType: Base class for all types
- PrimitiveType: bool, int, float, string, symbol
- CompositeType: struct, union, sequence
- TypeRegistry: Type catalog and validation
- TypeChecker: Type checking and inference

References:
- cnsc-haai/spec/ghll/03_Type_System.md
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4
import json


class TypeCategory(Enum):
    """Categories of types in GHLL."""

    PRIMITIVE = auto()
    COMPOSITE = auto()
    FUNCTION = auto()
    TYPE_VARIABLE = auto()


@dataclass
class TypeOrigin:
    """
    Information about where a type was defined.

    Attributes:
        source: Source file or module
        line: Line number
        column: Column number
        span: Text span of the definition
    """

    source: str = ""
    line: int = 0
    column: int = 0
    span: Tuple[int, int] = (0, 0)  # (start, end)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": self.source,
            "line": self.line,
            "column": self.column,
            "span": list(self.span),
        }


@dataclass
class GHLLType:
    """
    Base class for all GHLL types.

    Attributes:
        type_id: Unique identifier for this type
        name: Type name
        category: Type category
        origin: Where the type was defined
        metadata: Additional type information
    """

    type_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "unknown"
    category: TypeCategory = TypeCategory.PRIMITIVE
    origin: Optional[TypeOrigin] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "type_id": self.type_id,
            "name": self.name,
            "category": self.category.name,
            "origin": self.origin.to_dict() if self.origin else None,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        """Return type name as string representation."""
        return self.name

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"GHLLType({self.name})"

    def is_primitive(self) -> bool:
        """Check if this is a primitive type."""
        return self.category == TypeCategory.PRIMITIVE

    def is_composite(self) -> bool:
        """Check if this is a composite type."""
        return self.category == TypeCategory.COMPOSITE

    def is_function(self) -> bool:
        """Check if this is a function type."""
        return self.category == TypeCategory.FUNCTION

    def is_compatible_with(self, other: "GHLLType") -> bool:
        """
        Check if this type is compatible with another.

        By default, types are only compatible if they're the same.
        Override in subclasses for more complex compatibility rules.

        Args:
            other: The type to check compatibility with

        Returns:
            True if types are compatible
        """
        return self.type_id == other.type_id


class PrimitiveType(GHLLType):
    """
    Primitive type in GHLL.

    Primitive types are basic types like bool, int, float, string, symbol.
    """

    def __init__(
        self, name: str, type_id: Optional[str] = None, origin: Optional[TypeOrigin] = None
    ):
        super().__init__(
            type_id=type_id or f"primitive_{name}",
            name=name,
            category=TypeCategory.PRIMITIVE,
            origin=origin,
        )

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Primitive types are compatible if names match."""
        if isinstance(other, PrimitiveType):
            return self.name == other.name
        return False


class BoolType(PrimitiveType):
    """Boolean type."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("bool", origin=origin)


class IntType(PrimitiveType):
    """Integer type."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("int", origin=origin)


class FloatType(PrimitiveType):
    """Floating point type."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("float", origin=origin)


class StringType(PrimitiveType):
    """String type."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("string", origin=origin)


class SymbolType(PrimitiveType):
    """Symbol type (atomic identifier)."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("symbol", origin=origin)


class NoneType(PrimitiveType):
    """None/null type."""

    def __init__(self, origin: Optional[TypeOrigin] = None):
        super().__init__("none", origin=origin)


class CompositeType(GHLLType):
    """
    Composite type in GHLL.

    Composite types are constructed from other types.
    """

    def __init__(
        self,
        name: str,
        element_types: List[GHLLType],
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
    ):
        super().__init__(
            type_id=type_id or f"composite_{name}_{len(element_types)}",
            name=name,
            category=TypeCategory.COMPOSITE,
            origin=origin,
        )
        self.element_types = element_types


class StructType(CompositeType):
    """
    Struct type (named fields).

    Attributes:
        fields: Dictionary mapping field names to types
    """

    def __init__(
        self,
        fields: Dict[str, GHLLType],
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
        name: Optional[str] = None,
    ):
        # Use provided name or create one from field names
        if name is None:
            field_names = list(fields.keys())
            name = f"struct_{'_'.join(field_names[:3])}" + ("_etc" if len(field_names) > 3 else "")

        super().__init__(
            name=name, element_types=list(fields.values()), type_id=type_id, origin=origin
        )
        self.fields = fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["fields"] = {k: v.to_dict() for k, v in self.fields.items()}
        return result

    def get_field(self, field_name: str) -> Optional[GHLLType]:
        """Get the type of a field."""
        return self.fields.get(field_name)

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Structs are compatible if they have compatible fields."""
        if not isinstance(other, StructType):
            return False

        if set(self.fields.keys()) != set(other.fields.keys()):
            return False

        for field_name in self.fields:
            if not self.fields[field_name].is_compatible_with(other.fields[field_name]):
                return False

        return True


class UnionType(CompositeType):
    """
    Union type (one of many types).

    Attributes:
        variants: List of possible types
    """

    def __init__(
        self,
        variants: List[GHLLType],
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
        name: Optional[str] = None,
    ):
        # Use provided name or create one from variant count
        if name is None:
            name = f"union_{len(variants)}"
        super().__init__(name=name, element_types=variants, type_id=type_id, origin=origin)
        self.variants = variants

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["variants"] = [v.to_dict() for v in self.variants]
        return result

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Union is compatible if other matches any variant."""
        if isinstance(other, UnionType):
            # Both unions - check if all variants are compatible
            return all(
                any(v1.is_compatible_with(v2) for v2 in other.variants) for v1 in self.variants
            )

        # Check if other matches any variant
        return any(variant.is_compatible_with(other) for variant in self.variants)


class SequenceType(CompositeType):
    """
    Sequence type (ordered collection of same-type elements).

    Attributes:
        element_type: Type of elements in the sequence
    """

    def __init__(
        self,
        element_type: GHLLType,
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
    ):
        super().__init__(
            name=f"seq_{element_type.name}",
            element_types=[element_type],
            type_id=type_id,
            origin=origin,
        )
        self.element_type = element_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["element_type"] = self.element_type.to_dict()
        return result

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Sequences are compatible if element types are compatible."""
        if isinstance(other, SequenceType):
            return self.element_type.is_compatible_with(other.element_type)
        return False


class OptionalType(CompositeType):
    """
    Optional type (may be None).

    Attributes:
        inner_type: The wrapped type
    """

    def __init__(
        self,
        inner_type: GHLLType,
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
    ):
        super().__init__(
            name=f"optional_{inner_type.name}",
            element_types=[inner_type],
            type_id=type_id,
            origin=origin,
        )
        self.inner_type = inner_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["inner_type"] = self.inner_type.to_dict()
        return result

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Optional is compatible if inner types match or other is None."""
        if isinstance(other, NoneType):
            return True
        if isinstance(other, OptionalType):
            return self.inner_type.is_compatible_with(other.inner_type)
        return self.inner_type.is_compatible_with(other)


class FunctionType(GHLLType):
    """
    Function type.

    Attributes:
        param_types: Types of parameters
        return_type: Return type
    """

    def __init__(
        self,
        param_types: List[GHLLType],
        return_type: GHLLType,
        type_id: Optional[str] = None,
        origin: Optional[TypeOrigin] = None,
    ):
        super().__init__(
            type_id=type_id or f"func_{len(param_types)}_{return_type.name}",
            name=f"fn({','.join(p.name for p in param_types)}) -> {return_type.name}",
            category=TypeCategory.FUNCTION,
            origin=origin,
        )
        self.param_types = param_types
        self.return_type = return_type
        self.element_types = param_types + [return_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["param_types"] = [p.to_dict() for p in self.param_types]
        result["return_type"] = self.return_type.to_dict()
        return result

    def is_compatible_with(self, other: GHLLType) -> bool:
        """Functions are compatible if signatures match."""
        if not isinstance(other, FunctionType):
            return False

        if len(self.param_types) != len(other.param_types):
            return False

        # Covariant return type
        if not self.return_type.is_compatible_with(other.return_type):
            return False

        # Contravariant parameter types
        for p1, p2 in zip(self.param_types, other.param_types):
            if not p2.is_compatible_with(p1):
                return False

        return True


@dataclass
class TypeRegistry:
    """
    Registry of known types.

    The type registry manages all types in a GHLL program,
    providing lookup and type resolution.

    Attributes:
        types: Dictionary of types by type_id
        by_name: Dictionary of types by name
        primitives: Set of primitive type names
    """

    types: Dict[str, GHLLType] = field(default_factory=dict)
    by_name: Dict[str, GHLLType] = field(default_factory=dict)
    primitives: Set[str] = field(default_factory=set)

    def __post_init__(self):
        """Initialize with primitive types."""
        self._register_primitives()

    def _register_primitives(self) -> None:
        """Register all primitive types."""
        primitive_types = [
            BoolType(),
            IntType(),
            FloatType(),
            StringType(),
            SymbolType(),
            NoneType(),
        ]

        for prim in primitive_types:
            self.register_type(prim)
            self.primitives.add(prim.name)

    def register_type(self, type_obj: GHLLType) -> bool:
        """
        Register a type.

        Args:
            type_obj: The type to register

        Returns:
            True if registered successfully
        """
        if type_obj.type_id in self.types:
            return False

        self.types[type_obj.type_id] = type_obj
        self.by_name[type_obj.name] = type_obj
        return True

    def get_type(self, type_id: str) -> Optional[GHLLType]:
        """
        Get a type by ID.

        Args:
            type_id: The type ID to look up

        Returns:
            The type if found, None otherwise
        """
        return self.types.get(type_id)

    def lookup(self, name: str) -> Optional[GHLLType]:
        """
        Look up a type by name.

        Args:
            name: The type name to look up

        Returns:
            The type if found, None otherwise
        """
        return self.by_name.get(name)

    def is_primitive(self, name: str) -> bool:
        """Check if a type name is a primitive."""
        return name in self.primitives

    def create_struct(
        self, name: str, fields: Dict[str, str], origin: Optional[TypeOrigin] = None
    ) -> StructType:
        """
        Create and register a struct type.

        Args:
            name: Name for the struct
            fields: Dictionary mapping field names to type names
            origin: Source location

        Returns:
            The created struct type
        """
        field_types = {}
        for field_name, type_name in fields.items():
            type_obj = self.lookup(type_name)
            if type_obj is None:
                # Create type variable for forward reference
                type_obj = TypeVariable(type_name)
            field_types[field_name] = type_obj

        struct = StructType(fields=field_types, origin=origin, name=name)
        self.register_type(struct)
        return struct

    def create_union(
        self, name: str, variants: List[str], origin: Optional[TypeOrigin] = None
    ) -> UnionType:
        """
        Create and register a union type.

        Args:
            name: Name for the union
            variants: List of variant type names
            origin: Source location

        Returns:
            The created union type
        """
        variant_types = []
        for variant_name in variants:
            type_obj = self.lookup(variant_name)
            if type_obj is None:
                type_obj = TypeVariable(variant_name)
            variant_types.append(type_obj)

        union = UnionType(variants=variant_types, origin=origin, name=name)
        self.register_type(union)
        return union

    def create_sequence(
        self, element_type_name: str, origin: Optional[TypeOrigin] = None
    ) -> SequenceType:
        """
        Create and register a sequence type.

        Args:
            element_type_name: Name of element type
            origin: Source location

        Returns:
            The created sequence type
        """
        element_type = self.lookup(element_type_name)
        if element_type is None:
            element_type = TypeVariable(element_type_name)

        seq = SequenceType(element_type=element_type, origin=origin)
        self.register_type(seq)
        return seq

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "types": {tid: t.to_dict() for tid, t in self.types.items()},
            "primitives": list(self.primitives),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TypeRegistry":
        """Create from dictionary (simplified - full implementation would reconstruct types)."""
        return cls()


class TypeVariable(GHLLType):
    """
    Type variable for type inference.

    Type variables represent unknown types that will be resolved
    during type checking or inference.

    Attributes:
        bound: Optional bound type
        constraints: List of type constraints
    """

    def __init__(
        self, name: str = "T", bound: Optional[GHLLType] = None, origin: Optional[TypeOrigin] = None
    ):
        super().__init__(
            type_id=f"typevar_{uuid4().hex[:8]}",
            name=name,
            category=TypeCategory.TYPE_VARIABLE,
            origin=origin,
        )
        self.bound = bound
        self.constraints: List[GHLLType] = []
        self._resolved: Optional[GHLLType] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = super().to_dict()
        result["bound"] = self.bound.to_dict() if self.bound else None
        result["constraints"] = [c.to_dict() for c in self.constraints]
        result["resolved"] = self._resolved.to_dict() if self._resolved else None
        return result

    def is_resolved(self) -> bool:
        """Check if this variable is resolved."""
        return self._resolved is not None

    def resolve(self, type_obj: GHLLType) -> bool:
        """
        Resolve this variable to a concrete type.

        Args:
            type_obj: The type to resolve to

        Returns:
            True if resolved successfully
        """
        if self._resolved is not None:
            return False

        if self.bound and not type_obj.is_compatible_with(self.bound):
            return False

        # Check constraints
        for constraint in self.constraints:
            if not type_obj.is_compatible_with(constraint):
                return False

        self._resolved = type_obj
        return True

    def get_resolved(self) -> Optional[GHLLType]:
        """Get the resolved type, if any."""
        return self._resolved


class TypeChecker:
    """
    Type checker for GHLL.

    The type checker performs type checking and inference
    on GHLL programs.

    Attributes:
        registry: Type registry to use
        errors: List of type errors
        warnings: List of type warnings
    """

    def __init__(self, registry: Optional[TypeRegistry] = None):
        """Initialize the type checker."""
        self.registry = registry or TypeRegistry()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_type(self, expr_type: GHLLType, expected_type: GHLLType) -> bool:
        """
        Check that an expression has the expected type.

        Args:
            expr_type: The expression type
            expected_type: The expected type

        Returns:
            True if types are compatible
        """
        if not expr_type.is_compatible_with(expected_type):
            self.errors.append(
                f"Type mismatch: expected {expected_type.name}, got {expr_type.name}"
            )
            return False
        return True

    def infer_type(self, expr: Dict[str, Any], context: Dict[str, GHLLType]) -> Optional[GHLLType]:
        """
        Infer the type of an expression.

        Args:
            expr: The expression to infer
            context: Variable type context

        Returns:
            Inferred type, or None if inference failed
        """
        expr_type = expr.get("type")
        if expr_type:
            type_obj = self.registry.lookup(expr_type)
            if type_obj:
                return type_obj

        # Look up in context
        var_name = expr.get("var")
        if var_name and var_name in context:
            return context[var_name]

        self.errors.append(f"Cannot infer type for expression: {expr}")
        return None

    def unify_types(self, type1: GHLLType, type2: GHLLType) -> Optional[GHLLType]:
        """
        Unify two types, finding their most general common type.

        Args:
            type1: First type
            type2: Second type

        Returns:
            Unified type, or None if unification failed
        """
        # If types are compatible, return either
        if type1.is_compatible_with(type2):
            return type1
        if type2.is_compatible_with(type1):
            return type2

        # Handle type variables
        if isinstance(type1, TypeVariable):
            if type1.resolve(type2):
                return type2
            self.errors.append(f"Cannot unify {type1.name} with {type2.name}")
            return None

        if isinstance(type2, TypeVariable):
            if type2.resolve(type1):
                return type1
            self.errors.append(f"Cannot unify {type1.name} with {type2.name}")
            return None

        self.errors.append(f"Type mismatch: {type1.name} vs {type2.name}")
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get type checker statistics."""
        return {
            "registered_types": len(self.registry.types),
            "primitives": len(self.registry.primitives),
            "errors": len(self.errors),
            "warnings": len(self.warnings),
        }

    def clear_errors(self) -> None:
        """Clear all errors and warnings."""
        self.errors.clear()
        self.warnings.clear()
