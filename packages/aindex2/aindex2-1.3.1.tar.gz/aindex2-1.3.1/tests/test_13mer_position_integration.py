#!/usr/bin/env python3

"""
Comprehensive test for 13-mer position indexing and retrieval functionality.
Tests the complete pipeline: hash building, tf counting, position indexing, and searching.
"""

import sys
import os
import time
import tempfile
import shutil

# Add PYTHONPATH for direct import
sys.path.insert(0, '/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/aindex/core')

# Import only the C++ wrapper directly without going through aindex/__init__.py
try:
    import aindex_cpp
    AindexWrapper = aindex_cpp.AindexWrapper
except ImportError as e:
    print(f"Error importing aindex_cpp: {e}")
    print("Make sure the Python extension was compiled successfully")
    sys.exit(1)

def create_test_data():
    """Create simple test data with known k-mers."""
    test_data = tempfile.mkdtemp(prefix="aindex_13mer_test_")
    
    # Create test reads with known 13-mers
    reads_file = os.path.join(test_data, "test_reads.txt")
    with open(reads_file, 'w') as f:
        # Read 1: Contains "AAAAAAAAAAAAA" at position 0
        f.write("AAAAAAAAAAAAA\n")
        # Read 2: Contains "TTTTTTTTTTTTT" at position 14 (next line)
        f.write("TTTTTTTTTTTTT\n")
        # Read 3: Contains "ATGATGATGATGA" at position 28
        f.write("ATGATGATGATGA\n")
        # Read 4: Contains overlapping patterns
        f.write("AAAAAAAAAAAATTTTTTTTTTTTTGCGCGCGCGCGCG\n")
    
    print(f"Test data created in: {test_data}")
    print(f"Reads file: {reads_file}")
    
    return test_data, reads_file

def build_13mer_infrastructure(test_data, reads_file):
    """Build complete 13-mer infrastructure."""
    print("\n=== Building 13-mer infrastructure ===")
    
    # Step 1: Generate all 13-mers
    kmers_file = os.path.join(test_data, "all_13mers.txt")
    cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/generate_all_13mers.exe {kmers_file}"
    print(f"Running: {cmd}")
    os.system(cmd)
    
    # Step 2: Build perfect hash  
    hash_prefix = os.path.join(test_data, "13mer")
    cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/build_13mer_hash.exe {kmers_file} {hash_prefix}"
    print(f"Running: {cmd}")
    result = os.system(cmd)
    
    if result != 0:
        print(f"Warning: build_13mer_hash.exe returned exit code {result}")
    
    # The actual files created will have these names:
    hash_file = hash_prefix + ".hash"
    kmers_bin_file = hash_prefix + ".kmers.bin" 
    tf_file = hash_prefix + ".tf.bin"
    
    # Step 3: Count k-mer frequencies (skip if tf file already exists from hash building)
    if not os.path.exists(tf_file):
        cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/count_kmers13.exe {reads_file} {hash_file} {tf_file}"
        print(f"Running: {cmd}")
        os.system(cmd)
    else:
        print(f"TF file already exists: {tf_file}")
    
    # Step 4: Build position index
    pos_file = os.path.join(test_data, "pos.bin")
    index_file = os.path.join(test_data, "index.bin") 
    indices_file = os.path.join(test_data, "indices.bin")
    
    # Note: compute_aindex13.exe expects different argument order
    cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/compute_aindex13.exe {reads_file} {hash_file} {tf_file} {test_data}/output 4 {pos_file} {index_file} {indices_file}"
    print(f"Running: {cmd}")
    os.system(cmd)
    
    return {
        'kmers_file': kmers_file,
        'hash_file': hash_file, 
        'kmers_bin_file': kmers_bin_file,
        'tf_file': tf_file,
        'pos_file': pos_file,
        'index_file': index_file,
        'indices_file': indices_file
    }

def test_frequency_lookup(wrapper, test_kmers):
    """Test k-mer frequency lookup."""
    print("\n=== Testing frequency lookup ===")
    
    for kmer in test_kmers:
        tf = wrapper.get_tf_value(kmer)
        print(f"K-mer: {kmer} -> TF: {tf}")

