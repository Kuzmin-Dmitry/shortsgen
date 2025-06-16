# ShortsGen: Creative Video Generator API

ShortsGen is a Python application designed to automatically generate short, creative videos by combining AI-generated narratives, AI-generated or web-sourced images, and AI-generated audio narration. The application is exposed as a FastAPI service, allowing for asynchronous job processing.

## Features

* **API Interface:** Control video generation via a simple REST API (FastAPI).
* **Asynchronous Processing:** Video generation runs in the background, allowing users to check job status.
* **Dual Image Sourcing:**
    * Generate images using AI (OpenAI DALL-E 2/3).
    * Find and download relevant images from the web (using DuckDuckGo Search).
* **AI Narrative Generation:** Create unique mini-novels or use custom prompts (using OpenAI GPT-4o-mini or local models like Gemma).
* **AI Audio Narration:** Generate voiceovers for the narrative using OpenAI TTS with configurable voice styles.
* **Video Composition:** Assemble images and audio into a video using MoviePy.
* **Visual Effects:** Apply optional Ken Burns effect (zoom/pan) and fade transitions to image clips.
* **Configurable:** Easily configure API keys, models, directories, prompts, and video settings via `config.py` and `.env`.
* **Docker Support:** Run the application easily as a containerized API service.
* **Structured Logging:** Detailed logging using Python's standard `logging` module with configurable levels and formatting.

## Project Structure

```
test-gemini/
│
├── api_gateway/           # Front-facing service
│   ├── __init__.py
│   ├── app.py             # Routes client requests to the processing service
│   └── requirements.txt   # Gateway dependencies
├── processing_service/    # Background worker service
│   ├── __init__.py
│   ├── app.py             # Handles job execution and video generation
│   └── requirements.txt   # Processing service dependencies
├── config.py              # Central configuration (API keys, paths, models, prompts)
├── requirements.txt       # Combined dependencies
├── README.md              # This documentation file
├── .env.example           # Example environment variables file
│
├── services/              # Core business logic modules
│   ├── __init__.py
│   ├── generator.py       # Orchestrates the video generation workflow
│   ├── chat_service.py    # Text generation (OpenAI/Gemma)
│   ├── image_service.py   # Image generation (DALL-E) & web search/download (DDGS)
│   ├── audio_service.py   # Audio generation (OpenAI TTS)
│   └── video_service.py   # Video editing and composition (MoviePy)
│
└── utils/                 # Utility tools
    ├── __init__.py
    └── logger.py          # Logging configuration
```

## Installation

1. **Clone the repository (if applicable):**
   ```bash
   git clone <repository-url>
   cd test-gemini
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # or install individually for each service
   pip install -r api_gateway/requirements.txt
   pip install -r processing_service/requirements.txt
   ```

3. **Install Fonts (Linux - needed for MoviePy TextClip):**
   Ensure you have necessary fonts installed. For Debian/Ubuntu:
   ```bash
   sudo apt-get update && sudo apt-get install -y fonts-dejavu
   ```
   *(Note: The default font path in `video_service.py` is `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`. Adjust if needed.)*

## Configuration

1. Create a `.env` file in the project root directory (you can copy `.env.example`).
2. Add your API keys and any desired configuration overrides:

   ```dotenv
   # Required API Keys
   OPENAI_API_KEY=your_openai_api_key_here
   # Optional: DeepAI key if used elsewhere (currently not used in core generation)
   # DEEPAI_API_KEY=your_deepai_api_key_here   # Optional: Override default output directory (used inside Docker)
   DEFAULT_OUTPUT_DIR=/app/output

   # Logging is configured using Python's standard logging module
   # You can adjust logging levels in the application code as needed
   # LOG_FILE_PATH=/app/output/shortsgen.log
   ```

3. Review `config.py` for more detailed configuration options (models, prompts, image sizes, etc.).

## Running the API (Docker Recommended)

Using Docker simplifies deployment and dependency management.

### Prerequisites

* Docker installed on your system.
* A `.env` file created as described in the Configuration section.

### Building the Docker Image

From the project root directory:
```bash
docker build -t shortsgen .
```

### Running the Containers

Create a local directory (e.g., output) to store the generated videos.

First start the processing service (port 8001), then the API gateway (port 8000).

