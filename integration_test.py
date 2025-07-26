#!/usr/bin/env python3
"""
Integration test for the MCP Execution Server
Tests the actual queue system with the running service
"""

import json
import time
import sys
from pathlib import Path

# Queue paths
QUEUE_BASE = Path('/Users/bard/mcp/memory_files/command_queue')
PENDING_DIR = QUEUE_BASE / 'pending'
COMPLETED_DIR = QUEUE_BASE / 'completed'
FAILED_DIR = QUEUE_BASE / 'failed'

def test_service_running():
    """Check if the service is running"""
    print("1. Checking if service is running...")
    import subprocess
    result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True)
    if 'com.brain.execution-server' in result.stdout:
        print("   ✅ Service is loaded in launchctl")
        return True
    else:
        print("   ❌ Service not found in launchctl")
        return False

def test_simple_job():
    """Test a simple echo job"""
    print("\n2. Testing simple echo job...")
    
    job_data = {
        "command": "echo",
        "args": ["Integration test successful!"],
        "description": "Integration test echo"
    }
    
    job_file = PENDING_DIR / 'integration_test_echo.json'
    
    # Write job
    with open(job_file, 'w') as f:
        json.dump(job_data, f)
    print(f"   Created job: {job_file}")
    
    # Wait for processing
    print("   Waiting for job to process...")
    for i in range(10):  # Wait up to 10 seconds
        if not job_file.exists():
            break
        time.sleep(1)
    
    # Check result
    result_file = COMPLETED_DIR / 'integration_test_echo.json'
    if result_file.exists():
        with open(result_file) as f:
            result = json.load(f)
        if result['result']['status'] == 'completed':
            print(f"   ✅ Job completed successfully")
            print(f"   Output: {result['result']['stdout'].strip()}")
            result_file.unlink()  # Clean up
            return True
        else:
            print(f"   ❌ Job failed: {result}")
            return False
    else:
        print("   ❌ Job result not found")
        return False

def test_python_job():
    """Test Python execution"""
    print("\n3. Testing Python execution...")
    
    job_data = {
        "command": "python3",
        "args": ["-c", "import sys; print(f'Python {sys.version.split()[0]} is working')"],
        "description": "Integration test Python"
    }
    
    job_file = PENDING_DIR / 'integration_test_python.json'
    
    # Write job
    with open(job_file, 'w') as f:
        json.dump(job_data, f)
    print(f"   Created job: {job_file}")
    
    # Wait for processing
    print("   Waiting for job to process...")
    for i in range(10):
        if not job_file.exists():
            break
        time.sleep(1)
    
    # Check result
    result_file = COMPLETED_DIR / 'integration_test_python.json'
    if result_file.exists():
        with open(result_file) as f:
            result = json.load(f)
        if result['result']['status'] == 'completed':
            print(f"   ✅ Python execution successful")
            print(f"   Output: {result['result']['stdout'].strip()}")
            result_file.unlink()  # Clean up
            return True
        else:
            print(f"   ❌ Python execution failed")
            return False
    else:
        print("   ❌ Result not found")
        return False

def test_text_job():
    """Test text file job"""
    print("\n4. Testing text file job...")
    
    job_file = PENDING_DIR / 'integration_test_text.txt'
    
    # Write job
    with open(job_file, 'w') as f:
        f.write('echo "Text job works!" && date')
    print(f"   Created job: {job_file}")
    
    # Wait for processing
    print("   Waiting for job to process...")
    for i in range(10):
        if not job_file.exists():
            break
        time.sleep(1)
    
    # Check result
    result_file = COMPLETED_DIR / 'integration_test_text_result.json'
    if result_file.exists():
        with open(result_file) as f:
            result = json.load(f)
        if result['result']['status'] == 'completed':
            print(f"   ✅ Text job completed successfully")
            print(f"   Output preview: {result['result']['stdout'][:50]}...")
            result_file.unlink()  # Clean up
            return True
        else:
            print(f"   ❌ Text job failed")
            return False
    else:
        print("   ❌ Result not found")
        return False

def test_failing_job():
    """Test that failing jobs are handled correctly"""
    print("\n5. Testing failing job handling...")
    
    job_data = {
        "command": "false",
        "description": "Integration test - intentional failure"
    }
    
    job_file = PENDING_DIR / 'integration_test_fail.json'
    
    # Write job
    with open(job_file, 'w') as f:
        json.dump(job_data, f)
    print(f"   Created failing job: {job_file}")
    
    # Wait for processing
    print("   Waiting for job to process...")
    for i in range(10):
        if not job_file.exists():
            break
        time.sleep(1)
    
    # Check result in failed directory
    result_file = FAILED_DIR / 'integration_test_fail.json'
    if result_file.exists():
        with open(result_file) as f:
            result = json.load(f)
        if result['result']['status'] == 'failed':
            print(f"   ✅ Failing job handled correctly")
            result_file.unlink()  # Clean up
            return True
        else:
            print(f"   ❌ Unexpected result: {result}")
            return False
    else:
        print("   ❌ Failed job not in failed directory")
        return False

def main():
    """Run all integration tests"""
    print("🧪 MCP Execution Server Integration Tests")
    print("=" * 50)
    
    tests = [
        test_service_running,
        test_simple_job,
        test_python_job,
        test_text_job,
        test_failing_job
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
