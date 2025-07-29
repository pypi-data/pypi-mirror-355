#!/usr/bin/env python3
"""
Test script for checking the all 13-mers generator
"""

import subprocess
import os
import time
import sys

def run_command(cmd, description=""):
    """Executes command and shows result"""
    print(f"\n{'='*50}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*50}")
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = time.time()
        
        print(f"Exit code: {result.returncode}")
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def check_file_info(filename):
    """Shows information about created file"""
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"\nFile: {filename}")
        print(f"Size: {size:,} bytes ({size / (1024*1024):.2f} MB)")
        
        # Show first few lines
        try:
            with open(filename, 'r') as f:
                lines = [f.readline().strip() for _ in range(5)]
                if lines:
                    print("First lines:")
                    for i, line in enumerate(lines, 1):
                        if line:
                            print(f"  {i}: {line}")
        except:
            print("Cannot read file (might be binary)")
            
        # Show last few lines for text files
        try:
            with open(filename, 'r') as f:
                all_lines = f.readlines()
                if len(all_lines) > 10:
                    print("Last lines:")
                    for i, line in enumerate(all_lines[-3:], len(all_lines)-2):
                        print(f"  {i}: {line.strip()}")
                print(f"Total lines: {len(all_lines):,}")
        except:
            pass
    else:
        print(f"File {filename} not found")

def main():
    # Check if executable exists
    exe_path = "bin/generate_all_13mers.exe"
    if not os.path.exists(exe_path):
        print(f"Executable {exe_path} not found. Building...")
        if not run_command("make", "Building aindex"):
            print("Build failed!")
            return False
    
    # Create test directory
    test_dir = "test_13mers"
    os.makedirs(test_dir, exist_ok=True)
    
    print("Testing 13-mer generator...")
    
    # Test 1: Show statistics only
    print("\n" + "="*60)
    print("TEST 1: Show statistics only")
    run_command(f"{exe_path} dummy -s", "Statistics only")
    
    # Test 2: Validation
    print("\n" + "="*60)
    print("TEST 2: Validation test")
    run_command(f"{exe_path} dummy -s -v", "Validation test")
    
    # Test 3: Generate small text file (first 1000 k-mers for testing)
    print("\n" + "="*60)
    print("TEST 3: Generate sample text file")
    
    # Create modification to generate only first N k-mers
    sample_output = f"{test_dir}/sample_13mers.txt"
    
    # For full test create small sample
    print("Generating first 1000 13-mers as sample...")
    try:
        with open(sample_output, 'w') as f:
            bases = ['A', 'C', 'G', 'T']
            for i in range(1000):
                kmer = ""
                temp = i
                for _ in range(13):
                    kmer = bases[temp % 4] + kmer
                    temp //= 4
                f.write(f"{kmer}\t{i}\n")
        
        check_file_info(sample_output)
        
    except Exception as e:
        print(f"Error creating sample: {e}")
    
    # Test 4: If user wants full generation (optional)
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        print("\n" + "="*60)
        print("TEST 4: Full generation (this will take time and space!)")
        
        full_output = f"{test_dir}/all_13mers.txt"
        
        # Warning
        print("WARNING: This will generate ~67M k-mers and take significant time and disk space!")
        response = input("Continue? (y/N): ").strip().lower()
        
        if response == 'y':
            if run_command(f"{exe_path} {full_output}", "Full 13-mer generation"):
                check_file_info(full_output)
            
            # Test with indices
            full_indexed = f"{test_dir}/all_13mers_indexed.txt"
            if run_command(f"{exe_path} {full_indexed} -i", "Full generation with indices"):
                check_file_info(full_indexed)
                
            # Binary format
            full_binary = f"{test_dir}/all_13mers"
            if run_command(f"{exe_path} {full_binary} -b", "Full generation binary format"):
                check_file_info(full_binary + ".bin")
        else:
            print("Skipping full generation")
    else:
        print("\nNote: Use '--full' argument to test complete generation of all 67M k-mers")
    
    print("\n" + "="*60)
    print("Testing completed!")
    print(f"Test files are in: {test_dir}/")
    
    # Show general information
    if os.path.exists(test_dir):
        total_size = sum(os.path.getsize(os.path.join(test_dir, f)) 
                        for f in os.listdir(test_dir) 
                        if os.path.isfile(os.path.join(test_dir, f)))
        print(f"Total test files size: {total_size:,} bytes ({total_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    main()
