# Image Service

Микросервис для генерации изображений с использованием OpenAI DALL-E API.

## Возможности

- Генерация изображений по текстовым описаниям
- Поддержка различных стилей и размеров
- Кэширование сгенерированных изображений
- Интеграция с Redis для обработки задач
- Health check endpoint

## API Endpoints

### POST /generateImage
Генерирует изображение по текстовому описанию.

**Request:**
```json
{
  "prompt": "A beautiful sunset over mountains",
  "size": "1024x1024",
  "style": "natural",
  "quality": "standard"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Image generated successfully",
  "image_url": "/output/images/image_abc123.png",
  "file_size": 204800,
  "width": 1024,
  "height": 1024
}
```

### GET /health
Проверка состояния сервиса.

## Переменные окружения

- `OPENAI_API_KEY` - API ключ OpenAI (обязательно)
- `IMAGE_SERVICE_HOST` - Хост сервиса (по умолчанию: 0.0.0.0)
- `IMAGE_SERVICE_PORT` - Порт сервиса (по умолчанию: 8005)
- `OUTPUT_DIR` - Директория для сохранения изображений
- `REDIS_HOST` - Хост Redis
- `REDIS_PORT` - Порт Redis

## Поддерживаемые параметры

### Размеры изображений:
- 1024x1024
- 1536x1024
- 1024x1536
- 256x256
- 512x512
- 1792x1024
- 1024x1792

### Стили:
- natural
- vivid

### Качество:
- standard
- hd

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервиса
python app.py
```

## Docker

```bash
# Сборка образа
docker build -t image-service .

# Запуск контейнера
docker run -p 8005:8005 -e OPENAI_API_KEY=your_key image-service
```
