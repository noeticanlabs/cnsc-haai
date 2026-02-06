"""
Unit tests for GHLL Type System.

Tests cover:
- Primitive types (bool, int, float, string, symbol, none)
- Composite types (struct, union, sequence, optional)
- Function types
- Type variables
- Type registry
- Type checking and inference
"""

import unittest

from cnsc.haai.ghll.types import (
    GHLLType,
    PrimitiveType,
    BoolType,
    IntType,
    FloatType,
    StringType,
    SymbolType,
    NoneType,
    CompositeType,
    StructType,
    UnionType,
    SequenceType,
    OptionalType,
    FunctionType,
    TypeRegistry,
    TypeVariable,
    TypeChecker,
    TypeCategory,
)


class TestPrimitiveTypes(unittest.TestCase):
    """Tests for primitive types."""
    
    def test_bool_type(self):
        """Test boolean type creation."""
        bool_type = BoolType()
        
        assert bool_type.name == "bool"
        assert bool_type.category == TypeCategory.PRIMITIVE
        assert bool_type.is_primitive() is True
    
    def test_int_type(self):
        """Test integer type creation."""
        int_type = IntType()
        
        assert int_type.name == "int"
        assert int_type.is_primitive() is True
    
    def test_float_type(self):
        """Test float type creation."""
        float_type = FloatType()
        
        assert float_type.name == "float"
        assert float_type.is_primitive() is True
    
    def test_string_type(self):
        """Test string type creation."""
        string_type = StringType()
        
        assert string_type.name == "string"
        assert string_type.is_primitive() is True
    
    def test_symbol_type(self):
        """Test symbol type creation."""
        symbol_type = SymbolType()
        
        assert symbol_type.name == "symbol"
        assert symbol_type.is_primitive() is True
    
    def test_none_type(self):
        """Test none type creation."""
        none_type = NoneType()
        
        assert none_type.name == "none"
        assert none_type.is_primitive() is True
    
    def test_primitive_compatibility(self):
        """Test primitive type compatibility."""
        bool1 = BoolType()
        bool2 = BoolType()
        int_type = IntType()
        
        assert bool1.is_compatible_with(bool2) is True
        assert bool1.is_compatible_with(int_type) is False
    
    def test_primitive_serialization(self):
        """Test primitive type serialization."""
        int_type = IntType()
        
        data = int_type.to_dict()
        
        assert data["name"] == "int"
        assert data["category"] == "PRIMITIVE"


class TestStructType(unittest.TestCase):
    """Tests for struct type."""
    
    def test_struct_creation(self):
        """Test creating a struct type."""
        fields = {
            "x": IntType(),
            "y": IntType(),
        }
        
        struct = StructType(fields=fields)
        
        assert "x" in struct.fields
        assert "y" in struct.fields
        assert struct.fields["x"].name == "int"
        assert struct.category == TypeCategory.COMPOSITE
    
    def test_get_field(self):
        """Test getting a field from struct."""
        fields = {
            "name": StringType(),
            "age": IntType(),
        }
        
        struct = StructType(fields=fields)
        
        assert struct.get_field("name").name == "string"
        assert struct.get_field("age").name == "int"
        assert struct.get_field("nonexistent") is None
    
    def test_struct_compatibility(self):
        """Test struct type compatibility."""
        fields1 = {
            "x": IntType(),
            "y": IntType(),
        }
        fields2 = {
            "x": IntType(),
            "y": IntType(),
        }
        fields3 = {
            "x": IntType(),
            "y": StringType(),  # Different type
        }
        
        struct1 = StructType(fields=fields1)
        struct2 = StructType(fields=fields2)
        struct3 = StructType(fields=fields3)
        
        assert struct1.is_compatible_with(struct2) is True
        assert struct1.is_compatible_with(struct3) is False
    
    def test_struct_incompatible_fields(self):
        """Test struct incompatibility with different fields."""
        fields1 = {"x": IntType()}
        fields2 = {"x": IntType(), "y": IntType()}
        
        struct1 = StructType(fields=fields1)
        struct2 = StructType(fields=fields2)
        
        assert struct1.is_compatible_with(struct2) is False
    
    def test_struct_serialization(self):
        """Test struct type serialization."""
        fields = {"value": IntType()}
        struct = StructType(fields=fields)
        
        data = struct.to_dict()
        
        assert data["category"] == "COMPOSITE"
        assert "fields" in data
        assert "value" in data["fields"]


class TestUnionType(unittest.TestCase):
    """Tests for union type."""
    
    def test_union_creation(self):
        """Test creating a union type."""
        variants = [IntType(), StringType()]
        
        union = UnionType(variants=variants)
        
        assert len(union.variants) == 2
        assert union.category == TypeCategory.COMPOSITE
    
    def test_union_compatibility(self):
        """Test union type compatibility."""
        int_type = IntType()
        string_type = StringType()
        
        union1 = UnionType(variants=[int_type, string_type])
        union2 = UnionType(variants=[int_type, string_type])
        union3 = UnionType(variants=[int_type])
        
        assert union1.is_compatible_with(union2) is True
        assert union1.is_compatible_with(union3) is False  # Missing variant
    
    def test_union_with_primitive(self):
        """Test union compatibility with primitive types."""
        int_type = IntType()
        string_type = StringType()
        
        union = UnionType(variants=[int_type, string_type])
        
        assert union.is_compatible_with(int_type) is True
        assert union.is_compatible_with(string_type) is True
        assert union.is_compatible_with(BoolType()) is False


