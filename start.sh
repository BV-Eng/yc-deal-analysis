#!/bin/bash
# YC W26 Deal Analysis CRM - Start Script

# Check for Node.js
NODE_PATH="/tmp/node-v20.11.1-darwin-arm64/bin"
if [ -d "$NODE_PATH" ]; then
  export PATH="$NODE_PATH:$PATH"
fi

if ! command -v node &> /dev/null; then
  echo "Node.js not found. Downloading..."
  curl -fsSL https://nodejs.org/dist/v20.11.1/node-v20.11.1-darwin-arm64.tar.gz -o /tmp/node.tar.gz
  tar xzf /tmp/node.tar.gz -C /tmp/
  export PATH="/tmp/node-v20.11.1-darwin-arm64/bin:$PATH"
fi

cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install better-sqlite3 express cors
fi

# Initialize database if needed
if [ ! -f "data/yc_deals.db" ]; then
  echo "Initializing database and generating scores..."
  node generate_scores.js
fi

echo ""
echo "Starting YC W26 Deal Analysis CRM..."
echo "Open http://localhost:3456 in your browser"
echo ""

node backend/server.js
