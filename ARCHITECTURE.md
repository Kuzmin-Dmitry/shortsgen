# ShortsGen Architecture

## Component Diagram

```mermaid
graph TB
    %% External Client
    Client[Client/Browser] --> Gateway

    %% API Gateway Layer
    subgraph "API Gateway (Port 8000)"
        Gateway[API Gateway<br/>FastAPI<br/>- Request routing<br/>- Client interface<br/>- Authentication]
    end

    %% Core Services Layer
    subgraph "Microservices Architecture"
        
        %% Processing Service
        subgraph "Processing Service (Port 8001)"
            ProcessingAPI[Processing API<br/>FastAPI]
            JobManager[Job Manager<br/>- Async task execution<br/>- Status tracking<br/>- Workflow orchestration]
            Generator[Generator<br/>- Main pipeline logic<br/>- Service coordination]
            
            ProcessingAPI --> JobManager
            JobManager --> Generator
        end

        %% Text Service
        subgraph "Text Service (Port 8002)"
            TextAPI[Text API<br/>FastAPI]
            TextGen[Text Generation Service<br/>- Narrative creation<br/>- Scene descriptions]
            
            subgraph "Text Providers"
                OpenAIProvider[OpenAI Provider<br/>GPT-4o-mini]
                GemmaProvider[Gemma Provider<br/>Local LLM]
                ProviderFactory[Provider Factory<br/>- Model selection<br/>- Provider switching]
            end
            
            TextAPI --> TextGen
            TextGen --> ProviderFactory
            ProviderFactory --> OpenAIProvider
            ProviderFactory --> GemmaProvider
        end

        %% Audio Service
        subgraph "Audio Service (Port 8003)"
            AudioAPI[Audio API<br/>FastAPI]
            AudioService[Audio Service<br/>- TTS processing<br/>- Voice synthesis]
            AudioClient[Audio Client<br/>- OpenAI TTS integration]
            
            AudioAPI --> AudioService
            AudioService --> AudioClient
        end

        %% Video Service
        subgraph "Video Service (Port 8004)"
            VideoAPI[Video API<br/>FastAPI]
            VideoEditor[Video Editor<br/>- Scene composition<br/>- Effects processing<br/>- Final rendering]
            
            VideoAPI --> VideoEditor
        end
    end

    %% External APIs
    subgraph "External APIs"
        OpenAI_API[OpenAI API<br/>- GPT-4o-mini<br/>- DALL-E 2<br/>- TTS]
        DuckDuckGo[DuckDuckGo<br/>Image Search API]
    end

    %% Storage Layer
    subgraph "File Storage"
        OutputDir[Output Directory<br/>/app/output/]
        
        subgraph "Output Structure"
            ScenesDir[scenes/<br/>image_1.jpg...image_6.jpg]
            TextDir[text/<br/>narrative.txt]
            VideoDir[video/<br/>video.mp4]
            VoiceDir[voice/<br/>voice.mp3]
        end
        
        OutputDir --> ScenesDir
        OutputDir --> TextDir
        OutputDir --> VideoDir
        OutputDir --> VoiceDir
    end

    %% Service Communications
    Gateway --> ProcessingAPI
    
    %% Processing Service orchestrates all other services
    Generator --> TextAPI
    Generator --> AudioAPI
    Generator --> VideoAPI
    
    %% External API calls
    OpenAIProvider --> OpenAI_API
    AudioClient --> OpenAI_API
    Generator --> OpenAI_API
    Generator --> DuckDuckGo
    
    %% File operations
    Generator --> OutputDir
    AudioService --> VoiceDir
    VideoEditor --> ScenesDir
    VideoEditor --> VoiceDir
    VideoEditor --> VideoDir
    TextGen --> TextDir

    %% Docker Network
    subgraph "Docker Network: shortsgen_default"
        Gateway
        ProcessingAPI
        TextAPI
        AudioAPI
        VideoAPI
    end

    %% Styling
    classDef gateway fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef storage fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef provider fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class Gateway gateway
    class ProcessingAPI,TextAPI,AudioAPI,VideoAPI service
    class OpenAI_API,DuckDuckGo external
    class OutputDir,ScenesDir,TextDir,VideoDir,VoiceDir storage
    class OpenAIProvider,GemmaProvider,ProviderFactory provider
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant G as API Gateway
    participant P as Processing Service
    participant T as Text Service
    participant A as Audio Service
    participant V as Video Service
    participant O as OpenAI API
    participant D as DuckDuckGo
    participant F as File System

    Note over C,F: Video Generation Flow

    C->>G: POST /generate {custom_prompt}
    G->>P: Forward request
    P->>P: Create job, set status='queued'
    P->>C: Return job_id

    Note over P,F: Async Processing Pipeline

    P->>T: POST /generate-text {prompt}
    T->>O: Generate narrative (GPT-4o-mini)
    O->>T: Return text content
    T->>F: Save narrative.txt
    T->>P: Return narrative + scene descriptions

    alt AI Images Mode
        P->>O: Generate images (DALL-E 2)
        O->>P: Return image URLs
        P->>F: Download and save images
    else Internet Images Mode
        P->>D: Search images
        D->>P: Return image URLs
        P->>F: Download and save images
    end

    P->>A: POST /generate-audio {text}
    A->>O: Generate TTS audio
    O->>A: Return audio data
    A->>F: Save voice.mp3
    A->>P: Return audio file path

    P->>V: POST /create-video {scenes, audio}
    V->>F: Read images and audio
    V->>V: Compose video with effects
    V->>F: Save video.mp4
    V->>P: Return video file path

    P->>P: Set status='completed'

    Note over C,P: Status Checking

    C->>G: GET /status/{job_id}
    G->>P: Forward request
    P->>C: Return job status and result
```

