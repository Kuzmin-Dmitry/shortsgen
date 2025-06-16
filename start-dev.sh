#!/bin/bash
# Development startup script for Unix/Linux/Mac

echo "Starting ShortsGen services..."

# Create output directory
mkdir -p output/{scenes,video,voice,text}

# Start API Gateway
echo "Starting API Gateway on port 8000..."
cd api_gateway
python app.py &
API_GATEWAY_PID=$!

# Start Processing Service  
echo "Starting Processing Service on port 8001..."
cd ../processing_service
python app.py &
PROCESSING_SERVICE_PID=$!

echo "Services started!"
echo "API Gateway PID: $API_GATEWAY_PID"
echo "Processing Service PID: $PROCESSING_SERVICE_PID"
echo ""
echo "API Gateway: http://localhost:8000"
echo "Processing Service: http://localhost:8001"
echo ""
echo "To stop services, kill processes with:"
echo "kill $API_GATEWAY_PID $PROCESSING_SERVICE_PID"
