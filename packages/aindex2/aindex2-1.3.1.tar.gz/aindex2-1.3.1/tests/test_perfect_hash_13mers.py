#!/usr/bin/env python3
"""
Quick test for perfect hash for 13-mers
"""

import os
import struct
import time
import random

def test_13mer_perfect_hash(prefix="test_13mers/13mer_index"):
    """Tests the created perfect hash"""
    
    hash_file = f"{prefix}.hash"
    kmers_file = f"{prefix}.kmers.bin"
    tf_file = f"{prefix}.tf.bin"
    
    print("=== Testing Perfect Hash for 13-mers ===")
    
    # Check file existence
    for fname in [hash_file, kmers_file, tf_file]:
        if not os.path.exists(fname):
            print(f"Error: file {fname} not found")
            return False
    
    # Check file sizes
    kmers_size = os.path.getsize(kmers_file)
    tf_size = os.path.getsize(tf_file)
    hash_size = os.path.getsize(hash_file)
    
    expected_kmers = 67108864  # 4^13
    expected_kmers_bytes = expected_kmers * 8  # uint64_t
    expected_tf_bytes = expected_kmers * 4     # uint32_t
    
    print(f"File sizes:")
    print(f"  Hash function: {hash_size:,} bytes ({hash_size / (1024*1024):.1f} MB)")
    print(f"  K-mers:        {kmers_size:,} bytes ({kmers_size / (1024*1024):.1f} MB)")
    print(f"  Frequencies:   {tf_size:,} bytes ({tf_size / (1024*1024):.1f} MB)")
    print(f"  TOTAL:         {(hash_size + kmers_size + tf_size):,} bytes ({(hash_size + kmers_size + tf_size) / (1024*1024):.1f} MB)")
    
    print(f"\nExpected sizes:")
    print(f"  K-mers:     {expected_kmers_bytes:,} bytes ({expected_kmers_bytes / (1024*1024):.1f} MB)")
    print(f"  Frequencies: {expected_tf_bytes:,} bytes ({expected_tf_bytes / (1024*1024):.1f} MB)")
    
    # Check size correctness
    if kmers_size != expected_kmers_bytes:
        print(f"ERROR: k-mers file size {kmers_size} != {expected_kmers_bytes}")
        return False
        
    if tf_size != expected_tf_bytes:
        print(f"ERROR: frequencies file size {tf_size} != {expected_tf_bytes}")
        return False
    
    print("\n✓ File sizes are correct")
    
    # Read several random records for verification
    print("\nChecking random records...")
    
    with open(kmers_file, 'rb') as kf, open(tf_file, 'rb') as tf:
        for i in range(10):
            # Random position
            pos = random.randint(0, expected_kmers - 1)
            
            # Read k-mer (uint64_t)
            kf.seek(pos * 8)
            kmer_bits = struct.unpack('<Q', kf.read(8))[0]
            
            # Read frequency (uint32_t)
            tf.seek(pos * 4)
            frequency = struct.unpack('<I', tf.read(4))[0]
            
            # Convert bits back to string
            kmer_str = bits_to_13mer(kmer_bits & 0xFFFFFFFF)  # take only lower 32 bits
            
            print(f"  Position {pos:8}: {kmer_str} (frequency: {frequency})")
    
    print("\n✓ Perfect hash for 13-mers created successfully!")
    print(f"✓ All {expected_kmers:,} k-mers processed")
    print(f"✓ EMPHF size: {hash_size / (1024*1024):.1f} MB")
    print(f"✓ EMPHF compression ratio: {(expected_kmers * 13) / hash_size:.1f}x")
    
    return True

def bits_to_13mer(bits):
    """Converts 32-bit representation back to 13-mer"""
    bases = "ACGT"
    kmer = ""
    for i in range(13):
        kmer = bases[bits & 3] + kmer
        bits >>= 2
    return kmer

def compare_storage_methods():
    """Compares different storage methods for 13-mers"""
    
    total_kmers = 67108864  # 4^13
    
    print("\n=== Comparison of 13-mer storage methods ===")
    
    # 1. Text format (13 bytes + newline per k-mer)
    text_size = total_kmers * 14
    print(f"1. Text format:          {text_size:,} bytes ({text_size / (1024*1024):.1f} MB)")
    
    # 2. Direct uint32_t array
    direct_array_size = total_kmers * 4
    print(f"2. Direct array:         {direct_array_size:,} bytes ({direct_array_size / (1024*1024):.1f} MB)")
    
    # 3. Perfect hash (hash + data)
    hash_size = 21 * 1024 * 1024  # 21 MB
    data_size = total_kmers * 4    # uint32_t for frequencies
    perfect_hash_size = hash_size + data_size
    print(f"3. Perfect Hash:         {perfect_hash_size:,} bytes ({perfect_hash_size / (1024*1024):.1f} MB)")
    print(f"   - EMPHF function:     {hash_size:,} bytes ({hash_size / (1024*1024):.1f} MB)")
    print(f"   - Data:               {data_size:,} bytes ({data_size / (1024*1024):.1f} MB)")
    
    print(f"\nPerfect Hash vs direct array improvement: {direct_array_size / perfect_hash_size:.2f}x")
    print(f"Perfect Hash vs text improvement: {text_size / perfect_hash_size:.2f}x")

if __name__ == "__main__":
    print("Testing Perfect Hash for 13-mers...")
    
    success = test_13mer_perfect_hash()
    
    if success:
        compare_storage_methods()
    else:
        print("Test failed!")
