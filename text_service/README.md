# Text Service v2.0

Микросервис для генерации текста с использованием OpenAI API. Обновлен для работы с новой архитектурой processing-service.

## Новая архитектура (v2.0)

### Основные изменения
- **Redis-based queue system**: слушает очередь `queue:text-service`
- **TaskStatus lifecycle**: `PENDING → QUEUED → PROCESSING → SUCCESS/FAILED`
- **Consumer dependency management**: автоматическое уменьшение queue count для зависимых задач
- **Multiple task types**: поддержка `CreateText` и `CreateSlidePrompt`
- **Model parameter support**: использует `task.params.model` для выбора GPT модели

### Поддерживаемые типы задач

#### CreateText
```yaml
id: "text_task_123"
service: text-service
name: CreateText
prompt: "Напиши короткую историю про кота"
params:
  model: "gpt-4o-mini"
```

#### CreateSlidePrompt  
```yaml
id: "slide_prompt_456"
service: text-service
name: CreateSlidePrompt
prompt: "Создай заголовок для слайда о космосе"
params:
  model: "gpt-3.5-turbo"
```

## Конфигурация

### Переменные окружения
- `OPENAI_API_KEY` - ключ OpenAI API (обязательный)
- `REDIS_HOST` - хост Redis (по умолчанию: redis)
- `REDIS_PORT` - порт Redis (по умолчанию: 6379)
- `REDIS_URL` - полный URL Redis соединения
- `OUTPUT_DIR` - директория для сохранения файлов

### Очереди Redis
- `queue:text-service` - основная очередь для получения задач
- `task:{task_id}` - данные задач в формате Redis Hash

## API

- `GET /health` - проверка состояния сервиса (возвращает версию 2.0.0)

## Workflow

1. **Task Publishing**: processing-service размещает задачи в `queue:text-service`
2. **Task Processing**: text-service забирает задачи и обновляет статус на `PROCESSING`
3. **Text Generation**: генерация текста через OpenAI API
4. **Result Storage**: сохранение результата в файл `/app/output/text/text_{task_id}.txt`
5. **Consumer Triggering**: уменьшение queue count у зависимых задач
6. **Status Update**: финальный статус `SUCCESS` или `FAILED`

## Интеграция с processing-service

Text-service автоматически интегрируется с новой архитектурой:
- Использует тот же формат Task модели
- Совместим с dependency graph системой  
- Поддерживает chain execution через consumers


redis-cli EVAL "
local keys = redis.call('KEYS', 'task:*')
local pairs = {}
for i=1,#keys do
    local status = redis.call('HGET', keys[i], 'status')
    local service = redis.call('HGET', keys[i], 'service')
    if status and service then
        table.insert(pairs, status .. ':' .. service)
    end
end
return pairs
" 0