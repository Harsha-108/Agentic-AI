#!/bin/bash

# Multi-Agent POC Backend - Quick Start Script
# This script sets up and runs the complete POC

set -e  # Exit on any error

echo "🚀 Multi-Agent POC Backend - Quick Start"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Found $PYTHON_VERSION"
    else
        print_error "Python 3 is required but not installed"
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    print_status "Checking environment configuration..."
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# External WebSocket Configuration (OPTIONAL)
EXTERNAL_WS_URL=wss://your-friend-server.onrender.com/ws
EXTERNAL_WS_USER_ID=poc-backend
EOF
        print_warning "Please edit .env file with your OpenAI API key"
        echo "You can get one from: https://platform.openai.com/api-keys"
        read -p "Press Enter after updating .env file..." -r
    else
        print_success ".env file found"
    fi
    
    # Check if OpenAI API key is set
    if grep -q "your_openai_api_key_here" .env; then
        print_error "Please set your OpenAI API key in .env file"
        exit 1
    fi
}

# Create virtual environment if it doesn't exist
setup_venv() {
    print_status "Setting up Python virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_success "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
}

# Install dependencies
install_deps() {
    print_status "Installing dependencies..."
    pip install --upgrade pip > /dev/null
    pip install -r requirements.txt > /dev/null
    print_success "Dependencies installed"
}

# Create necessary directories
setup_dirs() {
    print_status "Setting up directories..."
    mkdir -p user_contexts
    mkdir -p logs
    print_success "Directories created"
}

# Run validation tests
run_validation() {
    print_status "Running validation tests..."
    
    # Test 1: Import all modules
    python3 -c "
import sys
sys.path.append('app')
try:
    from models import *
    from llm_service import LLMService
    from file_service import FileService
    from agents import *
    from router import MessageRouter
    print('✅ All modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    # Test 2: Check OpenAI connection
    python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
if not api_key or api_key == 'your_openai_api_key_here':
    print('❌ OpenAI API key not configured')
    exit(1)

# Try to import openai
try:
    import openai
    print('✅ OpenAI library available')
except ImportError:
    print('❌ OpenAI library not installed')
    exit(1)
"
    
    print_success "Validation tests passed"
}

# Start the server
start_server() {
    print_status "Starting Multi-Agent POC Backend..."
    echo ""
    echo "🌐 Server will be available at:"
    echo "   • Main server: http://localhost:8000"
    echo "   • WebSocket: ws://localhost:8000/ws/{user_id}"
    echo "   • Health check: http://localhost:8000/health"
    echo ""
    echo "📁 Test clients available:"
    echo "   • Local client: clients/test_local_client.html"
    echo "   • External client: clients/test_external_client.html"
    echo ""
    echo "🔧 Useful commands:"
    echo "   • Health check: curl http://localhost:8000/health"
    echo "   • External status: curl http://localhost:8000/external-status"
    echo "   • Load test: python clients/load_test.py --clients 5 --duration 10"
    echo ""
    print_success "Starting server now..."
    echo ""
    
    cd app
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
}

# Parse command line arguments
case "${1:-start}" in
    "start")
        check_python
        check_env
        setup_venv
        install_deps
        setup_dirs
        run_validation
        start_server
        ;;
    "test")
        print_status "Running load test..."
        source venv/bin/activate
        python clients/load_test.py --clients 5 --duration 10
        ;;
    "monitor")
        print_status "Starting external monitor..."
        source venv/bin/activate
        python clients/external_monitor.py "${2:-ws://localhost:8000}"
        ;;
    "health")
        print_status "Checking server health..."
        curl -s http://localhost:8000/health | python -m json.tool
        ;;
    "clean")
        print_status "Cleaning up..."
        rm -rf venv user_contexts logs __pycache__ app/__pycache__
        print_success "Cleanup complete"
        ;;
    "help")
        echo "Multi-Agent POC Backend - Quick Start Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start      - Start the complete POC (default)"
        echo "  test       - Run load testing"
        echo "  monitor    - Start external WebSocket monitor"
        echo "  health     - Check server health"
        echo "  clean      - Clean up generated files"
        echo "  help       - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                                    # Start server"
        echo "  $0 test                              # Run load test"
        echo "  $0 monitor ws://external-server.com  # Monitor external server"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Run '$0 help' for available commands"
        exit 1
        ;;
esac