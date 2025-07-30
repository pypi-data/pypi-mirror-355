# Очистка внутреннего состояния ChromaDB SharedSystemClient, если оно ранее было инициализировано.
from chromadb.api.shared_system_client import SharedSystemClient
SharedSystemClient._identifier_to_system.clear()

from typing import Optional, List
from agents import Agent as BaseAgent, Runner  # Импорт базового агента и исполнителя цепочек
import asyncio
from SimpleAgents import MemoryManager  # Класс, инкапсулирующий логику работы с кратко- и долговременной памятью
import uuid

class Agent(BaseAgent):
    def __init__(
        self,
        name: str,
        *,
        openai_api_key: str = "...",
        ttl_seconds: Optional[int] = None,  # Время жизни записей в долговременной памяти
        short_memory_max_pairs: int = 10,   # Максимум пар пользователь-агент в кратковременной памяти
        short_memory_ttl_minutes: int = 60, # Время жизни кратковременных сообщений
        short_memory_cleanup_minutes: int = 10,  # Частота фоновой очистки кратковременной памяти
        max_turns: int = 1,  # Максимальное число reasoning-проходов в цепочке
        **kwargs
    ):
        super().__init__(name=name, **kwargs)

        self.max_turns = max_turns

        # Инициализация менеджера памяти для текущего агента
        self.memory_manager = MemoryManager(
            agent_id=name,
            openai_api_key=openai_api_key,
            long_memory_ttl=ttl_seconds,
            short_memory_max_pairs=short_memory_max_pairs,
            short_memory_ttl_minutes=short_memory_ttl_minutes,
            short_memory_cleanup_minutes=short_memory_cleanup_minutes,
        )
        self._initialized = False

    async def init(self):
        # Однократная инициализация memory_manager (idempotent)
        if self._initialized:
            return
        await self.memory_manager.init()
        self._initialized = True

    async def message(
        self,
        input: str,
        *,
        context=None,
        tool_choice: Optional[str] = None,  # Явно заданный инструмент
        max_turns: Optional[int] = None,    # Переопределение числа reasoning-проходов
        enable_tracing: bool = True,        # Включить ли трассировку
        tags: Optional[List[str]] = None,   # Теги для трассировки
        user_id: Optional[str] = None,      # ID пользователя
        file_name: Optional[str] = None,
        file_path: Optional[str] = None,
    ):
        await self.init()
        max_turns = max_turns or self.max_turns

        # Получаем контекст памяти по user_id и текущему запросу
        memory_context = await self.memory_manager.get_memory_context(user_id=user_id, input=input)

        # Если память содержит полезный контекст — вставляем его в prompt
        if memory_context:
            augmented_input = (
                f"Ты — интеллектуальный агент, ведущий диалог с пользователем с ID: {user_id}.\n"
                f"У тебя есть доступ к двум типам памяти для этого пользователя:\n"
                f"1. 🧠 Краткосрочная память — содержит последние сообщения из диалога.\n"
                f"2. 📚 Долговременная память — содержит знания из прошлых взаимодействий.\n\n"
                f"Используй обе памяти, чтобы понять контекст и дать точный, персонализированный ответ.\n\n"
                f"{memory_context}\n\n"
                f"Теперь ответь на вопрос пользователя:\n{input}"
            )
        else:
            augmented_input = input  # Если памяти нет — отправляем сырой запрос

        # Формируем метаданные, включая tool_choice, user_id и прочее
        merged_metadata = {}
        if context and hasattr(context, "metadata") and context.metadata:
            merged_metadata.update(context.metadata)
        for k, v in (("user_id", user_id), ("file_name", file_name), ("file_path", file_path)):
            if v is not None:
                merged_metadata[k] = v

        trace_meta = {}
        if tool_choice is not None:
            merged_metadata["tool_choice"] = tool_choice
            trace_meta["tool_choice"] = tool_choice
        if tags:
            merged_metadata["tags"] = tags
            trace_meta["tags"] = tags

        # Если context отсутствует — создаём временный объект
        if context is None:
            context = type("Ctx", (), {})()
        context.metadata = merged_metadata or None

        # Запуск reasoning-цепочки с использованием Runner
        result = await Runner.run(
            starting_agent=self,
            input=augmented_input,
            context=context,
            max_turns=max_turns,
            run_config={"trace_metadata": trace_meta} if trace_meta else None,
        )

        # Сохраняем взаимодействие в память
        await self.memory_manager.record_interaction(
            user_id=user_id,
            input=input,
            output=result.final_output,
            file_name=file_name,
            file_path=file_path,
        )

        return result  # Возвращаем финальный результат reasoning-процесса