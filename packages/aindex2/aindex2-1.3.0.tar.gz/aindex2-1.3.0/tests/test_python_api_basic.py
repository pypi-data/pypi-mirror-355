#!/usr/bin/env python3
"""
Basic Python API test script for aindex
Tests module import and basic functionality
"""

import sys
import os

# Add parent directory to Python path (where aindex package is located)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def test_basic_import():
    """Test basic module import"""
    print('✓ Test 1: Importing aindex module...')
    try:
        import aindex
        print('  SUCCESS: aindex module imported!')
        return True
    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def test_cpp_wrapper():
    """Test C++ wrapper availability"""
    print('✓ Test 2: Checking C++ wrapper...')
    try:
        from aindex.core import aindex_cpp
        methods = [attr for attr in dir(aindex_cpp.AindexWrapper) if not attr.startswith('_')]
        print(f'  Found {len(methods)} methods in C++ wrapper')
        
        # Check for key methods
        required_methods = ['load', 'load_reads', 'get_tf_value', 'get_hash_value']
        missing = [m for m in required_methods if m not in methods]
        if missing:
            print(f'  WARNING: Missing methods: {missing}')
            return False
        else:
            print('  All required methods found!')
            return True
    except Exception as e:
        print(f'  ERROR: {e}')
        return False

def main():
    """Run all basic tests"""
    print('=== BASIC PYTHON API TESTS ===')
    
    tests = [test_basic_import, test_cpp_wrapper]
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f'❌ Test failed with exception: {e}')
            results.append(False)
    
    if all(results):
        print('🎉 All basic tests passed!')
        return 0
    else:
        print('❌ Some tests failed!')
        return 1

if __name__ == '__main__':
    sys.exit(main())
