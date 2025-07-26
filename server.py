#!/usr/bin/env python3
"""
Queue Processor for Brain MCP Execution Server
Monitors the command queue and executes pending jobs
"""

import json
import subprocess
import sys
import os
import time
import shutil
import traceback
from pathlib import Path
from datetime import datetime
import signal
import threading

# Queue directories
QUEUE_BASE = Path('/Users/bard/mcp/memory_files/command_queue')
PENDING_DIR = QUEUE_BASE / 'pending'
COMPLETED_DIR = QUEUE_BASE / 'completed'
FAILED_DIR = QUEUE_BASE / 'failed'
LOG_FILE = QUEUE_BASE / 'daemon.log'

class QueueProcessor:
    def __init__(self):
        self.running = True
        self.current_process = None
        
    def log(self, message, level='INFO'):
        """Log message to daemon.log"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} [{level}] {message}\n"
        print(log_entry.strip())
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)
    
    def stop(self, signum=None, frame=None):
        """Gracefully stop the processor"""
        self.log("Received stop signal, shutting down...")
        self.running = False
        if self.current_process:
            self.current_process.terminate()
    
    def process_json_job(self, job_file, data):
        """Process a JSON format job"""
        self.log(f"Processing JSON job: {job_file.name}")
        
        # Extract command and arguments
        if 'command' in data and 'args' in data:
            # Format: {"command": "which", "args": ["node"]}
            cmd = [data['command']] + data.get('args', [])
        elif 'command' in data:
            # Format: {"command": "python3 script.py"}
            cmd = data['command']
            if isinstance(cmd, str):
                cmd = cmd.split()
        else:
            raise ValueError("No command found in job file")
        
        # Execute the command
        self.log(f"Executing: {' '.join(cmd if isinstance(cmd, list) else [cmd])}")
        
        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=isinstance(cmd, str)
            )
            
            stdout, stderr = self.current_process.communicate(timeout=300)  # 5 minute timeout
            returncode = self.current_process.returncode
            
            # Update job data with results
            data['result'] = {
                'status': 'completed' if returncode == 0 else 'failed',
                'returncode': returncode,
                'stdout': stdout,
                'stderr': stderr,
                'completed_at': datetime.now().isoformat()
            }
            
            # Save result file if specified
            if 'result_file' in data and stdout:
                result_path = QUEUE_BASE / data['result_file']
                with open(result_path, 'w') as f:
                    f.write(stdout)
                self.log(f"Saved results to {result_path}")
            
            # Move to appropriate directory
            dest_dir = COMPLETED_DIR if returncode == 0 else FAILED_DIR
            dest_file = dest_dir / job_file.name
            
            # Write updated data
            with open(dest_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Remove original
            job_file.unlink()
            
            self.log(f"Job {job_file.name} {'completed' if returncode == 0 else 'failed'}")
            
        except subprocess.TimeoutExpired:
            self.current_process.kill()
            data['result'] = {
                'status': 'failed',
                'error': 'Timeout after 5 minutes',
                'completed_at': datetime.now().isoformat()
            }
            dest_file = FAILED_DIR / job_file.name
            with open(dest_file, 'w') as f:
                json.dump(data, f, indent=2)
            job_file.unlink()
            self.log(f"Job {job_file.name} timed out", 'ERROR')
            
        except Exception as e:
            data['result'] = {
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'completed_at': datetime.now().isoformat()
            }
            dest_file = FAILED_DIR / job_file.name
            with open(dest_file, 'w') as f:
                json.dump(data, f, indent=2)
            job_file.unlink()
            self.log(f"Job {job_file.name} failed: {str(e)}", 'ERROR')
        
        finally:
            self.current_process = None
    
    def process_text_job(self, job_file):
        """Process a text format job (shell command)"""
        self.log(f"Processing text job: {job_file.name}")
        
        try:
            # Read the command
            cmd = job_file.read_text().strip()
            self.log(f"Executing: {cmd}")
            
            # Execute the command
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            
            stdout, stderr = self.current_process.communicate(timeout=300)
            returncode = self.current_process.returncode
            
            # Create result JSON
            result_data = {
                'command': cmd,
                'source_file': job_file.name,
                'result': {
                    'status': 'completed' if returncode == 0 else 'failed',
                    'returncode': returncode,
                    'stdout': stdout,
                    'stderr': stderr,
                    'completed_at': datetime.now().isoformat()
                }
            }
            
            # Save result
            dest_dir = COMPLETED_DIR if returncode == 0 else FAILED_DIR
            result_file = dest_dir / f"{job_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            
            # Remove original
            job_file.unlink()
            
            self.log(f"Job {job_file.name} {'completed' if returncode == 0 else 'failed'}")
            
        except subprocess.TimeoutExpired:
            self.current_process.kill()
            result_data = {
                'command': cmd,
                'source_file': job_file.name,
                'result': {
                    'status': 'failed',
                    'error': 'Timeout after 5 minutes',
                    'completed_at': datetime.now().isoformat()
                }
            }
            result_file = FAILED_DIR / f"{job_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            job_file.unlink()
            self.log(f"Job {job_file.name} timed out", 'ERROR')
            
        except Exception as e:
            result_data = {
                'command': cmd if 'cmd' in locals() else 'unknown',
                'source_file': job_file.name,
                'result': {
                    'status': 'failed',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'completed_at': datetime.now().isoformat()
                }
            }
            result_file = FAILED_DIR / f"{job_file.stem}_result.json"
            with open(result_file, 'w') as f:
                json.dump(result_data, f, indent=2)
            job_file.unlink()
            self.log(f"Job {job_file.name} failed: {str(e)}", 'ERROR')
        
        finally:
            self.current_process = None
    
    def process_job(self, job_file):
        """Process a single job file"""
        try:
            if job_file.suffix == '.json':
                with open(job_file) as f:
                    data = json.load(f)
                self.process_json_job(job_file, data)
            elif job_file.suffix in ['.txt', '.sh']:
                self.process_text_job(job_file)
            else:
                self.log(f"Unknown job format: {job_file.name}", 'WARNING')
                
        except Exception as e:
            self.log(f"Error processing {job_file.name}: {str(e)}", 'ERROR')
            # Move to failed directory
            try:
                shutil.move(str(job_file), str(FAILED_DIR / job_file.name))
            except:
                pass
    
    def run(self):
        """Main processing loop"""
        self.log("Queue processor started")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        
        # Ensure directories exist
        for dir in [PENDING_DIR, COMPLETED_DIR, FAILED_DIR]:
            dir.mkdir(parents=True, exist_ok=True)
        
        while self.running:
            try:
                # Get all pending jobs
                jobs = sorted(PENDING_DIR.iterdir())
                
                if jobs:
                    # Skip directories
                    job_files = [j for j in jobs if j.is_file()]
                    if job_files:
                        # Process the oldest job
                        self.process_job(job_files[0])
                    else:
                        time.sleep(1)
                else:
                    # No jobs, wait a bit
                    time.sleep(2)
                    
            except Exception as e:
                self.log(f"Error in main loop: {str(e)}", 'ERROR')
                time.sleep(5)
        
        self.log("Queue processor stopped")

def main():
    """Run the queue processor"""
    processor = QueueProcessor()
    
    print("🚀 Brain Execution Queue Processor")
    print(f"📁 Monitoring: {PENDING_DIR}")
    print(f"📝 Log file: {LOG_FILE}")
    print("\nPress Ctrl+C to stop...\n")
    
    try:
        processor.run()
    except KeyboardInterrupt:
        print("\n✋ Processor stopped")

if __name__ == '__main__':
    main()
