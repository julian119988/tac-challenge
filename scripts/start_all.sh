#!/bin/bash
# Start both webhook server and frontend in parallel

echo "╔════════════════════════════════════════════════════════╗"
echo "║  Starting Anti-Procrastination Focus App              ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Starting services:"
echo "  • Webhook Server: http://localhost:8000"
echo "  • Frontend Dev:   http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup INT TERM

# Start webhook server in background
./start_webhook_server.sh &
WEBHOOK_PID=$!

# Give webhook server time to start
sleep 2

# Start frontend in background
./start_frontend.sh &
FRONTEND_PID=$!

# Wait for all background processes
wait