class TestSequenceType(unittest.TestCase):
    """Tests for sequence type."""
    
    def test_sequence_creation(self):
        """Test creating a sequence type."""
        element_type = IntType()
        
        seq = SequenceType(element_type=element_type)
        
        assert seq.element_type.name == "int"
        assert seq.category == TypeCategory.COMPOSITE
    
    def test_sequence_compatibility(self):
        """Test sequence type compatibility."""
        int_seq = SequenceType(element_type=IntType())
        string_seq = SequenceType(element_type=StringType())
        
        assert int_seq.is_compatible_with(int_seq) is True
        assert int_seq.is_compatible_with(string_seq) is False


class TestOptionalType(unittest.TestCase):
    """Tests for optional type."""
    
    def test_optional_creation(self):
        """Test creating an optional type."""
        inner_type = IntType()
        
        opt = OptionalType(inner_type=inner_type)
        
        assert opt.inner_type.name == "int"
        assert opt.category == TypeCategory.COMPOSITE
    
    def test_optional_compatibility(self):
        """Test optional type compatibility."""
        int_type = IntType()
        opt_int = OptionalType(inner_type=int_type)
        none_type = NoneType()
        
        # Optional is compatible with its inner type
        assert opt_int.is_compatible_with(int_type) is True
        # Optional is compatible with none
        assert opt_int.is_compatible_with(none_type) is True
        # Optional is compatible with compatible optional
        opt_string = OptionalType(inner_type=StringType())
        assert opt_int.is_compatible_with(opt_string) is False


class TestFunctionType(unittest.TestCase):
    """Tests for function type."""
    
    def test_function_creation(self):
        """Test creating a function type."""
        param_types = [IntType(), IntType()]
        return_type = IntType()
        
        func = FunctionType(param_types=param_types, return_type=return_type)
        
        assert len(func.param_types) == 2
        assert func.return_type.name == "int"
        assert func.category == TypeCategory.FUNCTION
    
    def test_function_compatibility(self):
        """Test function type compatibility (contravariant params, covariant return)."""
        int_type = IntType()
        float_type = FloatType()
        
        func1 = FunctionType(param_types=[int_type], return_type=int_type)
        func2 = FunctionType(param_types=[int_type], return_type=int_type)
        func3 = FunctionType(param_types=[float_type], return_type=int_type)  # Contravariant
        func4 = FunctionType(param_types=[int_type], return_type=float_type)  # Covariant
        
        assert func1.is_compatible_with(func2) is True
        assert func1.is_compatible_with(func3) is False  # Float not compatible with int
        assert func1.is_compatible_with(func4) is False  # Return type mismatch


class TestTypeVariable(unittest.TestCase):
    """Tests for type variables."""
    
    def test_type_variable_creation(self):
        """Test creating a type variable."""
        tv = TypeVariable(name="T")
        
        assert tv.name == "T"
        assert tv.category == TypeCategory.TYPE_VARIABLE
        assert tv.is_resolved() is False
        assert tv.get_resolved() is None
    
    def test_type_variable_resolution(self):
        """Test resolving a type variable."""
        tv = TypeVariable(name="T")
        int_type = IntType()
        
        assert tv.resolve(int_type) is True
        assert tv.is_resolved() is True
        assert tv.get_resolved().name == "int"
    
    def test_type_variable_double_resolution(self):
        """Test that a type variable can only be resolved once."""
        tv = TypeVariable(name="T")
        
        tv.resolve(IntType())
        assert tv.resolve(StringType()) is False
    
    def test_type_variable_bound(self):
        """Test type variable with bound."""
        int_type = IntType()
        tv = TypeVariable(name="T", bound=int_type)
        
        # Should resolve to compatible type
        assert tv.resolve(IntType()) is True
        # Should reject incompatible type
        tv2 = TypeVariable(name="U", bound=int_type)
        assert tv2.resolve(StringType()) is False


