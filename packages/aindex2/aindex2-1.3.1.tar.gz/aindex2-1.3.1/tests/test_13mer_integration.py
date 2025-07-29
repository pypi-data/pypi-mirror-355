#!/usr/bin/env python3
"""
Test script for 13-mer integration in aindex
Tests automatic mode detection, loading, and querying
"""

import sys
import os
sys.path.insert(0, '/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex')

import aindex

def test_13mer_integration():
    """Test 13-mer mode integration"""
    print("Testing 13-mer integration in aindex...")
    
    # Check if required files exist (from previous tests)
    hash_file = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/test_13mers/13mer_index.hash"
    tf_file = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/test_13mers/13mer_index.tf.bin"
    
    if not os.path.exists(hash_file):
        print(f"ERROR: Hash file not found: {hash_file}")
        print("Please run the 13-mer generation and hash building first")
        return False
        
    if not os.path.exists(tf_file):
        print(f"ERROR: TF file not found: {tf_file}")
        print("Please run the 13-mer counting first")
        return False
    
    try:
        # Test 1: Load 13-mer index using convenience function
        print("\n1. Testing load_13mer_index()...")
        index = aindex.load_13mer_index(hash_file, tf_file)
        print("✓ Successfully loaded 13-mer index")
        
        # Test 2: Check index info
        print("\n2. Testing index info...")
        info = index.get_index_info()
        print("Index information:")
        print(info)
        assert "Mode: 13-mer" in info
        print("✓ Confirmed 13-mer mode")
        
        # Test 3: Test single k-mer query
        print("\n3. Testing single k-mer queries...")
        test_kmers = [
            "AAAAAAAAAAAAA",  # All A's
            "ATCGATCGATCGA",  # Mixed
            "TTTTTTTTTTTTT",  # All T's
            "GCGCGCGCGCGCG",  # Alternating GC
            "NNNNNNNNNNNNN",  # Invalid (should return 0)
        ]
        
        for kmer in test_kmers:
            tf_value = index.get_tf_value(kmer)
            print(f"  {kmer}: tf = {tf_value}")
            if 'N' in kmer:
                assert tf_value == 0, "Invalid k-mer should return 0"
        
        print("✓ Single k-mer queries working")
        
        # Test 4: Test batch k-mer queries
        print("\n4. Testing batch k-mer queries...")
        tf_values = index.get_tf_values(test_kmers)
        print(f"  Batch results: {tf_values}")
        assert len(tf_values) == len(test_kmers)
        assert tf_values[-1] == 0  # Last k-mer with N's should be 0
        print("✓ Batch k-mer queries working")
        
        # Test 5: Test direct array access
        print("\n5. Testing direct array access...")
        tf_by_index = index.get_tf_by_index_13mer(0)
        print(f"  TF value at index 0: {tf_by_index}")
        print("✓ Direct array access working")
        
        # Test 6: Test auto-detection with different k-mer sizes
        print("\n6. Testing auto-detection...")
        
        # Create another index instance to test mode detection
        index2 = aindex.AIndex()
        
        # Test querying before any index is loaded
        tf_empty = index2.get_tf_value("ATCGATCGATCGA")
        print(f"  TF value with no index loaded: {tf_empty}")
        assert tf_empty == 0
        
        # Load 13-mer index and test
        index2.load_13mer_index(hash_file, tf_file)
        tf_13mer = index2.get_tf_value("ATCGATCGATCGA")
        print(f"  TF value for 13-mer: {tf_13mer}")
        
        # Test with wrong k-mer size (should return 0)
        tf_wrong_size = index2.get_tf_value("ATCGATCGATCGAAAAAAAAAA")  # 23-mer
        print(f"  TF value for 23-mer in 13-mer mode: {tf_wrong_size}")
        assert tf_wrong_size == 0
        
        print("✓ Auto-detection working")
        
        print("\n🎉 All tests passed! 13-mer integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Test performance of 13-mer queries"""
    print("\nTesting 13-mer query performance...")
    
    hash_file = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/test_13mers/13mer_index.hash"
    tf_file = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/test_13mers/13mer_index.tf.bin"
    
    if not os.path.exists(hash_file) or not os.path.exists(tf_file):
        print("Skipping performance test - required files not found")
        return
    
    try:
        import time
        
        index = aindex.load_13mer_index(hash_file, tf_file)
        
        # Generate test k-mers
        import random
        bases = ['A', 'T', 'G', 'C']
        test_kmers = []
        for _ in range(10000):
            kmer = ''.join(random.choice(bases) for _ in range(13))
            test_kmers.append(kmer)
        
        # Test single queries
        start_time = time.time()
        for kmer in test_kmers[:1000]:  # Test 1000 queries
            index.get_tf_value(kmer)
        single_time = time.time() - start_time
        
        # Test batch queries
        start_time = time.time()
        index.get_tf_values(test_kmers[:1000])
        batch_time = time.time() - start_time
        
        print(f"Single queries (1000): {single_time:.3f}s ({1000/single_time:.0f} qps)")
        print(f"Batch queries (1000):  {batch_time:.3f}s ({1000/batch_time:.0f} qps)")
        print(f"Speedup: {single_time/batch_time:.1f}x")
        
    except Exception as e:
        print(f"Performance test failed: {e}")

if __name__ == "__main__":
    success = test_13mer_integration()
    if success:
        test_performance()
    sys.exit(0 if success else 1)
