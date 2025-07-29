#!/usr/bin/env python
"""
Simple debug test to isolate kmer segfault issue
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from aindex.core.aindex import load_index

# Use test results from temp directory
test_dir = Path(__file__).parent / "tests"
temp_dir = test_dir / "temp"

# Define explicit file paths
hash_file = str(temp_dir / "test_kmer_counter.23.index.bin")
tf_file = str(temp_dir / "test_kmer_counter.23.tf.bin")
kmers_bin_file = str(temp_dir / "test_kmer_counter.23.kmers.bin")
kmers_text_file = str(temp_dir / "test_kmer_counter.23.txt")

print(f"Loading files:")
print(f"  hash: {hash_file}")
print(f"  tf: {tf_file}")
print(f"  kmers_bin: {kmers_bin_file}")
print(f"  kmers_text: {kmers_text_file}")

# Load index
try:
    aindex = load_index(hash_file, tf_file, kmers_bin_file, kmers_text_file)
    print("Index loaded successfully")
except Exception as e:
    print(f"Failed to load index: {e}")
    sys.exit(1)

# Check basic properties
print(f"N kmers: {aindex.n_kmers}")

# Test the exact kmers from demo.py that caused segfault
test_kmers = [
    "AAAAAAAAAAAAAAAAAAAAAAA",  # A*23 - this one caused the segfault
    "TTTTTTTTTTTTTTTTTTTTTTT",  # T*23
    "AAAAAAAAAAAAAAAAAAAAAAT",  # Mixed
]

for kmer in test_kmers:
    print(f"\nTesting kmer: {kmer} (length: {len(kmer)})")
    try:
        print("  Getting hash value...")
        hash_val = aindex.get_hash_value(kmer)
        print(f"  Hash value: {hash_val}")
        
        print("  Getting TF value...")
        tf = aindex.get_tf_value(kmer)
        print(f"  TF value: {tf}")
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        break

print("Debug test complete")
