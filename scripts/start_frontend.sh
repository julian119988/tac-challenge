#!/bin/bash
# Start the React frontend development server

echo "Starting React frontend development server..."
echo "Frontend will be available at http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

cd apps/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
    echo ""
fi

# Start Vite dev server
npm run dev