class TestTypeRegistry(unittest.TestCase):
    """Tests for type registry."""
    
    def test_registry_primitives(self):
        """Test that registry has primitive types."""
        registry = TypeRegistry()
        
        assert registry.lookup("bool") is not None
        assert registry.lookup("int") is not None
        assert registry.lookup("string") is not None
        assert registry.is_primitive("bool") is True
        assert registry.is_primitive("custom") is False
    
    def test_register_type(self):
        """Test registering a type."""
        registry = TypeRegistry()
        
        struct = StructType(fields={"x": IntType()})
        
        assert registry.register_type(struct) is True
        assert registry.get_type(struct.type_id) is struct
        assert registry.lookup(struct.name) is struct
        
        # Duplicate registration should fail
        assert registry.register_type(struct) is False
    
    def test_create_struct(self):
        """Test creating a struct through registry."""
        registry = TypeRegistry()
        
        struct = registry.create_struct(
            name="Point",
            fields={"x": "int", "y": "int"}
        )
        
        assert struct is not None
        assert registry.lookup("Point") is struct
        assert registry.lookup("int") is not None  # Primitive should exist
    
    def test_create_union(self):
        """Test creating a union through registry."""
        registry = TypeRegistry()
        
        union = registry.create_union(
            name="Number",
            variants=["int", "float"]
        )
        
        assert union is not None
        assert registry.lookup("Number") is not None
    
    def test_create_sequence(self):
        """Test creating a sequence through registry."""
        registry = TypeRegistry()
        
        seq = registry.create_sequence(element_type_name="int")
        
        assert seq is not None
        assert seq.element_type.name == "int"
    
    def test_registry_serialization(self):
        """Test registry serialization."""
        registry = TypeRegistry()
        
        data = registry.to_dict()
        
        assert "types" in data
        assert "primitives" in data


class TestTypeChecker(unittest.TestCase):
    """Tests for type checker."""
    
    def test_check_type_matching(self):
        """Test type checking with matching types."""
        checker = TypeChecker()
        
        assert checker.check_type(IntType(), IntType()) is True
        assert checker.check_type(IntType(), StringType()) is False
        assert len(checker.errors) == 1
    
    def test_check_type_compatibility(self):
        """Test type checking with compatible types."""
        checker = TypeChecker()
        
        # Optional int should be compatible with int
        opt_int = OptionalType(inner_type=IntType())
        assert checker.check_type(opt_int, IntType()) is True
    
    def test_infer_type(self):
        """Test type inference."""
        checker = TypeChecker()
        
        expr = {"type": "int"}
        context = {}
        
        result = checker.infer_type(expr, context)
        assert result is not None
        assert result.name == "int"
    
    def test_infer_type_from_context(self):
        """Test type inference from context."""
        checker = TypeChecker()
        
        expr = {"var": "x"}
        context = {"x": IntType()}
        
        result = checker.infer_type(expr, context)
        assert result is not None
        assert result.name == "int"
    
    def test_unify_types(self):
        """Test type unification."""
        checker = TypeChecker()
        
        # Unify same types
        result = checker.unify_types(IntType(), IntType())
        assert result is not None
        assert result.name == "int"
    
    def test_unify_incompatible_types(self):
        """Test unification of incompatible types."""
        checker = TypeChecker()
        
        result = checker.unify_types(IntType(), StringType())
        assert result is None
        assert len(checker.errors) > 0
    
    def test_unify_with_type_variable(self):
        """Test unification with type variable."""
        checker = TypeChecker()
        
        tv = TypeVariable(name="T")
        int_type = IntType()
        
        result = checker.unify_types(tv, int_type)
        assert result is not None
        assert tv.is_resolved() is True
    
    def test_checker_stats(self):
        """Test getting checker statistics."""
        checker = TypeChecker()
        
        stats = checker.get_stats()
        
        assert stats["registered_types"] > 0
        assert stats["primitives"] > 0
        assert stats["errors"] == 0
    
    def test_clear_errors(self):
        """Test clearing errors."""
        checker = TypeChecker()
        
        checker.check_type(IntType(), StringType())
        assert len(checker.errors) == 1
        
        checker.clear_errors()
        assert len(checker.errors) == 0


class TestTypeEdgeCases(unittest.TestCase):
    """Edge case tests for types."""
    
    def test_nested_struct(self):
        """Test nested struct types."""
        inner = StructType(fields={"value": IntType()})
        outer = StructType(fields={"inner": inner})
        
        assert outer.fields["inner"].name.startswith("struct_")
    
    def test_self_referential_struct(self):
        """Test struct with self-referential field (using TypeVariable)."""
        registry = TypeRegistry()
        
        # Create a type variable for forward reference
        node_type = TypeVariable(name="Node")
        
        # Create struct that references the type variable
        node_struct = StructType(fields={
            "value": IntType(),
            "next": node_type
        })
        
        registry.register_type(node_struct)
        
        # Resolve the type variable later
        node_type.resolve(node_struct)
        
        assert node_type.is_resolved() is True
    
    def test_empty_struct(self):
        """Test empty struct."""
        struct = StructType(fields={})
        
        assert len(struct.fields) == 0
        assert struct.name.startswith("struct_")
    
    def test_empty_union(self):
        """Test empty union (should be bottom type)."""
        union = UnionType(variants=[])
        
        assert len(union.variants) == 0
        # Empty union should be incompatible with everything
        assert union.is_compatible_with(IntType()) is False
    
    def test_empty_sequence(self):
        """Test empty sequence."""
        # Creating a sequence without element type would fail
        # This is an edge case that should be handled gracefully
        int_type = IntType()
        seq = SequenceType(element_type=int_type)
        
        assert seq.element_type.name == "int"
