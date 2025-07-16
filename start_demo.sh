#!/bin/bash

# Text Search Demo Startup Script
# This script starts both the text search API and the React frontend

echo "🚀 Starting Text Search Demo..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to handle cleanup
cleanup() {
    echo -e "\n${YELLOW}Shutting down servers...${NC}"
    kill $API_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
cd frontend
npm install

echo -e "${BLUE}🔧 Starting Text Search API server...${NC}"
cd ..
python text_search_api.py &
API_PID=$!

# Wait for API to start
sleep 3

echo -e "${BLUE}🌐 Starting React frontend...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Demo is starting up!${NC}"
echo -e "${GREEN}📱 Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}🔍 Text Search Demo: http://localhost:3000/text-search-demo${NC}"
echo -e "${GREEN}🔧 API: http://localhost:8001${NC}"
echo -e "${GREEN}📚 API Docs: http://localhost:8001/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"

# Wait for background processes
wait
