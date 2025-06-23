# Диаграмма классов для API Gateway

## UML Class Diagram

```mermaid
classDiagram
    class FastAPI {
        +title: str
        +description: str
        +get(path: str)
        +post(path: str)
    }

    class GenerationRequest {
        +custom_prompt: Optional[str]
        +mock: Optional[bool]
        +dict() dict
    }

    class JobStatus {
        +job_id: int
        +status: str
        +message: Optional[str]
        +output_file: Optional[str]
    }

    class APIGatewayApp {
        +app: FastAPI
        +logger: Logger
        +root() dict
        +health() dict
        +generate(request: GenerationRequest) JobStatus
        +generate_from_internet(request: GenerationRequest) JobStatus
        +status(job_id: int) JobStatus
        -_post(endpoint: str, payload: dict) dict
        -_get(endpoint: str) dict
    }

    class Config {
        +PROCESSING_SERVICE_URL: Final[str]
        +load_dotenv()
    }

    class HTTPClient {
        +httpx.AsyncClient
        +post(url: str, json: dict) Response
        +get(url: str) Response
    }

    class Logger {
        +info(message: str)
        +error(message: str)
    }

    %% Relationships
    APIGatewayApp --> FastAPI : uses
    APIGatewayApp --> GenerationRequest : receives
    APIGatewayApp --> JobStatus : returns
    APIGatewayApp --> Config : imports
    APIGatewayApp --> HTTPClient : uses
    APIGatewayApp --> Logger : uses
    
    GenerationRequest --|> BaseModel : inherits
    JobStatus --|> BaseModel : inherits

    %% Notes
    note for APIGatewayApp "Main application class containing\nall API endpoints and business logic"
    note for GenerationRequest "Request model for generation endpoints"
    note for JobStatus "Response model for all endpoints"
```

## Описание компонентов

### Основные классы:

1. **APIGatewayApp** - Главный класс приложения
   - Содержит все эндпоинты API
   - Управляет маршрутизацией запросов к processing service
   - Обрабатывает логику mock режима

2. **GenerationRequest** - Модель запроса
   - Наследуется от Pydantic BaseModel
   - Содержит параметры для генерации контента

3. **JobStatus** - Модель ответа
   - Наследуется от Pydantic BaseModel
   - Представляет статус задачи генерации

4. **Config** - Модуль конфигурации
   - Содержит настройки приложения
   - Управляет переменными окружения

### API Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Корневой эндпоинт, возвращает статус сервиса |
| `/health` | GET | Проверка здоровья сервиса |
| `/generate` | POST | Генерация контента |
| `/generateFromInternet` | POST | Генерация контента из интернета |
| `/status/{job_id}` | GET | Получение статуса задачи |

### Внешние зависимости:

- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **httpx** - HTTP client для асинхронных запросов
- **uvicorn** - ASGI server

### Паттерны проектирования:

1. **Gateway Pattern** - API Gateway маршрутизирует запросы к внутренним сервисам
2. **Proxy Pattern** - Сервис действует как прокси для processing service
3. **Model-View-Controller** - Разделение моделей данных и логики обработки

## Архитектурные особенности:

- **Асинхронная обработка** - Все операции выполняются асинхронно
- **Централизованная маршрутизация** - Единая точка входа для всех запросов
- **Mock режим** - Возможность тестирования без обращения к внешним сервисам
- **Логирование** - Централизованное логирование всех операций
- **Обработка ошибок** - Проксирование ошибок от внутренних сервисов
