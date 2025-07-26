#!/usr/bin/env python3
"""
Unit tests for the Brain Execution Server Queue Processor
"""

import json
import os
import sys
import tempfile
import subprocess
import time
import shutil
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import QueueProcessor


class TestQueueProcessor(unittest.TestCase):
    """Test cases for the Queue Processor"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for testing
        self.test_base = Path(tempfile.mkdtemp())
        self.test_pending = self.test_base / 'pending'
        self.test_completed = self.test_base / 'completed'
        self.test_failed = self.test_base / 'failed'
        self.test_log = self.test_base / 'daemon.log'
        
        # Create directories
        for dir in [self.test_pending, self.test_completed, self.test_failed]:
            dir.mkdir(parents=True, exist_ok=True)
        
        # Patch the queue directories in the module
        self.patches = [
            patch('server.QUEUE_BASE', self.test_base),
            patch('server.PENDING_DIR', self.test_pending),
            patch('server.COMPLETED_DIR', self.test_completed),
            patch('server.FAILED_DIR', self.test_failed),
            patch('server.LOG_FILE', self.test_log)
        ]
        
        for p in self.patches:
            p.start()
        
        self.processor = QueueProcessor()
    
    def tearDown(self):
        """Clean up test environment"""
        # Stop all patches
        for p in self.patches:
            p.stop()
        
        # Remove test directories
        shutil.rmtree(self.test_base)
    
    def test_json_job_simple_command(self):
        """Test processing a simple JSON job"""
        # Create a test job
        job_data = {
            "command": "echo",
            "args": ["Hello, World!"],
            "description": "Test echo command"
        }
        job_file = self.test_pending / 'test_echo.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Check results
        self.assertFalse(job_file.exists(), "Job file should be removed from pending")
        
        completed_file = self.test_completed / 'test_echo.json'
        self.assertTrue(completed_file.exists(), "Job should be in completed directory")
        
        # Check job results
        with open(completed_file) as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['result']['status'], 'completed')
        self.assertEqual(result_data['result']['returncode'], 0)
        self.assertIn('Hello, World!', result_data['result']['stdout'])
    
    def test_json_job_with_error(self):
        """Test processing a JSON job that fails"""
        # Create a job that will fail
        job_data = {
            "command": "false",
            "args": [],
            "description": "Test failing command"
        }
        job_file = self.test_pending / 'test_fail.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Check results
        self.assertFalse(job_file.exists(), "Job file should be removed from pending")
        
        failed_file = self.test_failed / 'test_fail.json'
        self.assertTrue(failed_file.exists(), "Job should be in failed directory")
        
        # Check job results
        with open(failed_file) as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['result']['status'], 'failed')
        self.assertNotEqual(result_data['result']['returncode'], 0)
    
    def test_text_job_processing(self):
        """Test processing a text file job"""
        # Create a text job
        job_file = self.test_pending / 'test_date.txt'
        with open(job_file, 'w') as f:
            f.write('date && echo "Test complete"')
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Check results
        self.assertFalse(job_file.exists(), "Job file should be removed from pending")
        
        result_file = self.test_completed / 'test_date_result.json'
        self.assertTrue(result_file.exists(), "Result should be in completed directory")
        
        # Check job results
        with open(result_file) as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['result']['status'], 'completed')
        self.assertEqual(result_data['result']['returncode'], 0)
        self.assertIn('Test complete', result_data['result']['stdout'])
    
    def test_python_execution(self):
        """Test Python code execution"""
        # Create a Python execution job
        job_data = {
            "command": "python3",
            "args": ["-c", "print('Python test'); print(2+2)"],
            "description": "Test Python execution"
        }
        job_file = self.test_pending / 'test_python.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Check results
        completed_file = self.test_completed / 'test_python.json'
        self.assertTrue(completed_file.exists(), "Job should be completed")
        
        with open(completed_file) as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['result']['status'], 'completed')
        self.assertIn('Python test', result_data['result']['stdout'])
        self.assertIn('4', result_data['result']['stdout'])
    
    def test_result_file_creation(self):
        """Test creation of result files"""
        # Create a job with result_file specified
        job_data = {
            "command": "echo",
            "args": ["Result file content"],
            "description": "Test result file",
            "result_file": "test_output.txt"
        }
        job_file = self.test_pending / 'test_result_file.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Check that result file was created
        result_file = self.test_base / 'test_output.txt'
        self.assertTrue(result_file.exists(), "Result file should be created")
        
        with open(result_file) as f:
            content = f.read()
        self.assertIn('Result file content', content)
    
    def test_timeout_handling(self):
        """Test timeout handling (mocked for speed)"""
        # Create a job that would timeout
        job_data = {
            "command": "sleep",
            "args": ["10"],
            "description": "Test timeout"
        }
        job_file = self.test_pending / 'test_timeout.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Mock subprocess to simulate timeout
        with patch('subprocess.Popen') as mock_popen:
            mock_process = MagicMock()
            mock_process.communicate.side_effect = subprocess.TimeoutExpired('cmd', 5)
            mock_popen.return_value = mock_process
            
            # Process the job
            self.processor.process_job(job_file)
        
        # Check that job failed due to timeout
        failed_file = self.test_failed / 'test_timeout.json'
        self.assertTrue(failed_file.exists(), "Job should be in failed directory")
        
        with open(failed_file) as f:
            result_data = json.load(f)
        
        self.assertEqual(result_data['result']['status'], 'failed')
        self.assertIn('Timeout', result_data['result']['error'])
    
    def test_logging(self):
        """Test logging functionality"""
        # Test logging
        self.processor.log("Test message", "INFO")
        self.processor.log("Test error", "ERROR")
        
        # Check log file
        self.assertTrue(self.test_log.exists(), "Log file should exist")
        
        with open(self.test_log) as f:
            log_content = f.read()
        
        self.assertIn("[INFO] Test message", log_content)
        self.assertIn("[ERROR] Test error", log_content)
    
    def test_invalid_job_format(self):
        """Test handling of invalid job formats"""
        # Create a job with no command
        job_data = {
            "description": "Invalid job - no command"
        }
        job_file = self.test_pending / 'test_invalid.json'
        with open(job_file, 'w') as f:
            json.dump(job_data, f)
        
        # Process the job
        self.processor.process_job(job_file)
        
        # Should be moved to failed
        failed_file = self.test_failed / 'test_invalid.json'
        self.assertTrue(failed_file.exists(), "Invalid job should be in failed directory")
    
    def test_stop_signal(self):
        """Test graceful shutdown"""
        # Test stop signal handling
        self.processor.stop()
        self.assertFalse(self.processor.running, "Processor should stop running")


class TestIntegration(unittest.TestCase):
    """Integration tests for the queue processor"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_base = Path(tempfile.mkdtemp())
        self.patches = [
            patch('server.QUEUE_BASE', self.test_base),
            patch('server.PENDING_DIR', self.test_base / 'pending'),
            patch('server.COMPLETED_DIR', self.test_base / 'completed'),
            patch('server.FAILED_DIR', self.test_base / 'failed'),
            patch('server.LOG_FILE', self.test_base / 'daemon.log')
        ]
        
        for p in self.patches:
            p.start()
    
    def tearDown(self):
        """Clean up"""
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.test_base)
    
    def test_multiple_job_processing(self):
        """Test processing multiple jobs in sequence"""
        processor = QueueProcessor()
        
        # Create directories
        for dir in ['pending', 'completed', 'failed']:
            (self.test_base / dir).mkdir(parents=True, exist_ok=True)
        
        # Create multiple jobs
        jobs = [
            {"command": "echo", "args": ["Job 1"]},
            {"command": "echo", "args": ["Job 2"]},
            {"command": "echo", "args": ["Job 3"]}
        ]
        
        for i, job_data in enumerate(jobs):
            job_file = self.test_base / 'pending' / f'job_{i}.json'
            with open(job_file, 'w') as f:
                json.dump(job_data, f)
        
        # Process all jobs
        for job_file in sorted((self.test_base / 'pending').iterdir()):
            processor.process_job(job_file)
        
        # Check all jobs completed
        completed_files = list((self.test_base / 'completed').iterdir())
        self.assertEqual(len(completed_files), 3, "All jobs should be completed")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
