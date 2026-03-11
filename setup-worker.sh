#!/bin/bash

# 🤖 CoPaw Worker Setup Script
# Deploy worker node to any VPS

set -e

# Configuration
BRAIN_URL="${BRAIN_URL:-https://superb-happiness-production.up.railway.app}"
NODE_NAME="${NODE_NAME:-$(hostname)}"
NODE_PORT="${NODE_PORT:-3001}"
INSTALL_DIR="${INSTALL_DIR:-/opt/copaw-worker}"

echo "🤖 CoPaw Worker Setup"
echo "===================="
echo "Brain Server: $BRAIN_URL"
echo "Node Name: $NODE_NAME"
echo "Port: $NODE_PORT"
echo "Install Directory: $INSTALL_DIR"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3 python3-pip curl wget git
elif command -v yum &> /dev/null; then
    yum update -y
    yum install -y python3 python3-pip curl wget git
elif command -v apk &> /dev/null; then
    apk update
    apk add python3 py3-pip curl wget git
fi

# Create installation directory
echo "📁 Creating installation directory..."
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Download worker files from GitHub
echo "📥 Downloading worker files..."
curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/copaw-brain/main/worker.py -o worker.py
curl -fsSL https://raw.githubusercontent.com/YOURUSERNAME/copaw-brain/main/requirements.txt -o requirements.txt

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/copaw-worker.service << EOF
[Unit]
Description=CoPaw Worker Node
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment=BRAIN_URL=$BRAIN_URL
Environment=NODE_PORT=$NODE_PORT
Environment=NODE_ID=worker-$(hostname)-$(date +%s)
Environment=NODE_NAME=$NODE_NAME
ExecStart=/usr/bin/python3 $INSTALL_DIR/worker.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
echo "🔧 Enabling service..."
systemctl daemon-reload
systemctl enable copaw-worker

# Start service
echo "🚀 Starting CoPaw Worker Node..."
systemctl start copaw-worker

# Wait a moment and check status
sleep 3
if systemctl is-active --quiet copaw-worker; then
    echo ""
    echo "✅ Worker setup completed successfully!"
    echo ""
    echo "🎉 CoPaw Worker Node is now running!"
    echo ""
    echo "📊 Management commands:"
    echo "  systemctl status copaw-worker         # Check service status"
    echo "  journalctl -u copaw-worker -f        # View logs"
    echo "  systemctl restart copaw-worker       # Restart worker"
    echo "  systemctl stop copaw-worker          # Stop worker"
    echo ""
    echo "🔧 Configuration:"
    echo "  Brain Server: $BRAIN_URL"
    echo "  Node Name: $NODE_NAME"
    echo "  Port: $NODE_PORT"
    echo ""
    echo "🌐 Check worker status:"
    echo "  curl http://localhost:$NODE_PORT/status"
    echo ""
    echo "🧠 The worker will automatically connect to the brain server!"
    echo "📊 You should see the worker appear in the brain web interface at:"
    echo "  $BRAIN_URL"
    echo ""
    echo "⚠️  Make sure the brain server URL is accessible from this VPS!"
    echo "   - Test connectivity: curl $BRAIN_URL/api/status"
else
    echo ""
    echo "❌ Failed to start worker node!"
    echo "Check logs with: journalctl -u copaw-worker -f"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Test brain connectivity: curl $BRAIN_URL/api/status"
    echo "2. Check firewall settings on brain server"
    echo "3. Verify brain server is running"
    exit 1
fi
