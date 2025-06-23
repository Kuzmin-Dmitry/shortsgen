# Text Service API Documentation

## Обзор

Text Service - это микросервис для генерации текста с использованием AI моделей (OpenAI GPT и локальные Gemma модели через Ollama).

---

## 📥 Точки входа (HTTP API)

| Endpoint | Метод | Описание | Входные данные | Формат ответа | Статус коды |
|----------|-------|----------|----------------|---------------|-------------|
| `/` | GET | Health check | Нет | `{"status": "online", "service": "Text Service", "version": "1.0.0"}` | 200 |
| `/health` | GET | Детальная проверка | Нет | `{"status": "healthy", "service": "Text Service", "version": "1.0.0"}` | 200 |
| `/generateText` | POST | Генерация текста | `TextGenerationRequest` | `TextGenerationResponse` | 200, 400, 500 |

---

## 📤 Точки выхода (External APIs)

| Сервис | URL | Провайдер | Аутентификация | Назначение | Формат запроса |
|--------|-----|-----------|---------------|------------|----------------|
| **OpenAI API** | `https://api.openai.com/v1/chat/completions` | `OpenAIProvider` | Bearer Token | GPT модели | JSON с `model`, `messages`, `tools` |
| **Ollama API** | `http://localhost:11434/api/generate` | `GemmaProvider` | Нет | Локальные модели | JSON с `model`, `prompt`, `options` |
| **Ollama Health** | `http://localhost:11434/api/tags` | `GemmaProvider` | Нет | Проверка доступности | GET запрос |

---

## 🔧 Входные модели данных

### TextGenerationRequest

| Поле | Тип | Обязательное | Значение по умолчанию | Описание |
|------|-----|--------------|----------------------|----------|
| `prompt` | `str` | ✅ | - | Текст для генерации |
| `functions` | `List[Function]` | ❌ | `[]` | Список доступных функций |
| `max_tokens` | `int` | ❌ | `300` | Максимальное количество токенов |
| `model` | `str` | ❌ | `"openai"` | Модель для использования |
| `temperature` | `float` | ❌ | `0.8` | Температура генерации |
| `system_prompt` | `str` | ❌ | `None` | Системный промпт |
| `mock` | `bool` | ❌ | `False` | Режим тестирования |

### Пример запроса:
```json
{
  "prompt": "Создай сценарий для короткого видео о путешествиях",
  "functions": [
    {
      "type": "function",
      "function": {
        "name": "create_scenes",
        "description": "Создание сцен для видео",
        "parameters": {
          "type": "object",
          "properties": {
            "scenes": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        }
      }
    }
  ],
  "max_tokens": 500,
  "model": "openai",
  "temperature": 0.7,
  "system_prompt": "Ты эксперт по созданию коротких видео для социальных сетей"
}
```

---

## 📊 Выходные модели данных

### TextGenerationResponse

| Поле | Тип | Описание |
|------|-----|----------|
| `content` | `str \| Dict[str, Any]` | Сгенерированный контент или результат вызова функции |
| `success` | `bool` | Статус успешного выполнения |
| `model_used` | `str` | Название использованной модели |
| `tokens_generated` | `int` | Количество сгенерированных токенов |

### HealthResponse

| Поле | Тип | Описание |
|------|-----|----------|
| `status` | `str` | Статус сервиса ("online", "healthy") |
| `service` | `str` | Название сервиса |
| `version` | `str` | Версия сервиса |

### Пример ответа:
```json
{
  "content": {
    "scenes": [
      "Восход солнца над горами",
      "Путешественник с рюкзаком на тропе",
      "Красивый пейзаж с озером"
    ]
  },
  "success": true,
  "model_used": "gpt-4o-mini",
  "tokens_generated": 45
}
```

---

## ⚙️ Конфигурационные переменные