def test_position_lookup(wrapper, test_kmers):
    """Test k-mer position lookup."""
    print("\n=== Testing position lookup ===")
    
    for kmer in test_kmers:
        positions = wrapper.get_positions(kmer)
        print(f"K-mer: {kmer} -> Positions: {positions}")

def test_13mer_specific_functions(wrapper, test_kmers):
    """Test 13-mer specific functions."""
    print("\n=== Testing 13-mer specific functions ===")
    
    # Test get_positions_13mer directly
    for kmer in test_kmers:
        positions = wrapper.get_positions_13mer(kmer)
        print(f"K-mer: {kmer} -> Positions (13mer): {positions}")
    
    # Test batch processing
    tf_values = wrapper.get_tf_values_13mer(test_kmers)
    print(f"Batch TF values: {tf_values}")

def verify_expected_results(wrapper):
    """Verify expected results for known k-mers."""
    print("\n=== Verifying expected results ===")
    
    # These k-mers should have frequency 1 and be at specific positions
    expected_results = {
        "AAAAAAAAAAAAA": {"tf": 1, "positions": [0]},  # First read, position 0
        "TTTTTTTTTTTTT": {"tf": 1, "positions": [14]}, # Second read, position 14
        "ATGATGATGATGA": {"tf": 1, "positions": [28]}, # Third read, position 28
    }
    
    all_passed = True
    
    for kmer, expected in expected_results.items():
        # Test frequency
        tf = wrapper.get_tf_value(kmer)
        if tf != expected["tf"]:
            print(f"❌ FAIL: {kmer} expected TF {expected['tf']}, got {tf}")
            all_passed = False
        else:
            print(f"✅ PASS: {kmer} TF = {tf}")
        
        # Test positions
        positions = wrapper.get_positions(kmer)
        if positions != expected["positions"]:
            print(f"❌ FAIL: {kmer} expected positions {expected['positions']}, got {positions}")
            all_passed = False
        else:
            print(f"✅ PASS: {kmer} positions = {positions}")
    
    return all_passed

def main():
    """Main test function."""
    print("=== 13-mer Position Index Integration Test ===")
    
    try:
        # Create test data
        test_data, reads_file = create_test_data()
        
        # Build infrastructure
        files = build_13mer_infrastructure(test_data, reads_file)
        
        # Verify files were created
        for name, path in files.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"✅ {name}: {path} ({size} bytes)")
            else:
                print(f"❌ {name}: {path} (missing)")
                return False
        
        # Test Python API
        print("\n=== Testing Python API ===")
        
        # Initialize wrapper
        wrapper = AindexWrapper()
        
        # Load 13-mer index (hash + tf)
        print("Loading 13-mer index...")
        wrapper.load_13mer_index(files['hash_file'], files['tf_file'])
        
        # Load 13-mer position index
        print("Loading 13-mer position index...")
        wrapper.load_13mer_aindex(files['pos_file'], files['index_file'], files['indices_file'])
        
        # Get index info
        print("\nIndex info:")
        print(wrapper.get_index_info())
        
        # Test with known k-mers
        test_kmers = [
            "AAAAAAAAAAAAA",  # Should be at position 0
            "TTTTTTTTTTTTT",  # Should be at position 14  
            "ATGATGATGATGA",  # Should be at position 28
            "GCGCGCGCGCGCG",  # Random k-mer, may or may not exist
            "NNNNNNNNNNNNN",  # Invalid k-mer
        ]
        
        # Run tests
        test_frequency_lookup(wrapper, test_kmers)
        test_position_lookup(wrapper, test_kmers)
        test_13mer_specific_functions(wrapper, test_kmers)
        
        # Verify expected results
        success = verify_expected_results(wrapper)
        
        if success:
            print("\n🎉 ALL TESTS PASSED! 13-mer position indexing is working correctly.")
        else:
            print("\n❌ SOME TESTS FAILED!")
            
        return success
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test data
        if 'test_data' in locals():
            print(f"\nCleaning up test data: {test_data}")
            shutil.rmtree(test_data, ignore_errors=True)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
