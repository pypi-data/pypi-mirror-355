#!/usr/bin/env python3
"""
Simple test for 13-mer position indexing with fixed progress reporting.
"""

import sys
import os
import tempfile
import shutil

def test_simple_13mer_workflow():
    """Test the basic 13-mer workflow with a small dataset."""
    print("=== Simple 13-mer Workflow Test ===")
    
    # Create temporary directory
    test_dir = tempfile.mkdtemp(prefix="aindex_13mer_simple_")
    print(f"Test directory: {test_dir}")
    
    try:
        # Create simple test reads
        reads_file = os.path.join(test_dir, "test_reads.txt")
        with open(reads_file, 'w') as f:
            f.write("AAAAAAAAAAAAA\n")       # 13 A's
            f.write("TTTTTTTTTTTTT\n")       # 13 T's  
            f.write("ATGATGATGATGA\n")       # Mixed pattern
            f.write("GCGCGCGCGCGCG\n")       # GC pattern
            
        print(f"Created test reads: {reads_file}")
        
        # Create small k-mer set for testing
        kmers_file = os.path.join(test_dir, "test_kmers.txt")
        with open(kmers_file, 'w') as f:
            f.write("AAAAAAAAAAAAA\n")
            f.write("TTTTTTTTTTTTT\n")
            f.write("ATGATGATGATGA\n")
            f.write("GCGCGCGCGCGCG\n")
            f.write("CCCCCCCCCCCCC\n")
            f.write("GGGGGGGGGGGGG\n")
            
        print(f"Created test k-mers: {kmers_file}")
        
        # Step 1: Build perfect hash
        hash_prefix = os.path.join(test_dir, "test_13mer")
        cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/build_13mer_hash.exe {kmers_file} {hash_prefix}"
        print(f"\nStep 1: Building perfect hash...")
        print(f"Command: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"❌ Hash building failed with exit code {result}")
            return False
            
        # Check created files
        hash_file = hash_prefix + ".hash"
        tf_file = hash_prefix + ".tf.bin"
        
        if not os.path.exists(hash_file):
            print(f"❌ Hash file not created: {hash_file}")
            return False
        if not os.path.exists(tf_file):
            print(f"❌ TF file not created: {tf_file}")
            return False
            
        print(f"✅ Hash files created:")
        print(f"  Hash: {hash_file} ({os.path.getsize(hash_file)} bytes)")
        print(f"  TF: {tf_file} ({os.path.getsize(tf_file)} bytes)")
        
        # Step 2: Count frequencies
        output_tf_file = os.path.join(test_dir, "frequencies.tf.bin")
        cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/count_kmers13.exe {reads_file} {hash_file} {output_tf_file}"
        print(f"\nStep 2: Counting k-mer frequencies...")
        print(f"Command: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"❌ Frequency counting failed with exit code {result}")
            return False
            
        if not os.path.exists(output_tf_file):
            print(f"❌ Output TF file not created: {output_tf_file}")
            return False
            
        print(f"✅ Frequency file created: {output_tf_file} ({os.path.getsize(output_tf_file)} bytes)")
        
        # Step 3: Build position index
        output_prefix = os.path.join(test_dir, "aindex13")
        cmd = f"/Users/akomissarov/Dropbox2/Dropbox/workspace/aindex/bin/compute_aindex13.exe {reads_file} {hash_file} {output_tf_file} {output_prefix} 2"
        print(f"\nStep 3: Building position index...")
        print(f"Command: {cmd}")
        result = os.system(cmd)
        if result != 0:
            print(f"❌ Position index building failed with exit code {result}")
            return False
            
        # Check output files
        pos_file = output_prefix + ".pos.bin"
        index_file = output_prefix + ".index.bin"
        indices_file = output_prefix + ".indices.bin"
        
        expected_files = [pos_file, index_file, indices_file]
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✅ {os.path.basename(file_path)}: {os.path.getsize(file_path)} bytes")
            else:
                print(f"❌ Missing: {file_path}")
                return False
                
        print("\n🎉 All steps completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print(f"\nCleaning up: {test_dir}")
        shutil.rmtree(test_dir, ignore_errors=True)

if __name__ == "__main__":
    success = test_simple_13mer_workflow()
    sys.exit(0 if success else 1)
