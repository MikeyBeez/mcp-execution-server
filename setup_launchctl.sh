#!/bin/bash
# Setup script for Brain Execution Server launchctl service

PLIST_NAME="com.brain.execution-server"
PLIST_FILE="/Users/bard/Code/mcp-execution-server/${PLIST_NAME}.plist"
LAUNCHAGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🚀 Setting up Brain Execution Server with launchctl..."

# Check if already loaded
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "⚠️  Service already loaded. Unloading first..."
    launchctl unload "$LAUNCHAGENTS_DIR/${PLIST_NAME}.plist" 2>/dev/null
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCHAGENTS_DIR"

# Copy plist file
echo "📁 Copying plist file to LaunchAgents..."
cp "$PLIST_FILE" "$LAUNCHAGENTS_DIR/"

# Load the service
echo "🔧 Loading service..."
launchctl load "$LAUNCHAGENTS_DIR/${PLIST_NAME}.plist"

# Check if loaded successfully
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Service loaded successfully!"
    echo ""
    echo "📊 Service status:"
    launchctl list | grep "$PLIST_NAME"
    echo ""
    echo "📝 Logs will be written to:"
    echo "   - Output: /Users/bard/mcp/memory_files/command_queue/server.log"
    echo "   - Errors: /Users/bard/mcp/memory_files/command_queue/server.error.log"
    echo ""
    echo "🛠️  Useful commands:"
    echo "   Stop:    launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
    echo "   Start:   launchctl load ~/Library/LaunchAgents/${PLIST_NAME}.plist"
    echo "   Status:  launchctl list | grep $PLIST_NAME"
else
    echo "❌ Failed to load service!"
    exit 1
fi
