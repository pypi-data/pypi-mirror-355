import asyncio
import aiosqlite
from typing import Optional
from datetime import datetime, timedelta

# Класс кратковременной памяти. Хранит пары сообщений user/agent в SQLite.
class ShortMemory:
    def __init__(
        self,
        db_path: str = "short_memory.db",              # Путь к SQLite-файлу
        max_pairs: int = 10,                           # Максимум пар user/agent в истории
        ttl_minutes: int = 60,                         # Время хранения записей, мин
        cleanup_interval_minutes: int = 5,             # Частота автоочистки (если активирована)
        start_auto_cleanup: bool = True,               # Флаг автоочистки (не используется здесь)
    ):
        self.db_path = db_path
        self.max_pairs = max_pairs
        self.ttl_minutes = ttl_minutes
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self.start_auto_cleanup = start_auto_cleanup
        self._db: Optional[aiosqlite.Connection] = None  # Подключение к SQLite
        self._initialization_lock = asyncio.Lock()       # Защита от повторной инициализации

    # Унифицированный логгер исключений
    def _log_exception(self, message: str, exc: Exception):
        print(f"[ShortMemory] {message}: {type(exc).__name__} - {exc}")

    # Инициализация базы данных (создание таблицы и индекса)
    async def init(self):
        async with self._initialization_lock:
            if self._db:
                return
            try:
                self._db = await aiosqlite.connect(self.db_path)
                await self._db.execute("""
                    CREATE TABLE IF NOT EXISTS memory (
                        id INTEGER PRIMARY KEY,
                        user_id TEXT,
                        agent_id TEXT,
                        message TEXT,
                        role TEXT,
                        timestamp TEXT
                    )
                """)
                await self._db.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_agent_timestamp
                    ON memory (user_id, agent_id, timestamp)
                """)
                await self._db.commit()
            except Exception as e:
                self._log_exception("init failed", e)
                self._db = None

    # Проверка и восстановление подключения к БД при необходимости
    async def _ensure_db(self):
        if self._db is None:
            await self.init()
        if self._db is None:
            raise RuntimeError("ShortMemory database is not available.")

    # Закрытие соединения с БД
    async def close(self):
        try:
            if self._db:
                await self._db.close()
                self._db = None
        except Exception as e:
            self._log_exception("close failed", e)

    # Добавление сообщения в историю диалога
    async def add_message(self, user_id: str, agent_id: str, message: str, role: str):
        try:
            await self._ensure_db()
            timestamp = datetime.utcnow().isoformat()
            await self._db.execute(
                "INSERT INTO memory (user_id, agent_id, message, role, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, agent_id, message, role, timestamp)
            )
            await self._db.commit()
            # Ограничиваем длину истории
            await self._enforce_max_pairs(user_id, agent_id)
        except Exception as e:
            self._log_exception("add_message failed", e)

    # Удаление старых пар, если превышено max_pairs
    async def _enforce_max_pairs(self, user_id: str, agent_id: str):
        try:
            await self._ensure_db()
            async with self._db.execute("""
                SELECT id FROM memory WHERE user_id = ? AND agent_id = ?
                ORDER BY timestamp DESC
            """, (user_id, agent_id)) as cursor:
                ids = [row[0] async for row in cursor]

            # Храним max_pairs * 2 записей (пары user-agent)
            if len(ids) > self.max_pairs * 2:
                to_delete = ids[self.max_pairs * 2:]
                await self._db.executemany("DELETE FROM memory WHERE id = ?", [(i,) for i in to_delete])
                await self._db.commit()
        except Exception as e:
            self._log_exception("_enforce_max_pairs failed", e)

    # Получение истории сообщений, сгруппированной по парам user/agent
    async def get_history(self, user_id: str, agent_id: str):
        try:
            await self._ensure_db()
            async with self._db.execute("""
                SELECT message, role FROM memory
                WHERE user_id = ? AND agent_id = ?
                ORDER BY timestamp ASC
            """, (user_id, agent_id)) as cursor:
                messages = await cursor.fetchall()

            # Собираем пары (user → agent) для дальнейшего использования в prompt
            pairs = []
            pair = {}
            for msg, role in messages:
                pair[role] = msg
                if "user" in pair and "agent" in pair:
                    pairs.append(pair)
                    pair = {}
            return pairs
        except Exception as e:
            self._log_exception("get_history failed", e)
            return []

    # Очистка устаревших сообщений на основе TTL
    async def cleanup_expired_dialogs(self):
        try:
            await self._ensure_db()
            expiration_threshold = (datetime.utcnow() - timedelta(minutes=self.ttl_minutes)).isoformat()
            await self._db.execute("DELETE FROM memory WHERE timestamp < ?", (expiration_threshold,))
            await self._db.commit()
        except Exception as e:
            self._log_exception("cleanup_expired_dialogs failed", e)