## Service Dependencies

```mermaid
graph TD
    %% Service dependency hierarchy
    Gateway[API Gateway] --> Processing[Processing Service]
    
    Processing --> Text[Text Service]
    Processing --> Audio[Audio Service]
    Processing --> Video[Video Service]
    
    Text --> OpenAI[OpenAI API]
    Audio --> OpenAI
    Processing --> OpenAI
    Processing --> DuckDuckGo[DuckDuckGo API]
    
    %% Internal dependencies
    subgraph "Text Service Internal"
        TextService[Text Generation] --> Factory[Provider Factory]
        Factory --> OpenAIText[OpenAI Provider]
        Factory --> Gemma[Gemma Provider]
    end
    
    %% Technology stack
    subgraph "Technology Stack"
        FastAPI[FastAPI Framework]
        Docker[Docker Containers]
        MoviePy[MoviePy Library]
        Async[Async/Await]
    end
    
    %% File system dependencies
    Processing --> FileSystem[File System]
    Audio --> FileSystem
    Video --> FileSystem
    Text --> FileSystem

    classDef coreService fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef externalAPI fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    classDef technology fill:#f1f8e9,stroke:#388e3c,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class Gateway,Processing,Text,Audio,Video coreService
    class OpenAI,DuckDuckGo externalAPI
    class FastAPI,Docker,MoviePy,Async technology
    class FileSystem storage
```

## Configuration Architecture

```mermaid
graph LR
    subgraph "Configuration Sources"
        EnvFile[.env File<br/>- OPENAI_API_KEY<br/>- DEFAULT_OUTPUT_DIR]
        ConfigPy[config.py<br/>- Service ports<br/>- Model settings<br/>- Processing params]
        Docker[docker-compose.yml<br/>- Service definitions<br/>- Network config<br/>- Volume mounts]
    end

    subgraph "Service Configuration"
        APIConfig[API Gateway Config<br/>- Routing rules<br/>- CORS settings]
        ProcessConfig[Processing Config<br/>- NUMBER_OF_SCENES<br/>- TEST_AUDIO/SCENES]
        TextConfig[Text Config<br/>- OPENAI_MODEL<br/>- Provider selection]
        AudioConfig[Audio Config<br/>- TTS voice<br/>- Audio format]
        VideoConfig[Video Config<br/>- Resolution<br/>- Effects settings]
    end

    EnvFile --> APIConfig
    EnvFile --> ProcessConfig
    EnvFile --> TextConfig
    EnvFile --> AudioConfig
    EnvFile --> VideoConfig

    ConfigPy --> ProcessConfig
    ConfigPy --> TextConfig
    ConfigPy --> AudioConfig
    ConfigPy --> VideoConfig

    Docker --> APIConfig
    Docker --> ProcessConfig
    Docker --> TextConfig
    Docker --> AudioConfig
    Docker --> VideoConfig
```

## Key Components Description

### API Gateway (Port 8000)
- **Purpose**: Single entry point for all client requests
- **Technology**: FastAPI
- **Responsibilities**: 
  - Request routing to appropriate services
  - Client interface management
  - Basic authentication and validation

### Processing Service (Port 8001)
- **Purpose**: Central orchestrator for video generation workflow
- **Technology**: FastAPI with async task management
- **Key Components**:
  - **Job Manager**: Handles async job execution and status tracking
  - **Generator**: Main pipeline logic, coordinates all other services
  - **Service Clients**: Interfaces to text, audio, and video services

### Text Service (Port 8002)
- **Purpose**: AI-powered text and narrative generation
- **Technology**: FastAPI with pluggable AI providers
- **Key Features**:
  - Multiple AI provider support (OpenAI GPT-4o-mini, Gemma)
  - Factory pattern for provider selection
  - Scene description generation

### Audio Service (Port 8003)
- **Purpose**: Text-to-speech audio generation
- **Technology**: FastAPI with OpenAI TTS integration
- **Features**:
  - High-quality voice synthesis
  - Multiple voice options
  - Audio format optimization

### Video Service (Port 8004)
- **Purpose**: Final video composition and rendering
- **Technology**: FastAPI with MoviePy
- **Capabilities**:
  - Multi-scene video composition
  - Audio synchronization
  - Visual effects and transitions
  - Export optimization

## Deployment Architecture

The system uses Docker Compose for orchestration with:
- **Network**: Custom Docker network `shortsgen_default`
- **Volumes**: Shared output directory across services
- **Health Checks**: Built-in service health monitoring
- **Scaling**: Individual service scaling capability
- **Development**: Hot reload support for development mode
