# Creative Video Generator

Это проект для генерации креативного видео с использованием OpenAI API, MoviePy и других библиотек. Проект разделён на модули, чтобы легко поддерживать и расширять функциональность.

## Структура проекта

- **config.py**: Конфигурация и API-ключи.
- **main.py**: Основной скрипт запуска.
- **services/**: Модули с бизнес-логикой для генерации текста, изображений, аудио и видео.
- **utils/**: Вспомогательные функции.

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Архитектура проекта

### Диаграмма компонентов

```mermaid
graph TD
    A[main.py] --> B[Video]
    B --> C[ChatService]
    B --> D[ImageService]
    B --> E[AudioService]
    B --> F[VideoEditor]
    C --> G[OpenAI API/Local Gemma]
    D --> H[DALL-E API]
    E --> I[OpenAI Audio API]
    F --> J[MoviePy]
    K[config.py] --> B
    K --> C
    K --> D
    K --> E
    L[utils] --> B
```

### Процесс генерации видео

```mermaid
sequenceDiagram
    participant User
    participant Video
    participant ChatService
    participant ImageService
    participant AudioService
    participant VideoEditor
    
    User->>Video: generate()
    Video->>ChatService: generate_chatgpt_text()
    ChatService-->>Video: novella_text
    Video->>ChatService: generate_frames_text()
    ChatService-->>Video: frames_text
    loop For each scene
        Video->>ChatService: generate_image_prompt()
        ChatService-->>Video: image_prompt
        Video->>ImageService: generate_image()
        ImageService-->>Video: image_path
    end
    Video->>AudioService: generate_audio()
    AudioService-->>Video: audio_path
    Video->>VideoEditor: create_video_with_transitions()
    VideoEditor-->>Video: video_path
    Video-->>User: final_video
```

### Структура классов

```mermaid
classDiagram
    class Video {
        -audio_service: AudioService
        -chat_service: ChatService
        -image_service: ImageService
        -video_editor: VideoEditor
        +generate()
    }
    
    class ChatService {
        +generate_chatgpt_text_gemma3()
        +generate_chatgpt_text_openai()
    }
    
    class ImageService {
        +generate_image_url()
        +download_image()
        +sanitize_filename()
        +process_prompt()
        +generate_image()
    }
    
    class AudioService {
        +generate_audio()
    }
    
    class VideoEditor {
        +validate_resources()
        +load_audio()
        +create_image_clip()
        +create_video_clips()
        +create_text_video()
        +create_video_with_transitions()
    }
    
    Video --> ChatService
    Video --> ImageService
    Video --> AudioService
    Video --> VideoEditor
```

### Поток данных

```
+----------------+     +----------------+     +----------------+
| Текстовый      |     | Изображения    |     | Аудио          |
| сценарий       | --> | для сцен       | --> | нарратив       | 
| (novella_text) |     | (scene images) |     | (audio file)   |
+----------------+     +----------------+     +----------------+
                                                      |
                                                      v
                                            +----------------+
                                            | Финальное      |
                                            | видео          |
                                            | (final video)  |
                                            +----------------+
```

### Таблица зависимостей

| Библиотека | Версия | Назначение |
|------------|--------|------------|
| request | 2.31.0 | HTTP-запросы к API |
| moviepy | 1.0.3 | Обработка и создание видео |
| numpy | 1.25.2 | Работа с массивами данных |
| openai | 0.28.0 | Взаимодействие с OpenAI API |
| python-dotenv | 1.0.0 | Загрузка переменных окружения |

### Дерево директорий

```
c:\git\shortsgen\
│
├── main.py                # Основная точка входа
├── config.py              # Конфигурация проекта
├── requirements.txt       # Зависимости проекта
├── README.md              # Документация
│
├── services\              # Модули сервисов
│   ├── __init__.py
│   ├── audio_service.py   # Генерация аудио
│   ├── chat_service.py    # Генерация текста
│   ├── image_service.py   # Генерация изображений
│   ├── video.py           # Основной видео-процесс
│   └── video_service.py   # Редактирование видео
│
└── utils\                 # Вспомогательные утилиты
    ├── __init__.py
    ├── file_utils.py      # Работа с файлами
    └── logger.py          # Логирование
```

### Таблица конфигурационных параметров

| Параметр | Тип | Описание |
|----------|-----|----------|
| DEEPAI_API_KEY | string | API ключ для DeepAI |
| OPENAI_API_KEY | string | API ключ для OpenAI |
| DEFAULT_IMAGE_SIZE | string | Размер изображения по умолчанию |
| DEFAULT_OUTPUT_DIR | string | Путь к директории вывода |
| DALLE_MODEL | string | Модель DALL-E для генерации изображений |
| OPENAI_MODEL | string | Модель OpenAI для генерации аудио |
| LOCAL_TEXT_TO_TEXT_MODEL | string | Локальная модель для генерации текста |
| LOCAL | boolean | Флаг использования локальных моделей |
| NUMBER_OF_THE_SCENES | int | Количество сцен для генерации |
