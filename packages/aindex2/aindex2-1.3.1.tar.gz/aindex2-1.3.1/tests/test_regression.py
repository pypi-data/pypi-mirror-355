#!/usr/bin/env python3
"""
Regression tests for aindex pipelines.

These tests verify that both jellyfish and kmer_counter pipelines produce
consistent, expected results on test data.

Usage:
    python test_regression.py [--skip-jellyfish]
    
Options:
    --skip-jellyfish: Skip jellyfish tests (saves time)
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path

# Add parent directory to path to import aindex
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

def get_file_stats(filepath):
    """Get basic file statistics."""
    if not os.path.exists(filepath):
        return None
    
    stats = {
        'exists': True,
        'size': os.path.getsize(filepath),
        'lines': 0
    }
    
    # Count lines for text files
    try:
        with open(filepath, 'r') as f:
            stats['lines'] = sum(1 for line in f)
    except:
        # Binary file or encoding issue
        pass
    
    return stats

def test_pipeline(pipeline_name, use_kmer_counter=False, test_dir=None):
    """Test a specific pipeline and return results."""
    if test_dir is None:
        test_dir = Path(__file__).parent
    
    # Input data from tests/data
    data_dir = test_dir / "data"
    fastq1 = data_dir / "raw_reads.101bp.IS350bp25_1.fastq"
    fastq2 = data_dir / "raw_reads.101bp.IS350bp25_2.fastq"
    
    if not fastq1.exists() or not fastq2.exists():
        raise FileNotFoundError(f"Test FASTQ files not found: {fastq1}, {fastq2}")
    
    # Output to tests/temp
    temp_dir = test_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    output_prefix = temp_dir / f"test_{pipeline_name}"
    
    # Build command - add path to binary executables
    cmd = f"python3 ../scripts/compute_aindex.py -i {fastq1},{fastq2} -t fastq -o {output_prefix} --lu 2 -P 4 --path_to_aindex ../bin/"
    if use_kmer_counter:
        cmd += " --use_kmer_counter"
    
    # Run pipeline
    result = run_command(cmd, check=False)
    
    # Collect results
    test_results = {
        'pipeline': pipeline_name,
        'command': cmd,
        'success': result.returncode == 0,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'files': {}
    }
    
    # Check expected output files
    expected_files = ['.reads', '.ridx', '.23.pf', '.23.tf.bin', '.23.kmers.bin', '.23.index.bin', '.23.indices.bin', '.23.pos.bin']
    for ext in expected_files:
        filepath = str(output_prefix) + ext
        test_results['files'][ext] = get_file_stats(filepath)
    
    # Try to load Python API if successful
    if test_results['success']:
        try:
            import aindex
            # Use load_index_with_reads to load all files
            # Need to construct paths to all the files that should exist
            hash_file = str(output_prefix) + ".23.index.bin"  # This might not exist due to compute_aindex.exe crash
            tf_file = str(output_prefix) + ".23.tf.bin"
            kmers_bin_file = str(output_prefix) + ".23.kmers.bin"
            kmers_text_file = str(output_prefix) + ".23.kmers"  # This file gets deleted by script
            reads_file = str(output_prefix) + ".reads"
            aindex_file = str(output_prefix) + ".23.indices.bin"  # or .23.pos.bin depending on expected name
            
            # Check if required files exist for full loading
            required_files = [hash_file, tf_file, kmers_bin_file, reads_file, aindex_file]
            existing_files = [f for f in required_files if os.path.exists(f)]
            missing_files = [f for f in required_files if not os.path.exists(f)]
            
            if len(existing_files) >= 3:  # At least hash, tf, and kmers_bin
                try:
                    # Try to load with all files first
                    if len(missing_files) == 0:
                        index = aindex.load_index_with_reads(hash_file, tf_file, kmers_bin_file, 
                                                           kmers_text_file, reads_file, aindex_file)
                    else:
                        # Fall back to basic index loading if some files missing
                        index = aindex.load_index(hash_file, tf_file, kmers_bin_file, kmers_text_file)
                    
                    # Test basic API functionality
                    test_kmer = "AAAAAAAAAAAAAAAAAAAAAA"  # 22-mer of A's
                    api_results = {
                        'n_kmers': index.n_kmers,
                        'aindex_loaded': index.aindex_loaded,
                        'test_kmer_freq': index.get_tf_value(test_kmer),
                        'existing_files': len(existing_files),
                        'missing_files': len(missing_files),
                    }
                    test_results['api'] = api_results
                except Exception as load_error:
                    test_results['api_error'] = f"Loading failed: {str(load_error)}, missing: {missing_files}"
            else:
                test_results['api_error'] = f"Too many required files missing: {missing_files}"
            
        except Exception as e:
            test_results['api_error'] = str(e)
    
    return test_results

def main():
    """Run regression tests for both pipelines."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run aindex regression tests')
    parser.add_argument('--skip-jellyfish', action='store_true', 
                       help='Skip jellyfish tests (saves time)')
    args = parser.parse_args()
    
    test_dir = Path(__file__).parent
    
    print("Running aindex regression tests...")
    if args.skip_jellyfish:
        print("(Skipping jellyfish tests for speed)")
    print("=" * 50)
    
    # Test both pipelines
    results = {}
    
    # Test kmer_counter pipeline
    print("\nTesting kmer_counter pipeline...")
    try:
        results['kmer_counter'] = test_pipeline('kmer_counter', use_kmer_counter=True, test_dir=test_dir)
        print("✓ kmer_counter pipeline completed")
    except Exception as e:
        print(f"✗ kmer_counter pipeline failed: {e}")
        results['kmer_counter'] = {'error': str(e)}
    
    # Test jellyfish pipeline (if not skipped and available)
    if args.skip_jellyfish:
        print("\nSkipping jellyfish pipeline (--skip-jellyfish flag)")
        results['jellyfish'] = {'skipped': 'skipped by user flag'}
    else:
        print("\nTesting jellyfish pipeline...")
        try:
            # Check if jellyfish is available
            jellyfish_check = run_command("which jellyfish", check=False)
            if jellyfish_check.returncode != 0:
                print("⚠ jellyfish not found, skipping jellyfish tests")
                results['jellyfish'] = {'skipped': 'jellyfish not available'}
            else:
                results['jellyfish'] = test_pipeline('jellyfish', use_kmer_counter=False, test_dir=test_dir)
                print("✓ jellyfish pipeline completed")
        except Exception as e:
            print(f"✗ jellyfish pipeline failed: {e}")
            results['jellyfish'] = {'error': str(e)}
    
    # Compare results if both pipelines succeeded
    print("\n" + "=" * 50)
    print("RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    
    for pipeline, result in results.items():
        if 'error' in result:
            print(f"✗ {pipeline}: FAILED - {result['error']}")
            all_passed = False
        elif 'skipped' in result:
            print(f"⚠ {pipeline}: SKIPPED - {result['skipped']}")
        elif result.get('success', False):
            print(f"✓ {pipeline}: PASSED")
            
            # Print file statistics  
            files = result.get('files', {})
            for ext, stats in files.items():
                if stats and stats['exists']:
                    print(f"  {ext}: {stats['size']} bytes, {stats.get('lines', 'N/A')} lines")
                else:
                    print(f"  {ext}: MISSING")
                    all_passed = False
            
            # Print API results
            api = result.get('api', {})
            if api:
                print(f"  API - n_kmers: {api.get('n_kmers', 'N/A')}")
                print(f"  API - test_kmer_freq: {api.get('test_kmer_freq', 'N/A')}")
                print(f"  API - aindex_loaded: {api.get('aindex_loaded', 'N/A')}")
        else:
            print(f"✗ {pipeline}: FAILED")
            all_passed = False
    
    # Compare outputs between pipelines (only if both succeeded)
    if ('kmer_counter' in results and 'jellyfish' in results and
        not results['jellyfish'].get('skipped') and
        results['kmer_counter'].get('success') and 
        results['jellyfish'].get('success')):
        
        print("\nPIPELINE COMPARISON:")
        kc_files = results['kmer_counter'].get('files', {})
        jf_files = results['jellyfish'].get('files', {})
        
        for ext in ['.reads', '.ridx', '.23.pf', '.23.tf.bin', '.23.kmers.bin']:
                kc_stats = kc_files.get(ext, {})
                jf_stats = jf_files.get(ext, {})
                
                if kc_stats and jf_stats:
                    if kc_stats.get('size') == jf_stats.get('size'):
                        print(f"✓ {ext}: sizes match ({kc_stats['size']} bytes)")
                    else:
                        print(f"✗ {ext}: size mismatch (kmer_counter: {kc_stats.get('size')}, jellyfish: {jf_stats.get('size')})")
                        all_passed = False
    
    # Save detailed results to JSON in tests/temp
    temp_dir = test_dir / "temp"
    temp_dir.mkdir(exist_ok=True) 
    results_file = temp_dir / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")
    
    print("\n" + "=" * 50)
    if all_passed:
        if args.skip_jellyfish:
            print("✓ ALL TESTS PASSED (jellyfish tests skipped)")
        else:
            print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
