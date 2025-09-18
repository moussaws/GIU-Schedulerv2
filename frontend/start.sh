#!/bin/bash

echo "🚀 Starting GIU Staff Schedule Composer Frontend..."
echo "📁 Current directory: $(pwd)"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
    echo "✅ Dependencies installed!"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🌟 Starting React development server..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🔗 Backend API at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the React development server
npm start