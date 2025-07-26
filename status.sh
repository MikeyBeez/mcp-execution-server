#!/bin/bash
# Status check for Brain Execution Server

echo "🧠 Brain Execution Server Status Check"
echo "======================================"
echo ""

# Check if service is loaded
echo "📊 Launchctl Status:"
if launchctl list | grep -q "com.brain.execution-server"; then
    launchctl list | grep "com.brain.execution-server"
    echo "✅ Service is loaded"
else
    echo "❌ Service is not loaded"
fi
echo ""

# Check if process is running
echo "🔄 Process Status:"
if pgrep -f "mcp-execution-server/server.py" > /dev/null; then
    echo "✅ Process is running"
    ps aux | grep "mcp-execution-server/server.py" | grep -v grep
else
    echo "❌ Process is not running"
fi
echo ""

# Check queue status
echo "📁 Queue Status:"
PENDING=$(ls -1 /Users/bard/mcp/memory_files/command_queue/pending/*.json 2>/dev/null | wc -l | tr -d ' ')
COMPLETED=$(ls -1 /Users/bard/mcp/memory_files/command_queue/completed/*.json 2>/dev/null | wc -l | tr -d ' ')
FAILED=$(ls -1 /Users/bard/mcp/memory_files/command_queue/failed/*.json 2>/dev/null | wc -l | tr -d ' ')

echo "   Pending:   $PENDING jobs"
echo "   Completed: $COMPLETED jobs"
echo "   Failed:    $FAILED jobs"
echo ""

# Show recent log entries
echo "📝 Recent Log Entries:"
tail -5 /Users/bard/mcp/memory_files/command_queue/daemon.log 2>/dev/null || echo "No log entries found"
