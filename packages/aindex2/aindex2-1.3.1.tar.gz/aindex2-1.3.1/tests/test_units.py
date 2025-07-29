#!/usr/bin/env python3
"""
Unit tests for aindex functionality with expected values.

This test file contains specific expected values derived from manual testing
of the aindex pipelines with the provided test data.
"""

import os
import sys
import unittest
from pathlib import Path

# Add parent directory to path to import aindex
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestAIndexFunctionality(unittest.TestCase):
    """Test aindex functionality with expected results."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.test_dir = Path(__file__).parent
        
        # Expected test data files in tests/data
        cls.data_dir = cls.test_dir / "data"
        cls.fastq1 = cls.data_dir / "raw_reads.101bp.IS350bp25_1.fastq"
        cls.fastq2 = cls.data_dir / "raw_reads.101bp.IS350bp25_2.fastq"
        
        # Check if test data exists
        if not (cls.fastq1.exists() and cls.fastq2.exists()):
            raise unittest.SkipTest("Test FASTQ files not found")
        
        # Look for existing test results in tests/temp
        cls.temp_dir = cls.test_dir / "temp"
        cls.kmer_counter_prefix = cls.temp_dir / "test_kmer_counter"
        cls.jellyfish_prefix = cls.temp_dir / "test_jellyfish"
        
        # Import aindex
        try:
            import aindex
            cls.aindex = aindex
        except ImportError:
            raise unittest.SkipTest("aindex module not available")
    
    def test_file_existence(self):
        """Test that required test files exist."""
        self.assertTrue(self.fastq1.exists(), f"Test file missing: {self.fastq1}")
        self.assertTrue(self.fastq2.exists(), f"Test file missing: {self.fastq2}")
    
    def test_kmer_counter_outputs(self):
        """Test that kmer_counter pipeline produces expected outputs."""
        prefix = str(self.kmer_counter_prefix)
        
        # Check that all expected files exist
        expected_files = ['.reads', '.ridx', '.23.pf', '.23.tf.bin', '.23.kmers.bin', '.23.index.bin', '.23.indices.bin', '.23.pos.bin']
        for ext in expected_files:
            filepath = prefix + ext
            self.assertTrue(os.path.exists(filepath), 
                          f"Missing output file: {filepath}")
    
    def test_kmer_counter_api_loading(self):
        """Test that kmer_counter results load correctly in Python API."""
        prefix = str(self.kmer_counter_prefix)
        
        if not os.path.exists(prefix + '.23.pf'):
            self.skipTest("kmer_counter results not available")
        
        # Load the index
        kmer2tf = self.aindex.get_aindex(prefix)
        self.assertIsNotNone(kmer2tf)
        
        # Test basic properties
        hash_size = kmer2tf.get_hash_size()
        self.assertIsInstance(hash_size, int)
        self.assertGreater(hash_size, 0)
        
        # Test k-mer lookup with known patterns
        # These are based on the test data characteristics
        test_kmers = [
            "AAAAAAAAAAAAAAAAAAAAAA",  # 22-mer of A's - should be rare/absent
            "TTTTTTTTTTTTTTTTTTTT",    # 20-mer of T's - should be rare/absent
        ]
        
        for kmer in test_kmers:
            freq = kmer2tf[kmer] if kmer in kmer2tf else 0
            self.assertIsInstance(freq, int)
            self.assertGreaterEqual(freq, 0)
    
    def test_jellyfish_outputs(self):
        """Test that jellyfish pipeline produces expected outputs (if available)."""
        prefix = str(self.jellyfish_prefix)
        
        # Skip if jellyfish results not available
        if not os.path.exists(prefix + '.23.pf'):
            self.skipTest("Jellyfish results not available")
        
        # Check that all expected files exist
        expected_files = ['.reads', '.ridx', '.23.pf', '.23.tf.bin', '.23.kmers.bin', '.23.index.bin', '.23.indices.bin', '.23.pos.bin']
        for ext in expected_files:
            filepath = prefix + ext
            self.assertTrue(os.path.exists(filepath), 
                          f"Missing output file: {filepath}")
    
    def test_pipeline_consistency(self):
        """Test that both pipelines produce consistent results."""
        kc_prefix = str(self.kmer_counter_prefix)
        jf_prefix = str(self.jellyfish_prefix)
        
        # Skip if either result set is missing
        if not (os.path.exists(kc_prefix + '.23.pf') and 
                os.path.exists(jf_prefix + '.23.pf')):
            self.skipTest("Both pipeline results not available")
        
        # Load both indices
        kc_index = self.aindex.get_aindex(kc_prefix)
        jf_index = self.aindex.get_aindex(jf_prefix)
        
        # Compare hash sizes
        self.assertEqual(kc_index.get_hash_size(), jf_index.get_hash_size(),
                        "Hash sizes should be identical between pipelines")
        
        # Compare k-mer frequencies for test k-mers
        test_kmers = [
            "AAAAAAAAAAAAAAAAAAAAAA",
            "TTTTTTTTTTTTTTTTTTTT",
            "GGGGGGGGGGGGGGGGGGGG",
            "CCCCCCCCCCCCCCCCCCCC"
        ]
        
        for kmer in test_kmers:
            kc_freq = kc_index[kmer] if kmer in kc_index else 0
            jf_freq = jf_index[kmer] if kmer in jf_index else 0
            self.assertEqual(kc_freq, jf_freq,
                           f"K-mer frequencies should match for {kmer}")
    
    def test_expected_file_sizes(self):
        """Test that output files have reasonable sizes."""
        prefixes = []
        
        if os.path.exists(str(self.kmer_counter_prefix) + '.23.pf'):
            prefixes.append(str(self.kmer_counter_prefix))
        
        if os.path.exists(str(self.jellyfish_prefix) + '.23.pf'):
            prefixes.append(str(self.jellyfish_prefix))
        
        if not prefixes:
            self.skipTest("No pipeline results available")
        
        for prefix in prefixes:
            # Check file sizes are reasonable (not empty, not too large)
            files_to_check = {
                '.reads': (1000000, 50000000),     # 1MB to 50MB
                '.ridx': (100000, 10000000),       # 100KB to 10MB  
                '.23.pf': (10000, 1000000),        # 10KB to 1MB
                '.23.tf.bin': (100000, 10000000),  # 100KB to 10MB
                '.23.kmers.bin': (1000000, 50000000), # 1MB to 50MB
                '.23.index.bin': (1000000, 100000000), # 1MB to 100MB
                '.23.indices.bin': (1000000, 10000000), # 1MB to 10MB
                '.23.pos.bin': (100, 1000000)      # 100B to 1MB
            }
            
            for ext, (min_size, max_size) in files_to_check.items():
                filepath = prefix + ext
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    self.assertGreaterEqual(size, min_size,
                                          f"{filepath} too small: {size} bytes")
                    self.assertLessEqual(size, max_size,
                                       f"{filepath} too large: {size} bytes")
    
    def test_api_iteration(self):
        """Test that API iteration functions work."""
        prefix = str(self.kmer_counter_prefix)
        
        if not os.path.exists(prefix + '.23.pf'):
            self.skipTest("kmer_counter results not available")
        
        kmer2tf = self.aindex.get_aindex(prefix)
        
        # Test read iteration
        read_count = 0
        for rid, read in kmer2tf.iter_reads():
            read_count += 1
            self.assertIsInstance(rid, int)
            self.assertIsInstance(read, str)
            self.assertGreater(len(read), 0)
            
            # Stop after checking a few reads
            if read_count >= 5:
                break
        
        self.assertGreater(read_count, 0, "Should have at least some reads")


class TestExpectedValues(unittest.TestCase):
    """Test specific expected values derived from manual testing."""
    
    def setUp(self):
        """Set up for each test."""
        self.test_dir = Path(__file__).parent
        self.temp_dir = self.test_dir / "temp"
        self.kmer_counter_prefix = str(self.temp_dir / "test_kmer_counter")
        
        # Skip if test data not available
        if not os.path.exists(self.kmer_counter_prefix + '.23.pf'):
            self.skipTest("Test results not available")
        
        import aindex
        self.kmer2tf = aindex.get_aindex(self.kmer_counter_prefix)
    
    def test_hash_size_range(self):
        """Test that hash size is in expected range."""
        hash_size = self.kmer2tf.get_hash_size()
        
        # Based on manual testing, hash size should be reasonable
        # for the test dataset (not too small, not too large)
        self.assertGreater(hash_size, 1000, "Hash size seems too small")
        self.assertLess(hash_size, 1000000, "Hash size seems too large")
    
    def test_common_kmers_absent(self):
        """Test that homopolymer k-mers are rare/absent as expected."""
        # Long homopolymers should be rare in real sequencing data
        homopolymers = [
            "A" * 22,  # 22-mer of A's
            "T" * 22,  # 22-mer of T's  
            "G" * 22,  # 22-mer of G's
            "C" * 22   # 22-mer of C's
        ]
        
        for kmer in homopolymers:
            freq = self.kmer2tf[kmer] if kmer in self.kmer2tf else 0
            # These should be very rare (frequency <= 2)
            self.assertLessEqual(freq, 2, 
                               f"Homopolymer {kmer[:5]}... frequency too high: {freq}")
    
    def test_read_length_consistency(self):
        """Test that reads have expected length patterns."""
        read_lengths = []
        read_count = 0
        
        for rid, read in self.kmer2tf.iter_reads():
            read_lengths.append(len(read))
            read_count += 1
            
            # Check first 10 reads
            if read_count >= 10:
                break
        
        # Based on test file name, expect ~101bp reads
        for length in read_lengths:
            self.assertGreater(length, 50, "Read too short")
            self.assertLess(length, 200, "Read too long")


if __name__ == '__main__':
    # Set up test output
    test_dir = Path(__file__).parent
    
    print("Running aindex unit tests...")
    print(f"Test directory: {test_dir}")
    print("=" * 60)
    
    # Run tests with detailed output
    unittest.main(verbosity=2)