Using PowerShell (Windows):

```PowerShell
# Create output directory if it doesn't exist
if (-not (Test-Path .\output)) { New-Item -ItemType Directory -Force -Path .\output }

docker run -d -p 8001:8001 `
    --env-file .env `
    -v ${PWD}\output:/app/output `
    --name processing-service `
    shortsgen processing_service/app.py

docker run -d -p 8000:8000 `
    --env-file .env `
    -v ${PWD}\output:/app/output `
    --name api-gateway `
    shortsgen api_gateway/app.py
```

Using Bash (Linux/macOS):

```bash
# Create output directory if it doesn't exist
mkdir -p ./output

docker run -d -p 8001:8001 \
    --env-file .env \
    -v "$(pwd)/output:/app/output" \
    --name processing-service \
    shortsgen processing_service/app.py

docker run -d -p 8000:8000 \
    --env-file .env \
    -v "$(pwd)/output:/app/output" \
    --name api-gateway \
    shortsgen api_gateway/app.py
```

This command:

- Starts each container in detached mode (`-d`).
- Maps port `8001` for the processing service and `8000` for the API gateway.
- Loads environment variables from your `.env` file.
- Mounts the local output directory to `/app/output` inside the containers.
- Uses the `shortsgen` image for both services.

The API gateway will be accessible at http://localhost:8000 and will forward requests to the processing service running on http://localhost:8001. Generated videos will appear in your local output directory.

## API Usage

The API provides the following endpoints:

- `GET /`: Health check. Returns `{"status": "online", "service": "ShortsGen API"}`.
- `POST /generate`: Starts a video generation job using AI-generated images. Accepts an optional JSON body: `{"custom_prompt": "Your narrative prompt here"}`. If omitted, uses the default `NOVELLA_PROMPT` from `config.py`.
- `POST /generateFromInternet`: Starts a video generation job using images found on the web. Accepts an optional JSON body: `{"custom_prompt": "Your narrative prompt here"}`. If omitted, uses the default `NOVELLA_PROMPT`.
- `GET /status/{job_id}`: Checks the status of a generation job specified by `job_id`.

### Example Requests

#### 1. Start Generation (AI Images):

curl (Bash):

```bash
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{}'
```

Or with a custom prompt:

```bash
curl -X POST "http://localhost:8000/generate" \
    -H "Content-Type: application/json" \
    -d '{"custom_prompt": "A story about a robot exploring a futuristic city."}'
```

PowerShell:

```PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/generate" -ContentType "application/json" -Body '{}'
```

Or with a custom prompt:

```PowerShell
$body = @{ custom_prompt = "A story about a robot exploring a futuristic city." } | ConvertTo-Json
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/generate" -ContentType "application/json" -Body $body
```

Response (Example):

```json
{
  "job_id": 0,
  "status": "queued",
  "message": "Job queued for processing",
  "output_file": null
}
```
*(Note the job_id for status checking)*

#### 2. Start Generation (Web Images):

curl (Bash):

```bash
curl -X POST "http://localhost:8000/generateFromInternet" \
    -H "Content-Type: application/json" \
    -d '{}'
```

PowerShell:

```PowerShell
Invoke-RestMethod -Method POST -Uri "http://localhost:8000/generateFromInternet" -ContentType "application/json" -Body '{}'
```

#### 3. Check Job Status:

Replace `{job_id}` with the ID received from the POST request (e.g., `0`).

curl (Bash):

```bash
curl -X GET "http://localhost:8000/status/0"
```

PowerShell:

```PowerShell
Invoke-RestMethod -Method GET -Uri "http://localhost:8000/status/0"
```

Response (Examples):

In Progress:
```json
{
  "job_id": 0,
  "status": "processing",
  "message": "Video generation in progress",
  "output_file": null
}
```

Completed:
```json
{
  "job_id": 0,
  "status": "completed",
  "message": "Video generation completed successfully",
  "output_file": "/app/output/video/video.mp4"
}
```

Failed:
```json
{
  "job_id": 0,
  "status": "failed",
  "message": "Video generation failed",
  "output_file": null
}
```

## Architecture Overview

The application follows a service-oriented architecture coordinated by the Generator service and managed via a FastAPI interface.

### Core Workflows

**AI-Generated Images (`/generate`):**

