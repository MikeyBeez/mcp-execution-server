/bin/bash
# Test script for the queue processor

echo "Testing Brain Execution Server Queue Processor..."

# Create test jobs
echo "Creating test jobs..."

# Test 1: Simple command
cat > /Users/bard/mcp/memory_files/command_queue/pending/test_echo.json << EOF
{
  "command": "echo",
  "args": ["Queue processor is working!"],
  "description": "Test echo command"
}
EOF

# Test 2: Check Python
cat > /Users/bard/mcp/memory_files/command_queue/pending/test_python.json << EOF
{
  "command": "python3",
  "args": ["-c", "print('Python execution works!')"],
  "description": "Test Python execution"
}
EOF

# Test 3: Text file job
echo 'date && echo "Text file execution works!"' > /Users/bard/mcp/memory_files/command_queue/pending/test_date.txt

echo "Created 3 test jobs in pending queue"
echo ""
echo "Start the server with: python3 server.py"
echo "Monitor with: python3 /Users/bard/mcp/memory_files/command_queue/queue_viewer.py"
