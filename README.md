# Brain Execution Server

A queue-based execution server that monitors and processes jobs from the Brain MCP command queue.

## Features
- Monitors `/Users/bard/mcp/memory_files/command_queue/pending` for jobs
- Executes shell commands and Python scripts
- Supports both JSON and text file job formats
- Moves completed jobs to `completed/` or `failed/` directories
- 5-minute timeout for safety
- Logs all operations to `daemon.log`

## Job Formats

### JSON Format
```json
{
  "command": "which",
  "args": ["node"],
  "description": "Check if node is in PATH"
}
```

Or:
```json
{
  "task_id": "unique_id",
  "command": "python3 /path/to/script.py",
  "purpose": "Description of the job",
  "result_file": "optional_output.txt"
}
```

### Text Format
Plain text files (.txt or .sh) containing shell commands:
```
cd /path/to/dir && python script.py
```

## Installation & Usage

1. **Start the server:**
   ```bash
   cd /Users/bard/Code/mcp-execution-server
   python3 server.py
   ```

2. **Monitor the queue:**
   ```bash
   python3 /Users/bard/mcp/memory_files/command_queue/queue_viewer.py
   ```

3. **Add a job to the queue:**
   ```bash
   # JSON job
   echo '{"command": "echo", "args": ["Hello from queue!"]}' > /Users/bard/mcp/memory_files/command_queue/pending/test_job.json
   
   # Text job
   echo 'ls -la /Users/bard/Code' > /Users/bard/mcp/memory_files/command_queue/pending/list_code.txt
   ```

## Running in Background with LaunchControl

Create a launch agent to run the server automatically:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.brain.execution-server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/bard/Code/mcp-execution-server/server.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/bard/Code/mcp-execution-server</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/bard/mcp/memory_files/command_queue/server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/bard/mcp/memory_files/command_queue/server.error.log</string>
</dict>
</plist>
```

## Queue Directories

- **Pending**: `/Users/bard/mcp/memory_files/command_queue/pending/` - Jobs waiting to be processed
- **Completed**: `/Users/bard/mcp/memory_files/command_queue/completed/` - Successfully executed jobs
- **Failed**: `/Users/bard/mcp/memory_files/command_queue/failed/` - Jobs that failed or timed out
- **Logs**: `/Users/bard/mcp/memory_files/command_queue/daemon.log` - Server activity log

## Security Note

This server executes arbitrary code from the queue. Ensure proper permissions on the queue directories.
