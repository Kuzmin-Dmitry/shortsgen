# Audio Service

Микросервис для генерации аудио из текста с использованием OpenAI TTS API.

## Возможности

- Преобразование текста в речь с использованием различных голосов
- Поддержка множественных форматов аудио (MP3, WAV, OPUS и др.)
- Мок-режим для тестирования без реальной генерации
- Health check endpoint для мониторинга

## API Endpoints

### POST /generateAudio
Генерация аудио из текста.

**Request Body:**
```json
{
  "text": "Привет! Это тестовое сообщение для генерации аудио.",
  "language": "ru",
  "voice": "alloy", 
  "format": "mp3",
  "mock": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Audio generated successfully",
  "file_size_kb": 123.45,
  "duration_seconds": 15.2
}
```

### GET /health
Проверка состояния сервиса.

## Переменные окружения

- `OPENAI_API_KEY` - API ключ OpenAI (обязательно)
- `AUDIO_SERVICE_HOST` - хост сервиса (по умолчанию: 0.0.0.0)
- `AUDIO_SERVICE_PORT` - порт сервиса (по умолчанию: 8003)
- `AUDIO_OUTPUT_DIR` - директория для сохранения аудио файлов

## Запуск

```bash
python app.py
```

Или через Docker:
```bash
docker build -t audio-service .
docker run -p 8003:8003 audio-service
```
