#!/bin/bash

# AI Interview System - Quick Start Script

echo "========================================="
echo "   AI Interview System Setup"
echo "========================================="
echo ""

# Check if Gemini API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  WARNING: GEMINI_API_KEY environment variable not set!"
    echo ""
    echo "Please set your Gemini API key:"
    echo "  export GEMINI_API_KEY='your-key-here'"
    echo ""
    echo "Get your free API key at: https://makersuite.google.com/app/apikey"
    echo ""
    exit 1
fi

echo "✅ Gemini API key detected"
echo ""

# Check if dependencies are installed
echo "📦 Checking Python dependencies..."
python3 -c "import langchain" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing LangChain dependencies..."
    cd backend
    pip install langchain==0.1.0 langchain-google-genai==0.0.6 google-generativeai==0.3.2
    cd ..
fi

echo "✅ Dependencies installed"
echo ""

# Start backend
echo "🚀 Starting backend server..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if backend is running
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Backend running at http://localhost:8000"
else
    echo "⚠️  Backend may not be running properly"
fi

echo ""
echo "========================================="
echo "   System Started!"
echo "========================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000 (start manually)"
echo ""
echo "To start frontend:"
echo "  cd frontend && npm start"
echo ""
echo "To stop backend:"
echo "  kill $BACKEND_PID"
echo ""
echo "📚 Documentation:"
echo "  - Testing Guide: TEST_AI_SYSTEM.md"
echo "  - Implementation: AI_IMPLEMENTATION.md"
echo ""
