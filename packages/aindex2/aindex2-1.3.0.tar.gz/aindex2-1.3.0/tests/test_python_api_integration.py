#!/usr/bin/env python3
"""
Integration test script for aindex Python API
Tests with real data files from regression tests
"""

import sys
import os

# Add parent directory to Python path (where aindex package is located)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

def check_test_data():
    """Check if test data files exist"""
    required_files = [
        'tests/temp/test_kmer_counter.23.index.bin',
        'tests/temp/test_kmer_counter.23.tf.bin',
        'tests/temp/test_kmer_counter.23.kmers.bin',
        'tests/temp/test_kmer_counter.23.pos.bin',
        'tests/temp/test_kmer_counter.23.indices.bin',
        'tests/temp/test_kmer_counter.reads'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print('❌ Test data files not found:')
        for f in missing:
            print(f'  - {f}')
        print('\nPlease run regression tests first:')
        print('  cd tests && python3 test_regression.py --skip-jellyfish')
        return False
    
    print('✓ All required test data files found')
    return True

def test_load_index():
    """Test loading index with all files"""
    print('✓ Test: Loading index with all files...')
    try:
        import aindex
        
        # Define file paths (using correct names from demo)
        hash_file = 'tests/temp/test_kmer_counter.23.index.bin'
        tf_file = 'tests/temp/test_kmer_counter.23.tf.bin'
        kmers_bin_file = 'tests/temp/test_kmer_counter.23.kmers.bin'
        kmers_text_file = ''  # Not used
        reads_file = 'tests/temp/test_kmer_counter.reads'
        pos_file = 'tests/temp/test_kmer_counter.23.pos.bin'
        index_file = 'tests/temp/test_kmer_counter.23.index.bin'
        indices_file = 'tests/temp/test_kmer_counter.23.indices.bin'
        
        # Use named parameters as in demo
        index = aindex.load_index_with_reads(
            hash_file=hash_file,
            tf_file=tf_file,
            kmers_bin_file=kmers_bin_file,
            kmers_text_file=kmers_text_file,
            reads_file=reads_file,
            pos_file=pos_file,
            index_file=index_file,
            indices_file=indices_file
        )
        
        print(f'  - Reads: {index.n_reads}')
        print(f'  - Kmers: {index.n_kmers}')
        print(f'  - Reads size: {index.reads_size}')
        
        # Basic sanity checks
        if index.n_reads == 0:
            print('  WARNING: No reads loaded')
            return False
        if index.n_kmers == 0:
            print('  WARNING: No kmers loaded')
            return False
            
        print('  SUCCESS: Index loaded correctly!')
        return index
        
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_kmer_query(index):
    """Test kmer querying functionality"""
    print('✓ Test: Testing kmer queries...')
    try:
        # Test with a 23bp kmer (the k-mer size used in tests)
        test_kmer = 'ATCGATCGATCGATCGATCGATCG'  # 23bp
        
        # Test TF value query
        tf_value = index.get_tf_value(test_kmer)
        print(f'  - TF value for test kmer: {tf_value}')
        
        # Test hash value query
        hash_value = index.get_hash_value(test_kmer)
        print(f'  - Hash value for test kmer: {hash_value}')
        
        print('  SUCCESS: Kmer queries work!')
        return True
        
    except Exception as e:
        print(f'  ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print('=== PYTHON API INTEGRATION TESTS ===')
    
    # Check test data
    if not check_test_data():
        return 1
    
    # Test index loading
    index = test_load_index()
    if not index:
        return 1
    
    # Test queries
    if not test_kmer_query(index):
        return 1
    
    print('🎉 ALL INTEGRATION TESTS PASSED! 🎉')
    return 0

if __name__ == '__main__':
    sys.exit(main())
