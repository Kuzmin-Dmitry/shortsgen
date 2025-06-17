# Audio Service

Микросервис для генерации аудио из текста с использованием OpenAI TTS API.

## Возможности

- Преобразование текста в речь с использованием OpenAI TTS
- Поддержка нескольких голосов (alloy, echo, fable, onyx, nova, shimmer)
- Поддержка разных аудио форматов (mp3, opus, aac, flac, wav, pcm)
- Поддержка языков: русский (ru) и английский (en)
- REST API для интеграции с другими сервисами
- Потоковая передача аудио данных
- Health check эндпоинт
- Тестовый режим для разработки

## API Эндпоинты

### GET /health
Проверка состояния сервиса

### POST /generate
Генерация аудио файла и возврат метаданных

**Тело запроса:**
```json
{
  "text": "Текст для преобразования в речь",
  "language": "ru",
  "voice": "alloy",
  "format": "mp3"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Audio generated successfully",
  "file_size_kb": 123.45,
  "duration_seconds": 15.2
}
```

### POST /generate-stream
Генерация и потоковая передача аудио файла

**Тело запроса:** то же, что и для `/generate`

**Ответ:** Аудио файл в бинарном формате

## Переменные окружения

- `OPENAI_API_KEY` - API ключ для OpenAI (обязательно)
- `AUDIO_SERVICE_PORT` - Порт сервиса (по умолчанию: 8003)
- `AUDIO_SERVICE_HOST` - Хост сервиса (по умолчанию: 0.0.0.0)
- `DEFAULT_OUTPUT_DIR` - Директория для сохранения файлов (по умолчанию: ./output)
- `TEST_AUDIO` - Включить тестовый режим (по умолчанию: true)

## Запуск

### С помощью Docker
```bash
docker build -t audio-service .
docker run -p 8003:8003 -e OPENAI_API_KEY=your_key_here audio-service
```

### Локально
```bash
pip install -r requirements.txt
python app.py
```

## Использование клиента

```python
from audio_service.client import AudioServiceClient

client = AudioServiceClient("http://localhost:8003")

# Проверка здоровья сервиса
if client.health_check():
    # Генерация аудио в файл
    client.generate_audio_stream(
        text="Привет, мир!",
        output_path="output.mp3",
        language="ru",
        voice="alloy"
    )
```

## Интеграция с другими сервисами

Сервис интегрируется с `processing_service` через HTTP API. Processing service использует `audio_service_client.py` для взаимодействия с аудио сервисом.

## Архитектура

- `app.py` - FastAPI приложение с REST API
- `audio_service.py` - Основная логика работы с OpenAI TTS
- `config.py` - Конфигурация сервиса
- `models/requests.py` - Модели данных для API
- `client.py` - HTTP клиент для взаимодействия с сервисом
- `Dockerfile` - Конфигурация Docker контейнера
