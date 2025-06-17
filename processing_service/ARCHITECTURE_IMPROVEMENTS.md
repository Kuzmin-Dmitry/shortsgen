# Processing Service - Архитектурные улучшения

## Обзор изменений

Микросервис processing_service был значительно улучшен для повышения надежности, поддерживаемости и масштабируемости.

## Новая архитектура

### 1. Модульная структура

#### ContentGenerator (`content_generator.py`)
- Отвечает за генерацию текстового контента
- Генерация нарратива, описаний сцен, поисковых запросов
- Использует retry-механизмы для устойчивости

#### MediaProcessor (`media_processor.py`)
- Обрабатывает медиа-контент (изображения, аудио, видео)
- Генерация AI-изображений или поиск в интернете
- Композиция финального видео

#### WorkflowOrchestrator (`workflow_orchestrator.py`)
- Координирует весь процесс генерации видео
- Поддерживает разные стратегии генерации
- Централизованное управление workflow

#### TextService (`text_service.py`)
- Унифицированный сервис для работы с текстовыми API
- Обработка различных типов ответов (обычный текст, function calls)
- Структурированные ответы через ModelResponse

### 2. Система устойчивости (`resilience.py`)

#### Retry механизм
```python
@with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
def unreliable_operation():
    # Код, который может упасть
    pass
```

#### Circuit Breaker
```python
circuit_breaker = CircuitBreaker(CircuitBreakerConfig())

@with_circuit_breaker(circuit_breaker)
def external_api_call():
    # Вызов внешнего API
    pass
```

### 3. Управление состоянием (`workflow_state.py`)

#### Отслеживание выполнения
- Детальное логирование каждого этапа
- Информация о времени выполнения
- Обработка ошибок с контекстом

#### Структурированные результаты
```python
@dataclass
class StageResult:
    stage_name: str
    status: StageStatus
    data: Any
    error_message: Optional[str]
    duration_seconds: Optional[float]
```

### 4. Конфигурация (`enhanced_config.py`)

#### Валидация с Pydantic
```python
class ApplicationConfig(BaseModel):
    text_service: ServiceConfig
    audio_service: ServiceConfig
    video_service: ServiceConfig
    scene_count: int = Field(default=6, ge=1, le=20)
```

#### Управление окружением
- Автоматическая загрузка из переменных окружения
- Валидация на этапе запуска
- Поддержка разных окружений (dev, test, prod)

## Использование

### Новый API (рекомендуется)
```python
from workflow_orchestrator import WorkflowOrchestrator, GenerationStrategy

orchestrator = WorkflowOrchestrator()

# AI-генерация изображений
result = orchestrator.execute_workflow(
    strategy=GenerationStrategy.AI_GENERATED,
    custom_prompt="История о космических приключениях"
)

# Поиск изображений в интернете
result = orchestrator.execute_workflow(
    strategy=GenerationStrategy.WEB_SEARCH,
    custom_prompt="Документальный фильм о природе"
)
```

### Legacy API (совместимость)
```python
from generator import Generator

generator = Generator()

# Использует WEB_SEARCH стратегию
result = generator.find_and_generate("Custom prompt")

# Использует AI_GENERATED стратегию
result = generator.ai_generate("Custom prompt")
```

## Преимущества новой архитектуры

### 1. Надежность
- ✅ Retry-механизмы для внешних вызовов
- ✅ Circuit breaker для защиты от каскадных сбоев
- ✅ Graceful degradation при ошибках

### 2. Поддерживаемость
- ✅ Четкое разделение ответственности
- ✅ Модульная архитектура
- ✅ Структурированное логирование

### 3. Масштабируемость
- ✅ Независимые компоненты
- ✅ Возможность параллельного выполнения
- ✅ Легкое добавление новых стратегий

### 4. Качество кода
- ✅ Строгая типизация
- ✅ Валидация конфигурации
- ✅ Удаление дублирования кода

## Миграция

### Обратная совместимость
Старый API Generator сохранен для совместимости:
```python
# Старый код продолжает работать
generator = Generator()
result = generator.find_and_generate()
```

### Рекомендации
1. Новый код должен использовать WorkflowOrchestrator
2. Постепенная миграция существующего кода
3. Тестирование новых компонентов

## Файлы

### Новые модули
- `workflow_orchestrator.py` - Главный оркестратор
- `content_generator.py` - Генерация контента
- `media_processor.py` - Обработка медиа
- `workflow_state.py` - Управление состоянием
- `resilience.py` - Паттерны устойчивости
- `enhanced_config.py` - Улучшенная конфигурация

### Обновленные модули
- `text_service.py` - Унифицированный текстовый сервис
- `generator.py` - Legacy wrapper
- `requirements.txt` - Добавлены новые зависимости

### Удаленные файлы
- `text_client_service.py` - Дублированный код

## Следующие шаги

1. **Тестирование** - Написание тестов для новых компонентов
2. **Мониторинг** - Добавление метрик и трейсинга
3. **Документация** - API документация для новых сервисов
4. **Performance** - Оптимизация производительности workflow
5. **Features** - Добавление новых стратегий генерации
