# Video Service

Микросервис для генерации видео из изображений и аудио файлов.

## Описание

Video Service - это специализированный микросервис, отвечающий за:
- Создание видео из последовательности изображений
- Наложение аудиодорожки на видео
- Применение эффектов и переходов между кадрами
- Применение эффекта Ken Burns (плавное масштабирование и панорамирование)
- Добавление текстовых наложений

## API Endpoints

### GET /health
Проверка статуса сервиса.

**Response:**
```json
{
  "status": "healthy",
  "service": "video-service",
  "version": "1.0.0"
}
```

### POST /generate
Генерация видео из изображений и аудио.

**Request:**
```json
{
  "images_folder": "/path/to/images",
  "audio_file": "/path/to/audio.mp3",
  "settings": {
    "fps": 24,
    "width": 1024,
    "height": 1024,
    "transition_type": "fade",
    "text_position": "bottom"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Video generated successfully",
  "video_path": "/app/output/video/video.mp4",
  "duration": 30.5
}
```

### GET /download/{filename}
Скачивание сгенерированного видео файла.

### POST /upload-images
Загрузка изображений для генерации видео.

## Настройки

Сервис поддерживает следующие настройки для генерации видео:

- `fps`: Частота кадров (по умолчанию 24)
- `width`, `height`: Разрешение видео (по умолчанию 1024x1024)
- `text_fontsize`: Размер шрифта для текстовых наложений
- `fade_duration`: Длительность эффектов перехода
- `text_color`, `bg_color`: Цвета текста и фона
- `text_position`: Позиция текста (top, bottom, center, etc.)
- `transition_type`: Тип перехода между кадрами (none, fade, crossfade, slide)

## Технологии

- **FastAPI**: Web framework
- **MoviePy**: Библиотека для обработки видео
- **Pillow**: Обработка изображений
- **NumPy**: Численные вычисления

## Переменные окружения

- `DEFAULT_OUTPUT_DIR`: Директория для выходных файлов (по умолчанию ./output)

## Запуск

### Docker
```bash
docker build -t video-service .
docker run -p 8004:8004 -v ./output:/app/output video-service
```

### Локально
```bash
pip install -r requirements.txt
python app.py
```

Сервис будет доступен по адресу `http://localhost:8004`