1. Generator calls ChatService to generate a novella (narrative).
2. Generator calls ChatService to generate scene descriptions from the novella.
3. Generator calls ChatService to generate image prompts for each scene.
4. Generator calls ImageService to generate images using DALL-E based on the prompts.
5. Generator calls AudioService to generate narration from the novella text.
6. Generator calls VideoEditor to combine generated images and audio into the final video.

**Web-Sourced Images (`/generateFromInternet`):**

1. Generator calls ChatService to generate a novella.
2. Generator calls ChatService (using function calling) to generate web search queries based on the novella.
3. Generator calls ImageService to search for image URLs (DuckDuckGo) and download the images.
4. Generator calls AudioService to generate narration.
5. Generator calls VideoEditor to combine downloaded images and audio.

### Component Diagram

```
graph TD
    subgraph "User Interface"
        UI[User via HTTP API]
    end

    subgraph "API Gateway"
        AG[api_gateway]
    end

    subgraph "Processing Service"
        PS[processing_service]
        M[JobManager]
        B[BackgroundTasks]
    end

    subgraph "Core Logic"
       G[services.Generator]
    end

    subgraph "Specialized Services"
        CS[services.ChatService]
        IS[services.ImageService]
        AS[services.AudioService]
        VE[services.VideoEditor]
    end

    subgraph "External APIs & Libraries"
        OAI_Text[OpenAI API (GPT-4o-mini)]
        OAI_Audio[OpenAI API (TTS)]
        OAI_Image[OpenAI API (DALL-E)]
        Gemma[Local Gemma Model (Optional)]
        DDGS[DuckDuckGo Search API]
        MP[MoviePy Library]
    end    subgraph "Utilities"
        L[Python logging module]
        C[config.py]
        ENV[.env File]
    end

    UI -- Request --> AG
    AG -- Forward --> PS
    PS -- Create Job --> M
    PS -- Add Task --> B
    B -- Run Job --> G
    AG -- Check Status --> PS

    G --> CS
    G --> IS
    G --> AS
    G --> VE

    CS --> OAI_Text
    CS --> Gemma
    IS --> OAI_Image
    IS --> DDGS
    AS --> OAI_Audio
    VE --> MP

    G -- Uses Config --> C
    CS -- Uses Config --> C
    IS -- Uses Config --> C
    AS -- Uses Config --> C
    VE -- Uses Config --> C
    AG -- Uses Config --> C

    C -- Reads --> ENV

    G -- Uses Logger --> L
    AG -- Uses Logger --> L
    CS -- Uses Logger --> L
    IS -- Uses Logger --> L
    AS -- Uses Logger --> L
    VE -- Uses Logger --> L
```

### Class Structure

