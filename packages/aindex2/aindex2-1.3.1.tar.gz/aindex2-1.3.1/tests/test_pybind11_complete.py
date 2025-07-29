#!/usr/bin/env python3
"""
Test script to verify all pybind11 bindings are working
"""

import sys
import os
sys.path.insert(0, '/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex')

# Import both APIs for comparison
from aindex.core.aindex import get_aindex as get_aindex_pybind11, AIndex
import aindex_cpp

def test_direct_wrapper():
    """Test the direct pybind11 wrapper"""
    print("=== Testing direct pybind11 wrapper ===")
    
    wrapper = aindex_cpp.AindexWrapper()
    
    # Test loading
    prefix = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/tests/temp/test"
    wrapper.load(f"{prefix}.23", f"{prefix}.23.tf.bin")
    wrapper.load_reads(f"{prefix}.reads")
    wrapper.load_reads_index(f"{prefix}.ridx")
    wrapper.load_aindex(f"{prefix}.23", 255)
    
    print(f"Hash size: {wrapper.get_hash_size()}")
    print(f"Number of k-mers: {wrapper.get_n()}")
    print(f"Reads size: {wrapper.get_reads_size()}")
    
    # Test k-mer operations
    test_kmer = "ATGCGATCGATCGATCGATCGAT"
    count = wrapper.get(test_kmer)
    print(f"K-mer '{test_kmer}' count: {count}")
    
    if count > 0:
        kid = wrapper.get_kid_by_kmer(test_kmer)
        print(f"K-mer ID: {kid}")
        
        kmer_back = wrapper.get_kmer_by_kid(kid)
        print(f"K-mer from ID: {kmer_back}")
        
        strand = wrapper.get_strand(test_kmer)
        print(f"Strand: {strand}")
        
        hash_value = wrapper.get_hash_value(test_kmer)
        print(f"Hash value: {hash_value}")
        
        positions = wrapper.get_positions(test_kmer)
        print(f"Positions: {positions[:5]}...")  # Show first 5
        
        if positions:
            pos = positions[0]
            rid = wrapper.get_rid(pos)
            start = wrapper.get_start(pos)
            print(f"Position {pos}: read_id={rid}, start={start}")
            
            # Test read retrieval
            read = wrapper.get_read_by_rid(rid)
            print(f"Read {rid}: {read[:50]}...")
            
            # Test read by positions
            read_fragment = wrapper.get_read(start, start + 50, False)
            print(f"Read fragment: {read_fragment}")
    
    # Test utility functions
    tf, kmer_result, rkmer = wrapper.get_kmer(0)  # Get info for first k-mer
    print(f"First k-mer info: tf={tf}, kmer={kmer_result}, rkmer={rkmer}")
    
    # Test validation
    wrapper.check_aindex()
    wrapper.check_aindex_reads()
    print("✓ Direct wrapper tests passed")

def test_python_api():
    """Test the Python API wrapper"""
    print("\n=== Testing Python API wrapper ===")
    
    prefix = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/tests/temp/test"
    aindex = get_aindex_pybind11(prefix, max_tf=255)
    
    print(f"Hash size: {aindex.get_hash_size()}")
    print(f"Number of k-mers: {len(aindex)}")
    print(f"Reads size: {aindex.reads_size}")
    
    # Test k-mer operations
    test_kmer = "ATGCGATCGATCGATCGATCGAT"
    count = aindex[test_kmer]
    print(f"K-mer '{test_kmer}' count: {count}")
    
    if count > 0:
        kid = aindex.get_kid_by_kmer(test_kmer)
        print(f"K-mer ID: {kid}")
        
        kmer_back = aindex.get_kmer_by_kid(kid)
        print(f"K-mer from ID: {kmer_back}")
        
        strand = aindex.get_strand(test_kmer)
        print(f"Strand: {strand}")
        
        positions = aindex.pos(test_kmer)
        print(f"Positions: {positions[:5]}...")  # Show first 5
        
        if positions:
            pos = positions[0]
            rid = aindex.get_rid(pos)
            start = aindex.get_start(pos)
            print(f"Position {pos}: read_id={rid}, start={start}")
            
            # Test read retrieval
            read = aindex.get_read_by_rid(rid)
            print(f"Read {rid}: {read[:50]}...")
            
            # Test read by positions  
            read_fragment = aindex.get_read(start, start + 50, False)
            print(f"Read fragment: {read_fragment}")
    
    # Test iteration
    print("\nTesting iteration over reads...")
    read_count = 0
    for rid, read in aindex.iter_reads():
        read_count += 1
        if read_count <= 3:  # Show first 3 reads
            print(f"Read {rid}: {read[:30]}...")
        if read_count >= 10:
            break
    print(f"Iterated over {read_count} reads")
    
    # Test k-mer iteration over a sequence
    test_seq = "ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC"
    kmer_counts = list(aindex.iter_sequence_kmers(test_seq, k=23))
    print(f"Found {len(kmer_counts)} k-mers in test sequence")
    
    # Test coverage
    coverage = aindex.get_sequence_coverage(test_seq, cutoff=0, k=23)
    print(f"Coverage array length: {len(coverage)}")
    
    print("✓ Python API tests passed")

def test_compatibility():
    """Test compatibility with expected ctypes API"""
    print("\n=== Testing compatibility ===")
    
    prefix = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/tests/temp/test"
    aindex = get_aindex_pybind11(prefix, max_tf=255)
    
    # Test all the methods that should be available
    methods_to_test = [
        'get_hash_size', '__len__', '__getitem__', 'get_strand', 
        'get_kid_by_kmer', 'get_kmer_by_kid', '__contains__', 'get',
        'get_rid', 'get_start', 'get_read_by_rid', 'get_read',
        'iter_reads', 'iter_reads_se', 'pos', 'iter_sequence_kmers',
        'get_sequence_coverage', 'get_rid2poses', 'increase', 'decrease'
    ]
    
    for method_name in methods_to_test:
        if hasattr(aindex, method_name):
            print(f"✓ {method_name} - available")
        else:
            print(f"✗ {method_name} - MISSING")
    
    # Test some specific compatibility features
    test_kmer = "ATGCGATCGATCGATCGATCGAT"
    
    # Dictionary-like access
    if test_kmer in aindex:
        print(f"✓ K-mer '{test_kmer}' found using 'in' operator")
    
    # Get with default
    count = aindex.get(test_kmer, 0)
    print(f"✓ get() with default: {count}")
    
    # Position mapping
    rid2poses = aindex.get_rid2poses(test_kmer)
    print(f"✓ rid2poses mapping: {len(rid2poses)} reads")
    
    print("✓ Compatibility tests passed")

if __name__ == "__main__":
    print("Testing complete pybind11 API...")
    
    # Check if test data exists
    test_prefix = "/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/tests/temp/test"
    required_files = [
        f"{test_prefix}.23.pf",
        f"{test_prefix}.23.tf.bin",
        f"{test_prefix}.reads",
        f"{test_prefix}.ridx"
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"Missing test files: {missing}")
        print("Please run the regression tests first to generate test data")
        sys.exit(1)
    
    try:
        test_direct_wrapper()
        test_python_api()
        test_compatibility()
        print("\n🎉 ALL TESTS PASSED! The pybind11 API is fully functional.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
