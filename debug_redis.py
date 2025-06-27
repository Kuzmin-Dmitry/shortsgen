#!/usr/bin/env python3
"""
Скрипт для отладки Redis и проверки структуры данных.
"""

import redis
import json
import sys
from typing import Dict, List


def connect_redis() -> redis.Redis:
    """Подключение к Redis."""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"Ошибка подключения к Redis: {e}")
        sys.exit(1)


def analyze_tasks(r: redis.Redis) -> None:
    """Анализ задач в Redis."""
    print("=== АНАЛИЗ ЗАДАЧ В REDIS ===")
    
    # Получаем все ключи задач
    task_keys = r.keys('task:*')
    print(f"Найдено задач: {len(task_keys)}")
    
    if not task_keys:
        print("Задач не найдено")
        return
    
    # Статистика
    stats = {
        'total': len(task_keys),
        'by_status': {},
        'by_service': {},
        'by_queue': {},
        'ready_to_process': 0
    }
    
    print("\n=== ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ===")
    for key in task_keys:
        try:
            task_data = r.hgetall(key)
            if not task_data:
                print(f"ОШИБКА: {key} - пустые данные")
                continue
                
            print(f"\nЗадача: {key}")
            print(f"  ID: {task_data.get('id', 'N/A')}")
            print(f"  Service: {task_data.get('service', 'N/A')}")
            print(f"  Name: {task_data.get('name', 'N/A')}")
            print(f"  Status: {task_data.get('status', 'N/A')}")
            print(f"  Queue: {task_data.get('queue', 'N/A')}")
            
            # Статистика
            status = task_data.get('status', 'unknown')
            service = task_data.get('service', 'unknown')
            queue = task_data.get('queue', '0')
            
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            stats['by_service'][service] = stats['by_service'].get(service, 0) + 1
            stats['by_queue'][queue] = stats['by_queue'].get(queue, 0) + 1
            
            if queue == '0' and status == 'pending':
                stats['ready_to_process'] += 1
                
        except Exception as e:
            print(f"ОШИБКА при обработке {key}: {e}")
    
    print(f"\n=== СТАТИСТИКА ===")
    print(f"Всего задач: {stats['total']}")
    print(f"Готовых к обработке: {stats['ready_to_process']}")
    print(f"По статусам: {stats['by_status']}")
    print(f"По сервисам: {stats['by_service']}")
    print(f"По очереди: {stats['by_queue']}")


def analyze_queues(r: redis.Redis) -> None:
    """Анализ очередей задач."""
    print("\n=== АНАЛИЗ ОЧЕРЕДЕЙ ===")
    
    services = ['text-service', 'voice-service', 'image-service', 'video-service']
    
    for service in services:
        queue_name = f"queue:{service}"
        try:
            length = r.llen(queue_name)
            print(f"{queue_name}: {length} задач")
            
            if length > 0:
                # Показать первые 5 задач
                tasks = r.lrange(queue_name, 0, 4)
                print(f"  Первые задачи: {tasks}")
                
        except Exception as e:
            print(f"ОШИБКА для {queue_name}: {e}")


def check_task_structure(r: redis.Redis, task_id: str) -> None:
    """Детальная проверка структуры конкретной задачи."""
    print(f"\n=== ДЕТАЛЬНАЯ ПРОВЕРКА ЗАДАЧИ {task_id} ===")
    
    try:
        task_key = f"task:{task_id}"
        task_data = r.hgetall(task_key)
        
        if not task_data:
            print(f"Задача {task_id} не найдена")
            return
            
        print("Все поля:")
        for field, value in task_data.items():
            print(f"  {field}: {value} (тип: {type(value)})")
            
        # Проверяем JSON поля
        json_fields = ['consumers', 'slide_ids', 'params']
        for field in json_fields:
            if field in task_data and task_data[field]:
                try:
                    parsed = json.loads(task_data[field])
                    print(f"  {field} (parsed): {parsed}")
                except json.JSONDecodeError as e:
                    print(f"  ОШИБКА JSON в {field}: {e}")
                    
    except Exception as e:
        print(f"ОШИБКА при проверке задачи: {e}")


def clear_redis(r: redis.Redis) -> None:
    """Очистка Redis для тестирования."""
    response = input("Очистить все данные в Redis? (yes/no): ")
    if response.lower() != 'yes':
        print("Отмена")
        return
        
    print("Очистка Redis...")
    
    # Удаляем все задачи
    task_keys = r.keys('task:*')
    if task_keys:
        r.delete(*task_keys)
        print(f"Удалено {len(task_keys)} задач")
    
    # Удаляем все очереди
    queue_keys = r.keys('queue:*')
    if queue_keys:
        r.delete(*queue_keys)
        print(f"Удалено {len(queue_keys)} очередей")
    
    # Удаляем все сценарии
    scenario_keys = r.keys('scenario:*')
    if scenario_keys:
        r.delete(*scenario_keys)
        print(f"Удалено {len(scenario_keys)} сценариев")
        
    print("Очистка завершена")


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python debug_redis.py analyze - анализ данных")
        print("  python debug_redis.py task <task_id> - детальная проверка задачи")
        print("  python debug_redis.py clear - очистка Redis")
        return
    
    r = connect_redis()
    command = sys.argv[1]
    
    if command == 'analyze':
        analyze_tasks(r)
        analyze_queues(r)
    elif command == 'task' and len(sys.argv) > 2:
        task_id = sys.argv[2]
        check_task_structure(r, task_id)
    elif command == 'clear':
        clear_redis(r)
    else:
        print("Неизвестная команда")


if __name__ == "__main__":
    main()