| Переменная | Тип | Значение по умолчанию | Описание |
|------------|-----|----------------------|----------|
| `OPENAI_API_KEY` | `str` | `None` | API ключ OpenAI |
| `DEFAULT_OPENAI_MODEL` | `str` | `"gpt-4o-mini"` | Модель OpenAI по умолчанию |
| `DEFAULT_MAX_TOKENS` | `int` | `300` | Максимум токенов |
| `DEFAULT_TEMPERATURE` | `float` | `0.8` | Температура генерации |
| `LOCAL_TEXT_TO_TEXT_MODEL` | `str` | `"gemma2:2b"` | Локальная модель |
| `LOCAL_MODEL_URL` | `str` | `"http://localhost:11434/api/generate"` | URL локальной модели |
| `SERVICE_HOST` | `str` | `"0.0.0.0"` | Хост сервиса |
| `SERVICE_PORT` | `int` | `8002` | Порт сервиса |
| `LOG_LEVEL` | `str` | `"INFO"` | Уровень логирования |

---

## 🚦 Коды ответов и ошибки

| HTTP Code | Статус | Причина | Формат ответа |
|-----------|--------|---------|---------------|
| **200** | Success | Успешное выполнение | Соответствующая модель ответа |
| **400** | Bad Request | Неверные параметры запроса | `{"detail": "error message", "status_code": 400}` |
| **500** | Internal Error | Ошибка сервера/модели | `{"detail": "error message", "status_code": 500}` |
| **503** | Service Unavailable | Недоступность внешних API | `{"detail": "error message", "status_code": 503}` |

---

## 🔄 Типы исключений

| Исключение | Наследуется от | Описание | Использование |
|------------|---------------|----------|---------------|
| `ModelException` | `Exception` | Базовое исключение модели | Общие ошибки работы с моделями |
| `OpenAIException` | `ModelException` | Ошибки OpenAI API | Проблемы с OpenAI сервисом |
| `GemmaException` | `ModelException` | Ошибки локальных моделей | Проблемы с Ollama/Gemma |

---

## 📝 Логирование

| Тип вывода | Назначение | Формат | Кодировка |
|------------|------------|--------|-----------|
| **Console** | Вывод в консоль | `%(asctime)s [%(levelname)s] %(name)s: %(message)s` | UTF-8 |
| **File** | `text_service.log` | `%(asctime)s [%(levelname)s] %(name)s: %(message)s` | UTF-8 |

### Уровни логирования:
- **INFO**: Основные операции и состояния
- **DEBUG**: Детальная информация о запросах/ответах  
- **WARNING**: Предупреждения и неоптимальные ситуации
- **ERROR**: Ошибки выполнения

---

## 🚀 Запуск сервиса

### Через Docker:
```bash
docker build -t text-service .
docker run -p 8002:8002 -e OPENAI_API_KEY=your_key text-service
```

### Локально:
```bash
pip install -r requirements.txt
python app.py
```

### Через Docker Compose:
```bash
docker-compose up text_service
```

---

## 🧪 Примеры использования

### Базовая генерация текста:
```bash
curl -X POST "http://localhost:8002/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Напиши короткий рассказ о роботе",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

### Генерация с функциями:
```bash
curl -X POST "http://localhost:8002/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Создай 3 сцены для видео о кулинарии",
    "functions": [
      {
        "type": "function", 
        "function": {
          "name": "create_video_scenes",
          "description": "Создание сцен для видео",
          "parameters": {
            "type": "object",
            "properties": {
              "scenes": {
                "type": "array",
                "items": {"type": "string"}
              }
            }
          }
        }
      }
    ]
  }'
```

### Проверка здоровья:
```bash
curl -X GET "http://localhost:8002/health"
```

---

## 📋 Архитектура

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   HTTP Client   │───▶│   Text Service   │───▶│  OpenAI API     │
└─────────────────┘    │   (FastAPI)      │    └─────────────────┘
                       │                  │    
                       │  ┌─────────────┐ │    ┌─────────────────┐
                       │  │  Routes     │ │───▶│  Ollama API     │
                       │  │  Service    │ │    │  (Local)        │
                       │  │  Providers  │ │    └─────────────────┘
                       │  └─────────────┘ │
                       └──────────────────┘
```

---

## 📞 Контакты и поддержка

- **Порт**: 8002
- **Health Check**: `GET /health`
- **API Docs**: `GET /docs` (Swagger UI)
- **Логи**: `text_service.log`

---

*Документация обновлена: 23 июня 2025*
