#!/bin/bash

# 🤖 CoPaw Worker Setup Script (Simple Version)
# Works in current directory, no sudo needed

set -e

# Configuration - MUST be provided
BRAIN_URL="${BRAIN_URL:-https://superb-happiness-production.up.railway.app}"
NODE_NAME="${NODE_NAME:-$(hostname)}"
NODE_PORT="${NODE_PORT:-3001}"

echo "🤖 CoPaw Worker Setup (Simple)"
echo "================================"
echo "Brain Server: $BRAIN_URL"
echo "Node Name: $NODE_NAME"
echo "Port: $NODE_PORT"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3 first."
    exit 1
fi

# Download worker files from GitHub
echo "📥 Downloading worker files..."
curl -fsSL https://raw.githubusercontent.com/aidorablecanada-art/copaw-brain/main/worker.py -o worker.py
curl -fsSL https://raw.githubusercontent.com/aidorablecanada-art/copaw-brain/main/requirements.txt -o requirements.txt

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Create start script
echo "📝 Creating start script..."
cat > start-worker.sh << 'EOF'
#!/bin/bash
export BRAIN_URL="$BRAIN_URL"
export NODE_PORT="$NODE_PORT"
export NODE_ID="worker-$(hostname)-$(date +%s)"
export NODE_NAME="$NODE_NAME"
echo "🧠 Starting worker with ID: $NODE_ID"
echo "🌐 Connecting to brain: $BRAIN_URL"
python3 worker.py
EOF

chmod +x start-worker.sh

echo ""
echo "✅ Worker setup completed!"
echo ""
echo "🎉 CoPaw Worker is ready to start!"
echo ""
echo "🔧 Configuration:"
echo "  Brain Server: $BRAIN_URL"
echo "  Node Name: $NODE_NAME"
echo "  Port: $NODE_PORT"
echo ""
echo "🚀 To start worker:"
echo "  ./start-worker.sh"
echo ""
echo "🌐 Check worker status:"
echo "  curl http://localhost:$NODE_PORT/status"
echo ""
echo "🧠 The worker will connect to brain server when started!"
echo "📊 You should see the worker appear in the brain web interface at:"
echo "  $BRAIN_URL"
echo ""
echo "⚠️  Make sure to run this in the background:"
echo "  nohup ./start-worker.sh &"
echo "  or: screen -S worker ./start-worker.sh"
