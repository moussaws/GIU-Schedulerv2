#!/bin/bash

echo "🚀 Starting GIU Staff Schedule Composer Backend (Simple Version)..."
echo "📁 Current directory: $(pwd)"

# Create fresh virtual environment
echo "📦 Creating fresh virtual environment..."
rm -rf venv-simple
python3 -m venv venv-simple

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv-simple/bin/activate

# Install minimal dependencies
echo "📥 Installing minimal dependencies..."
pip install -r requirements-minimal.txt
echo "✅ Dependencies installed!"

echo ""
echo "🌟 Starting FastAPI server with your algorithms..."
echo "🌐 API will be available at: http://localhost:8000"
echo "📚 API Documentation at: http://localhost:8000/docs"
echo "🧪 Demo Scheduling at: http://localhost:8000/demo-schedule"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the simple server
python simple_main.py