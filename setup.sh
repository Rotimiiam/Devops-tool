#!/bin/bash

echo "DevOps Tool - Setup Script"
echo "============================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your OAuth credentials and API keys before starting the application."
    echo ""
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

echo "✓ Docker and docker-compose are installed"
echo ""

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials:"
echo "   - Bitbucket OAuth credentials"
echo "   - GitHub OAuth credentials"
echo "   - Gemini API key (optional, can be configured via UI)"
echo ""
echo "2. Start the application:"
echo "   docker-compose up -d"
echo ""
echo "3. Access the application:"
echo "   http://localhost:3000"
echo ""
echo "4. Check logs:"
echo "   docker-compose logs -f"
echo ""
