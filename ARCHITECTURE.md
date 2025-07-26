# MCP Execution Server Architecture

## Overview

The MCP Execution Server is a queue-based job processor that executes commands submitted by other MCP tools and Brain components. It monitors a file-based queue system and processes jobs sequentially, providing a secure and controlled way to execute system commands.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Tools / Brain Components            │
│  (brain-manager, todo-manager, contemplation, etc.)         │
└───────────────────────┬─────────────────────────────────────┘
                        │ Submit Jobs (JSON/TXT files)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Queue Directory Structure                 │
│  /Users/bard/mcp/memory_files/command_queue/                │
│  ├── pending/      (incoming jobs)                          │
│  ├── completed/    (successful jobs with results)           │
│  ├── failed/       (failed jobs with error info)            │
│  └── daemon.log    (server activity log)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │ Monitor & Process
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Execution Server                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Queue Processor Loop                    │   │
│  │  1. Monitor pending/ directory                       │   │
│  │  2. Process oldest job first (FIFO)                  │   │
│  │  3. Execute command with timeout                     │   │
│  │  4. Capture stdout/stderr/return code               │   │
│  │  5. Move to completed/ or failed/                    │   │
│  │  6. Log all operations                               │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────┬─────────────────────────────────────┘
                        │ Managed by
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                        launchctl                             │
│  Service: com.brain.execution-server                         │
│  - Auto-start on boot                                       │
│  - Keep alive (restart if crashes)                          │
│  - Logs to server.log and server.error.log                  │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Queue Directory Structure

The server uses a file-based queue system located at `/Users/bard/mcp/memory_files/command_queue/`:

- **pending/**: Directory where new jobs are placed by MCP tools
- **completed/**: Successfully executed jobs with their results
- **failed/**: Failed jobs with error information
- **daemon.log**: Server activity log with timestamps

### 2. Job Formats

The server supports two job formats:

#### JSON Format
```json
{
  "command": "echo",
  "args": ["Hello, World!"],
  "description": "Test echo command",
  "result_file": "optional_output.txt"  // Optional
}
```

Alternative JSON format:
```json
{
  "task_id": "unique_id",
  "command": "python3 /path/to/script.py",
  "purpose": "Description of the job"
}
```

#### Text Format
Plain text files (`.txt` or `.sh`) containing shell commands:
```bash
cd /path/to/dir && python script.py
```

### 3. Queue Processor

The main server component (`server.py`) implements:

- **QueueProcessor class**: Main processing logic
- **process_job()**: Handles individual job execution
- **process_json_job()**: Processes JSON format jobs
- **process_text_job()**: Processes text format jobs
- **Timeout handling**: 5-minute timeout for all jobs
- **Signal handling**: Graceful shutdown on SIGINT/SIGTERM
- **Logging**: All operations logged with timestamps

### 4. Execution Flow

1. **Job Submission**: MCP tools write job files to `pending/`
2. **Detection**: Server monitors `pending/` directory every 2 seconds
3. **Processing**: Oldest job processed first (FIFO)
4. **Execution**: Command executed with subprocess
5. **Result Capture**: stdout, stderr, and return code captured
6. **Job Movement**: 
   - Success: Job moved to `completed/` with results
   - Failure: Job moved to `failed/` with error info
7. **Logging**: Operation logged to `daemon.log`

### 5. Result Format

Completed jobs are updated with result information:

```json
{
  "command": "echo",
  "args": ["Hello"],
  "description": "Test",
  "result": {
    "status": "completed",
    "returncode": 0,
    "stdout": "Hello\n",
    "stderr": "",
    "completed_at": "2025-07-26T13:42:20.076398"
  }
}
```

## Security Considerations

1. **No Network Access**: Server only processes local file-based jobs
2. **Timeout Protection**: 5-minute timeout prevents runaway processes
3. **Controlled Execution**: Only processes jobs from specific queue directory
4. **Signal Handling**: Graceful shutdown ensures no orphaned processes
5. **File Permissions**: Queue directories should have appropriate permissions

## Integration with MCP System

### How MCP Tools Submit Jobs

MCP tools can submit jobs by writing files to the pending queue:

```python
# Example from an MCP tool
import json

job = {
    "command": "python3",
    "args": ["-c", "print('Hello from MCP tool')"],
    "description": "Test from my tool"
}

with open("/Users/bard/mcp/memory_files/command_queue/pending/my_job.json", "w") as f:
    json.dump(job, f)
```

### Brain Integration

The Brain system uses the execution server for:
- Running Python scripts
- Executing system commands
- Background processing tasks
- Tool coordination

## Monitoring and Management

### Status Check
```bash
/Users/bard/Code/mcp-execution-server/status.sh
```

### View Queue
```bash
python3 /Users/bard/mcp/memory_files/command_queue/queue_viewer.py
```

### Service Management
```bash
# Stop service
launchctl unload ~/Library/LaunchAgents/com.brain.execution-server.plist

# Start service
launchctl load ~/Library/LaunchAgents/com.brain.execution-server.plist

# Check status
launchctl list | grep com.brain.execution-server
```

### Log Monitoring
```bash
# View recent activity
tail -f /Users/bard/mcp/memory_files/command_queue/daemon.log

# Check errors
tail -f /Users/bard/mcp/memory_files/command_queue/server.error.log
```

## Testing

The server includes comprehensive unit tests (`test_server.py`):

- JSON job processing
- Text file job processing
- Error handling
- Timeout handling
- Result file creation
- Logging functionality
- Multiple job processing
- Invalid job format handling

Run tests with:
```bash
cd /Users/bard/Code/mcp-execution-server
python3 test_server.py -v
```

## Future Enhancements

Potential improvements for future versions:

1. **Priority Queue**: Support for job priorities
2. **Parallel Processing**: Multiple worker processes
3. **Job Dependencies**: Support for job chains
4. **Resource Limits**: Memory and CPU limits per job
5. **Webhook Notifications**: Notify on job completion
6. **Web Dashboard**: Visual queue monitoring
7. **Job Scheduling**: Cron-like scheduling support
8. **Result Archiving**: Automatic cleanup of old results

## Troubleshooting

### Common Issues

1. **Jobs not processing**:
   - Check if service is running: `launchctl list | grep com.brain.execution-server`
   - Check logs: `tail -f /Users/bard/mcp/memory_files/command_queue/daemon.log`

2. **Permission errors**:
   - Ensure queue directories are writable
   - Check file ownership

3. **Timeout errors**:
   - Jobs taking >5 minutes will timeout
   - Consider breaking into smaller jobs

4. **Service won't start**:
   - Check error log: `server.error.log`
   - Verify Python path is correct
   - Check launchctl logs: `log show --predicate 'subsystem == "com.brain.execution-server"' --info`
