#!/bin/bash
# Test the execution server

echo "🧪 Testing Brain Execution Server..."

# Test if server is running
if ! curl -s http://localhost:9998/ > /dev/null 2>&1; then
    echo "❌ Server not running on port 9998"
    echo "Start it with: cd /Users/bard/Code/mcp-execution-server && python3 server.py"
    exit 1
fi

echo "✅ Server is running"

# Test Python execution
echo -e "\n📐 Testing Python execution..."
PYTHON_RESULT=$(curl -s -X POST http://localhost:9998/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello from Python!\")\nprint(2 + 2)", "language": "python"}')

echo "Python result: $PYTHON_RESULT"

# Test Shell execution
echo -e "\n🐚 Testing Shell execution..."
SHELL_RESULT=$(curl -s -X POST http://localhost:9998/execute \
  -H "Content-Type: application/json" \
  -d '{"code": "echo Hello from Shell && date", "language": "shell"}')

echo "Shell result: $SHELL_RESULT"

echo -e "\n✨ All tests complete!"
