# Audio Service

Микросервис для генерации аудио с использованием OpenAI Text-to-Speech API.

## Архитектура

- **Redis Queue**: Обработка задач через Redis очереди
- **Direct API**: Прямые HTTP запросы для генерации аудио
- **OpenAI TTS**: Использует OpenAI API для преобразования текста в речь

## API Endpoints

### Health Check
```
GET /health
```

### Generate Audio
```
POST /generateAudio
{
    "text": "Текст для озвучивания",
    "voice": "alloy",  // optional
    "speed": 1.0,      // optional, 0.25-4.0
    "format": "mp3"    // optional
}
```

## Queue Tasks

Сервис обрабатывает задачи типа `CreateAudio` из очереди `queue:audio-service`.

## Environment Variables

- `OPENAI_API_KEY` - API ключ OpenAI
- `REDIS_URL` - URL подключения к Redis
- `OUTPUT_DIR` - Директория для сохранения аудио файлов
- `AUDIO_SERVICE_PORT` - Порт сервиса (по умолчанию 8003)

## Dependencies

- FastAPI 
- OpenAI Python SDK
- Redis
- Pydantic
