#!/bin/bash
# YC W26 Deal Analysis CRM - Team Access Startup Script
# This starts the server + creates a public tunnel for team access
# Protected by password authentication (default: bettervc2026)
#
# To change the team password, set the TEAM_PASSWORD environment variable:
#   TEAM_PASSWORD=mypassword ./start-team.sh
#
# To change the tunnel subdomain, set the TUNNEL_NAME environment variable:
#   TUNNEL_NAME=my-custom-name ./start-team.sh
#   → URL will be: https://my-custom-name.loca.lt

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
  npm install
fi

TUNNEL_SUBDOMAIN="${TUNNEL_NAME:-bettervc-deals}"
TUNNEL_URL="https://${TUNNEL_SUBDOMAIN}.loca.lt"

# Start the Node.js server
echo ""
echo "Starting YC W26 Deal Analysis CRM..."
node backend/server.js &
SERVER_PID=$!
sleep 2

# Start the localtunnel
echo ""
echo "Creating secure tunnel for team access..."
npx --yes localtunnel --port 3456 --subdomain "$TUNNEL_SUBDOMAIN" &
TUNNEL_PID=$!

# Wait for tunnel to initialize
sleep 5
echo ""
echo "============================================"
echo "  🔒 YC W26 Deal Analysis CRM is LIVE"
echo "============================================"
echo ""
echo "  URL: $TUNNEL_URL"
echo ""
echo "  Team password: ${TEAM_PASSWORD:-bettervc2026}"
echo ""
echo "  Share the URL and password with your team."
echo ""
echo "  NOTE: On first visit, click 'Click to Continue'"
echo "  on the localtunnel interstitial page."
echo ""
echo "  Press Ctrl+C to stop the server and tunnel."
echo "============================================"
echo ""

# Handle shutdown
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $SERVER_PID 2>/dev/null
  kill $TUNNEL_PID 2>/dev/null
  wait $SERVER_PID 2>/dev/null
  wait $TUNNEL_PID 2>/dev/null
  echo "Done."
  exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait $SERVER_PID $TUNNEL_PID
