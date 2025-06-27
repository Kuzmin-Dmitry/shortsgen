"""
Redis utility functions for querying task statuses and other fields.
"""

import asyncio
import redis.asyncio as redis
from typing import List, Dict, Set
from config import REDIS_URL, logger


async def get_all_task_statuses() -> List[str]:
    """
    Получить список всех значений поля 'status' из всех задач в Redis.
    
    Returns:
        List[str]: Список всех статусов задач
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        statuses = []
        
        # Метод 1: Сканирование всех ключей задач
        async for key in redis_client.scan_iter(match="task:*"):
            # Получаем только поле status для каждой задачи
            status = redis_client.hget(key, "status")
            if status:
                statuses.append(status)
        
        logger.info(f"Found {len(statuses)} task statuses")
        return statuses
        
    except Exception as e:
        logger.error(f"Error getting task statuses: {e}")
        return []
    finally:
        await redis_client.close()


async def get_unique_task_statuses() -> Set[str]:
    """
    Получить уникальные значения статусов задач.
    
    Returns:
        Set[str]: Множество уникальных статусов
    """
    statuses = await get_all_task_statuses()
    return set(statuses)


async def get_status_distribution() -> Dict[str, int]:
    """
    Получить распределение статусов задач (сколько задач в каждом статусе).
    
    Returns:
        Dict[str, int]: Словарь {статус: количество}
    """
    statuses = await get_all_task_statuses()
    distribution = {}
    
    for status in statuses:
        distribution[status] = distribution.get(status, 0) + 1
    
    return distribution


async def get_tasks_by_status(target_status: str) -> List[Dict]:
    """
    Получить все задачи с определенным статусом.
    
    Args:
        target_status: Искомый статус
        
    Returns:
        List[Dict]: Список данных задач с указанным статусом
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        tasks = []
        
        async for key in redis_client.scan_iter(match="task:*"):
            # Получаем все данные задачи
            task_data = redis_client.hgetall(key)
            
            if task_data.get("status") == target_status:
                tasks.append(task_data)
        
        logger.info(f"Found {len(tasks)} tasks with status '{target_status}'")
        return tasks
        
    except Exception as e:
        logger.error(f"Error getting tasks by status: {e}")
        return []
    finally:
        await redis_client.close()


async def get_all_field_values(field_name: str) -> List[str]:
    """
    Универсальная функция для получения всех значений любого поля.
    
    Args:
        field_name: Имя поля (например, 'status', 'service', 'name')
        
    Returns:
        List[str]: Список всех значений указанного поля
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        values = []
        
        async for key in redis_client.scan_iter(match="task:*"):
            value = await redis_client.hget(key, field_name)
            if value:
                values.append(value)
        
        logger.info(f"Found {len(values)} values for field '{field_name}'")
        return values
        
    except Exception as e:
        logger.error(f"Error getting field values: {e}")
        return []
    finally:
        await redis_client.close()


async def get_bulk_field_values(field_names: List[str]) -> Dict[str, List[str]]:
    """
    Получить значения нескольких полей одним запросом (эффективнее).
    
    Args:
        field_names: Список имен полей
        
    Returns:
        Dict[str, List[str]]: Словарь {поле: [значения]}
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        result = {field: [] for field in field_names}
        
        async for key in redis_client.scan_iter(match="task:*"):
            # Получаем все указанные поля одним запросом
            values = await redis_client.hmget(key, *field_names)
            
            for i, field in enumerate(field_names):
                if values[i]:  # Если значение не None
                    result[field].append(values[i])
        
        for field in field_names:
            logger.info(f"Found {len(result[field])} values for field '{field}'")
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting bulk field values: {e}")
        return {field: [] for field in field_names}
    finally:
        await redis_client.close()


# Альтернативные методы с использованием Redis Lua скриптов для большей эффективности

LUA_GET_ALL_STATUSES = """
local keys = redis.call('KEYS', 'task:*')
local statuses = {}
for i=1,#keys do
    local status = redis.call('HGET', keys[i], 'status')
    if status then
        table.insert(statuses, status)
    end
end
return statuses
"""

async def get_all_statuses_lua() -> List[str]:
    """
    Получить все статусы с помощью Lua скрипта (более эффективно для больших данных).
    
    Returns:
        List[str]: Список всех статусов
    """
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    
    try:
        # Выполняем Lua скрипт
        statuses = await redis_client.eval(LUA_GET_ALL_STATUSES, 0)
        logger.info(f"Found {len(statuses)} statuses using Lua script")
        return statuses
        
    except Exception as e:
        logger.error(f"Error with Lua script: {e}")
        return []
    finally:
        await redis_client.close()


async def demo_redis_queries():
    """Демонстрация всех методов получения статусов."""
    print("🔍 Redis Task Status Queries Demo\n")
    
    # 1. Все статусы
    print("1. Получение всех статусов:")
    statuses = await get_all_task_statuses()
    print(f"   Найдено {len(statuses)} статусов: {statuses[:5]}{'...' if len(statuses) > 5 else ''}")
    
    # 2. Уникальные статусы
    print("\n2. Уникальные статусы:")
    unique_statuses = await get_unique_task_statuses()
    print(f"   Уникальные: {sorted(unique_statuses)}")
    
    # 3. Распределение статусов
    print("\n3. Распределение статусов:")
    distribution = await get_status_distribution()
    for status, count in sorted(distribution.items()):
        print(f"   {status}: {count} задач")
    
    # 4. Задачи по статусу
    if distribution:
        most_common_status = max(distribution.items(), key=lambda x: x[1])[0]
        print(f"\n4. Задачи со статусом '{most_common_status}':")
        tasks = await get_tasks_by_status(most_common_status)
        print(f"   Найдено {len(tasks)} задач")
        if tasks:
            first_task = tasks[0]
            print(f"   Пример: ID={first_task.get('id', 'N/A')}, Name={first_task.get('name', 'N/A')}")
    
    # 5. Значения нескольких полей
    print("\n5. Значения нескольких полей:")
    bulk_data = await get_bulk_field_values(['status', 'service', 'name'])
    for field, values in bulk_data.items():
        unique_values = set(values)
        print(f"   {field}: {len(values)} всего, {len(unique_values)} уникальных")
        print(f"     Уникальные: {sorted(unique_values)}")
    
    # 6. Lua скрипт (если есть данные)
    print("\n6. Lua скрипт метод:")
    lua_statuses = await get_all_statuses_lua()
    print(f"   Lua результат: {len(lua_statuses)} статусов")


if __name__ == "__main__":
    asyncio.run(demo_redis_queries())
