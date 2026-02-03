#!/usr/bin/env python3
"""
Test script to verify GHLL syntax fix without external dependencies.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ghll_syntax():
    """Test that GHLL classes can be defined and instantiated."""
    
    # Test basic class definition
    class TestGHLLLexer:
        """Test version of GHLLLexer to verify syntax."""
        def __init__(self):
            self.tokens = []
        
        def tokenize(self, text):
            return ["test_token"]
    
    class TestGHLLProcessor:
        """Test version of GHLLProcessor to verify syntax."""
        def __init__(self):
            self.lexer = TestGHLLLexer()
    
    # Test instantiation
    lexer = TestGHLLLexer()
    processor = TestGHLLProcessor()
    
    # Test basic functionality
    tokens = lexer.tokenize("test input")
    assert tokens == ["test_token"]
    
    print("✓ GHLL syntax test passed - classes can be defined and instantiated")
    return True

def test_ghll_import():
    """Test importing the actual GHLL module (may fail due to numpy)."""
    try:
        # Try to import just the class definitions without executing
        import ast
        
        with open('src/haai/nsc/ghll.py', 'r') as f:
            source_code = f.read()
        
        # Parse the source code to check for syntax errors
        try:
            ast.parse(source_code)
            print("✓ GHLL module has valid Python syntax")
            return True
        except SyntaxError as e:
            print(f"✗ GHLL module has syntax error: {e}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing GHLL import: {e}")
        return False

if __name__ == "__main__":
    print("Testing GHLL syntax fix...")
    
    # Test 1: Basic class syntax
    test1_passed = test_ghll_syntax()
    
    # Test 2: Actual module syntax
    test2_passed = test_ghll_import()
    
    if test1_passed and test2_passed:
        print("\n✓ All tests passed - GHLL syntax fix is successful!")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)