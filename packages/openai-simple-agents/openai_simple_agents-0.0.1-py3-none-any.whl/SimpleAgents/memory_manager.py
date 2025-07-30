import asyncio
import uuid
from typing import Optional, List, Dict

from SimpleAgents import ShortMemory
from SimpleAgents import LongMemory

# Класс, инкапсулирующий работу с кратковременной и долговременной памятью
class MemoryManager:
    def __init__(
        self,
        agent_id: str,  # Уникальный идентификатор агента
        openai_api_key: str,
        *,
        long_memory_ttl: Optional[int] = None,        # TTL для долговременной памяти (в секундах)
        short_memory_max_pairs: int = 10,             # Макс. число пар user/agent в кратковременной памяти
        short_memory_ttl_minutes: int = 60,           # TTL кратковременной памяти (в минутах)
        short_memory_cleanup_minutes: int = 10,       # Интервал очистки кратковременной памяти
    ):
        self.agent_id = agent_id

        # Инициализация долговременной памяти (ChromaDB)
        self.long_memory = LongMemory(
            collection_name=f"long_memory_{agent_id}",
            openai_api_key=openai_api_key,
            ttl_seconds=long_memory_ttl,
        )

        # Инициализация кратковременной памяти (SQLite)
        self.short_memory = ShortMemory(
            max_pairs=short_memory_max_pairs,
            ttl_minutes=short_memory_ttl_minutes,
            cleanup_interval_minutes=short_memory_cleanup_minutes,
            start_auto_cleanup=False  # автоочистку мы запускаем вручную
        )

        self._cleanup_task = None  # Задача фоновой очистки
        self._cleanup_interval = short_memory_cleanup_minutes * 60  # интервал в секундах

    async def init(self):
        # Инициализация кратковременной памяти и запуск фоновой задачи очистки
        await self.short_memory.init()
        self._start_auto_cleanup()

    def _start_auto_cleanup(self):
        # Запускаем фоновую задачу очистки, если она ещё не активна
        if self._cleanup_task is not None:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        self._cleanup_task = loop.create_task(self._auto_cleanup_loop())

    async def _auto_cleanup_loop(self):
        # Бесконечный цикл: через указанный интервал вызывается очистка памяти
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self.cleanup()

    async def shutdown(self):
        # Корректная остановка фоновой задачи
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def cleanup(self):
        # Очистка устаревших данных как в краткосрочной, так и в долговременной памяти
        await self.short_memory.cleanup_expired_dialogs()
        await self.long_memory.cleanup_expired()

    async def get_memory_context(self, user_id: Optional[str], input: str) -> str:
        """
        Получает срез памяти для текущего пользователя и запроса.
        Объединяет записи из кратковременной и долговременной памяти
        """
        memory_context_parts = []

        # Получаем релевантные записи из долговременной памяти
        if user_id:
            memory_records = await self.long_memory.query_by_metadata(
                filter={"user_id": user_id},
                text=input,
                top_k=3,
            )
        else:
            memory_records = await self.long_memory.query_similar(text=input, top_k=3)

        # Формируем текстовый блок из долговременной памяти
        if memory_records:
            long_context = "\n".join([f"- {r['text']}" for r in memory_records])
            memory_context_parts.append(f"[Долговременная память (user_id={user_id})]\n{long_context}")

        # Получаем историю диалога из кратковременной памяти
        if user_id:
            short_history = await self.short_memory.get_history(user_id=user_id, agent_id=self.agent_id)
            if short_history:
                short_context = "\n".join(
                    [f"Пользователь: {pair['user']}\nАгент: {pair.get('agent', '')}" for pair in short_history]
                )
                memory_context_parts.append(f"[Краткосрочная память (user_id={user_id})]\n{short_context}")

        return "\n\n".join(memory_context_parts)

    async def record_interaction(self, *, user_id: Optional[str], input: str, output: str, file_name=None, file_path=None):
        """
        Сохраняет факт взаимодействия с пользователем:
        - в кратковременную память добавляются пары запрос/ответ
        - в долговременную память сохраняются те же фразы с метаданными
        """
        if user_id:
            await self.short_memory.add_message(user_id=user_id, agent_id=self.agent_id, message=input, role="user")
            await self.short_memory.add_message(user_id=user_id, agent_id=self.agent_id, message=output, role="agent")

        # Формируем набор метаданных
        common_md = {k: v for k, v in (("user_id", user_id), ("file_name", file_name), ("file_path", file_path)) if v is not None}

        # Запоминаем в долговременной памяти отдельно вопрос и ответ
        await self.long_memory.add_record(text=input, metadata={**common_md, "role": "user"})
        await self.long_memory.add_record(text=output, metadata={**common_md, "role": "assistant"})