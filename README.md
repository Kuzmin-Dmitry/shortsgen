# ShortsGen: AI Video Generator

Microservice-based application for automatic video generation using AI-generated narratives, images (AI or web-sourced), and audio narration.

## Architecture

### Services

| Service | Port | Responsibility | Key Technologies |
|---------|------|----------------|------------------|
| **API Gateway** | 8000 | Request routing, client interface | FastAPI |
| **Processing Service** | 8001 | Workflow orchestration, job management | FastAPI, async tasks |
| **Text Service** | 8002 | Text/narrative generation | OpenAI GPT-4o-mini, Gemma |
| **Audio Service** | 8003 | TTS audio generation | OpenAI TTS |
| **Video Service** | 8004 | Video composition, effects | MoviePy |
| **Image Service** | 8005 | AI image generation | OpenAI DALL-E |

### Features

* **Dual Image Sources**: AI generation (DALL-E) or web search (DuckDuckGo)
* **Async Processing**: Background job execution with status tracking
* **Mock Mode**: Testing without API costs
* **Docker Support**: Full containerization with health checks
* **Configurable**: Models, prompts, effects via config files

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key
- `.env` file with `OPENAI_API_KEY=your_key_here`

### Run with Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up --build

# Background mode
docker-compose up -d --build

# Stop services
docker-compose down

# Rebuild specific service
docker-compose build text-service
docker-compose up text-service

# Restart single service
docker-compose restart processing-service

# Remove everything (containers, networks, volumes)
docker-compose down -v --remove-orphans
```

**Service URLs:**
- API Gateway: http://localhost:8000 (main entry point)
- Processing: http://localhost:8001 (internal)
- Text: http://localhost:8002 (internal)
- Audio: http://localhost:8003 (internal)
- Video: http://localhost:8004 (internal)

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Windows
start-dev.bat

# Linux/Mac
chmod +x start-dev.sh && ./start-dev.sh
```

## API Usage

### Endpoints
- `GET /` - Health check
- `POST /generate` - Generate video with AI images
- `POST /generateFromInternet` - Generate video with web images  
- `GET /status/{job_id}` - Check job status

### Examples

**Generate Video (AI Images):**
```bash
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{"custom_prompt": "A robot exploring a futuristic city"}'
```

**Generate Video (Web Images):**
```bash
curl -X POST "http://localhost:8000/generateFromInternet" \
    -H "Content-Type: application/json" \
    -d '{"custom_prompt": "Ocean waves at sunset"}'
```

**Mock Mode (Testing):**
```bash
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{"mock": true}'
```

**Check Status:**
```bash
curl "http://localhost:8000/status/0"
```

### Response Examples

**Job Created:**
```json
{
  "job_id": 0,
  "status": "queued", 
  "message": "Job queued for processing"
}
```

**Job Completed:**
```json
{
  "job_id": 0,
  "status": "completed",
  "message": "Video generation completed",
  "output_file": "/app/output/video/video.mp4"
}
```

## Debugging & Monitoring

### Service Health Checks
```bash
curl http://localhost:8000/        # API Gateway
curl http://localhost:8001/        # Processing Service  
curl http://localhost:8002/health  # Text Service
curl http://localhost:8003/health  # Audio Service
curl http://localhost:8004/health  # Video Service
```

### Docker Compose Debugging
```bash
# Check service status
docker-compose ps

# View logs for all services
docker-compose logs

# Follow specific service logs in real-time
docker-compose logs -f processing-service
docker-compose logs -f text-service

# View last N lines of logs
docker-compose logs --tail=100 video-service
docker-compose logs --tail=50 api-gateway

# Debug specific service
docker-compose logs --since=1h audio-service

# Execute commands inside running container
docker-compose exec processing-service bash
docker-compose exec text-service python -c "import requests; print('OK')"

# View container resource usage
docker stats $(docker-compose ps -q)

# Inspect service configuration
docker-compose config

# Check what ports are exposed
docker-compose port api-gateway 8000
docker-compose port processing-service 8001
```

### Common Issues & Solutions
```bash
# Port conflicts
docker-compose down && docker-compose up

# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up

# Check service dependencies
docker-compose logs processing-service | grep -i "connection\|error\|failed"

# Restart stuck service
docker-compose restart processing-service

# Debug networking
docker network ls
docker network inspect shortsgen_default
```

### Mock Mode Testing
Add `"mock": true` to requests for testing without API costs:
```bash
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{"mock": true}'
```

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_key_here
DEFAULT_OUTPUT_DIR=/app/output
```

### Key Parameters (config.py)
| Parameter | Description | Default |
|-----------|-------------|---------|
| `NUMBER_OF_THE_SCENES` | Images per video | 6 |
| `DALLE_MODEL` | Image model | dall-e-2 |
| `OPENAI_MODEL` | Text model | gpt-4o-mini |
| `AUDIO_CONFIG.voice` | TTS voice | alloy |
| `TEST_AUDIO` | Skip audio if exists | True |
| `TEST_SCENES` | Skip images if exist | True |