```
classDiagram
    class FastAPI {
        +post("/generate")
        +post("/generateFromInternet")
        +get("/status/{job_id}")
    }

    class JobManager {
        -jobs: Dict[int, JobData]
        -current_job_id: int
        +create_job() int
        +get_job(int) JobData
        +update_job(int, ...) None
    }

    class JobData {
      +status: str
      +message: str
      +output_file: str
    }

    class BackgroundTasks {
      +add_task(func, ...)
    }

    class Generator {
        -audio_service: AudioService
        -chat_service: ChatService
        -image_service: ImageService
        -video_editor: VideoEditor
        +generate() OperationResult
        +find_and_generate(custom_prompt) OperationResult
        # Private helper methods for stages
    }

    class ChatService {
        -client: OpenAI
        +generate_text(prompt, functions, ...) Union[str, Dict]
        # Private methods for OpenAI/Gemma
    }

    class ImageService {
        -client: OpenAI
        +generate_image(prompt, ...) ImageResult
        +find_image_url_by_prompt(prompt, ...) str
        +download_image_from_url(url, path) ImageResult
        +process_prompt(prompt, ...) ImageResult
    }

    class AudioService {
        -client: OpenAI
        +generate_audio(text, path, ...) AudioGenerationResult
    }

    class VideoEditor {
        -settings: VideoSettings
        +create_video(img_folder, audio, output, ...) str
        +validate_resources(img_folder, audio) List[str]
        +load_audio(audio) AudioFileClip
        +create_image_clip(img_path, duration, ...) VideoClip
        +create_video_clips(img_files, duration, ...) List[VideoClip]
        +compose_video(clips, audio, output) None
        +create_text_clip(text, duration, ...) VideoClip
    }

    class OperationResult~T~ {
        +success: bool
        +data: T
        +error_message: str
        +elapsed_time: float
        +stage: GenerationStage
    }

    class ImageResult {
        +success: bool
        +file_path: str
        +url: str
        +error_message: str
        +size_bytes: int
    }

    class AudioGenerationResult {
        +success: bool
        +file_path: Path
        +file_size_kb: float
        +message: str
        +error: Exception
    }


    FastAPI --> JobManager
    FastAPI --> BackgroundTasks
    BackgroundTasks --> Generator : process_generation_job()
    Generator --> ChatService
    Generator --> ImageService
    Generator --> AudioService
    Generator --> VideoEditor
    Generator ..> OperationResult : Returns
    ImageService ..> ImageResult : Returns
    AudioService ..> AudioGenerationResult : Returns
```

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.12 | Web framework for building APIs |
| uvicorn | 0.34.0 | ASGI server for FastAPI |
| requests | 2.32.3 | HTTP requests (e.g., to local Gemma, download) |
| moviepy | 2.1.2 | Video editing and composition |
| numpy | 2.2.4 | Numerical operations (used by MoviePy) |
| openai | 1.70.0 | Interaction with OpenAI API (Text, Audio, DALL-E) |
| python-dotenv | 1.1.0 | Loading environment variables from .env file |
| pydantic | 2.11.1 | Data validation and settings management |
| duckduckgo-search | 8.0.0 | Searching for images on the web |
| Pillow | Implicit | Image processing (dependency of MoviePy/others) |

*(Note: Pillow is usually installed as a dependency of MoviePy)*

## Configuration Parameters (config.py)

This table highlights key configurable parameters. Refer to config.py for the full list and detailed prompt templates.

| Parameter | Type | Description | Default (Example) |
|-----------|------|-------------|-------------------|
| DEEPAI_API_KEY | Optional[str] | API key for DeepAI (currently unused in core flow) | None (from .env) |
| OPENAI_API_KEY | Optional[str] | Required API key for OpenAI | None (from .env) |
| DIRS.base | str | Base output directory | ./output |
| DIRS.scenes | str | Directory for generated/downloaded images | ./output/scenes |
| DIRS.video | str | Directory for the final video output | ./output/video |
| DIRS.voice | str | Directory for generated audio | ./output/voice |
| VOICE_FILE_PATH | str | Full path for the generated voice file | ./output/voice/voice.mp3 |
| VIDEO_FILE_PATH | str | Full path for the final video file | ./output/video/video.mp4 |
| GENERATED_IMAGE_SIZE | str | Default size for DALL-E generated images | 1024x1024 |
| DALLE_MODEL | str | DALL-E model for image generation (dall-e-2, dall-e-3) | dall-e-2 |
| OPENAI_MODEL | str | OpenAI model for text-to-speech | gpt-4o-mini-tts |
| LOCAL_TEXT_TO_TEXT_MODEL | str | Identifier for the local text model (e.g., Ollama) | gemma3:12b |
| LOCAL | bool | Flag to potentially switch text generation (currently unused) | False |
| AUDIO_CONFIG | AudioConfig | Dictionary with voice ("coral") and format ("mp3") | {...} |
| AUDIO_INSTRUCTIONS | str | Detailed instructions for the TTS voice style | """...""" |
| PROMPTS | PromptTemplates | Dataclass holding various prompt templates (system, user, etc.) | {...} |
| NUMBER_OF_THE_SCENES | int | Number of scenes/images to generate/find per video | 6 |
| HORIZONTAL_SIZE | int | (Potentially outdated/unused) Image width parameter | 256 |
| CHUNK_SIZE | int | Max characters per line for text overlay in video | 25 |
| FONTSIZE | int | Font size for text overlay in video | 20 |
| SEARCH_QUERY_FUNCTION | List[Dict] | Function definition for OpenAI tool call to generate search queries | [{...}] |
| TEST_AUDIO | bool | If True, skips audio generation if voice.mp3 exists | True |
| TEST_SCENES | bool | If True, skips image generation/download if files exist | True |