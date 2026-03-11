#!/bin/bash

# 🤖 CoPaw Worker Setup Script (No Sudo Version)
# For containers where sudo is not available

set -e

# Configuration
BRAIN_URL="${BRAIN_URL:-https://superb-happiness-production.up.railway.app}"
NODE_NAME="${NODE_NAME:-$(hostname)}"
NODE_PORT="${NODE_PORT:-3001}"
INSTALL_DIR="${INSTALL_DIR:-/home/copaw-worker}"

echo "🤖 CoPaw Worker Setup (No Sudo)"
echo "=================================="
echo "Brain Server: $BRAIN_URL"
echo "Node Name: $NODE_NAME"
echo "Port: $NODE_PORT"
echo "Install Directory: $INSTALL_DIR"
echo ""

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Download worker files from GitHub
echo "📥 Downloading worker files..."
curl -fsSL https://raw.githubusercontent.com/aidorablecanada-art/copaw-brain/main/worker.py -o worker.py
curl -fsSL https://raw.githubusercontent.com/aidorablecanada-art/copaw-brain/main/requirements.txt -o requirements.txt

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3 first."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip3 first."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user -r requirements.txt

# Create start script
echo "📝 Creating start script..."
cat > start-worker.sh << 'EOF'
#!/bin/bash
cd $INSTALL_DIR
export BRAIN_URL="$BRAIN_URL"
export NODE_PORT="$NODE_PORT"
export NODE_ID="worker-$(hostname)-$(date +%s)"
export NODE_NAME="$NODE_NAME"
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
echo "  Install Directory: $INSTALL_DIR"
echo ""
echo "🚀 To start the worker:"
echo "  cd $INSTALL_DIR"
echo "  ./start-worker.sh"
echo ""
echo "🌐 Check worker status:"
echo "  curl http://localhost:$NODE_PORT/status"
echo ""
echo "🧠 The worker will connect to brain server when started!"
echo "📊 You should see the worker appear in the brain web interface at:"
echo "  $BRAIN_URL"
echo ""
echo "⚠️  Make sure the brain server URL is accessible from this container!"
