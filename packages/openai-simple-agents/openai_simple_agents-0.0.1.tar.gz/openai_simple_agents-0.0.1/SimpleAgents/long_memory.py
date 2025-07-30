import chromadb
from chromadb.api.models.Collection import Collection
from openai import OpenAI
from typing import List, Optional, Dict
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
import uuid
import time
import os
import asyncio
from collections import defaultdict
from chromadb.config import Settings

# Фабрика клиентов ChromaDB — обеспечивает переиспользование одного клиента
class ChromaClientFactory:
    _client = None

    @classmethod
    def get_client(cls):
        # Возвращаем уже инициализированный клиент, если он есть
        if cls._client is not None:
            return cls._client
        # Определяем среду: ephemeral (в тестах) или persistent (по умолчанию)
        env = os.getenv("APP_ENV", "production").lower()
        if env == "test":
            cls._client = chromadb.EphemeralClient()
        else:
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
            cls._client = chromadb.PersistentClient(path=persist_dir)
        return cls._client

# Класс долговременной памяти, основанный на векторном хранилище ChromaDB
class LongMemory:
    def __init__(
        self,
        collection_name: str = "long_term_memory",
        openai_api_key: str = "...",
        ttl_seconds: Optional[int] = None,
        client=None,
    ):
        # Инициализация клиента OpenAI и функции эмбеддинга
        self.openai = OpenAI(api_key=openai_api_key)
        self.embedding_fn = OpenAIEmbeddingFunction(
            api_key=openai_api_key,
            model_name="text-embedding-3-small"
        )
        # Получение клиента Chroma
        self.client = client or ChromaClientFactory.get_client()
        # Получение или создание коллекции Chroma
        self.collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine", "hnsw:M": 32, "hnsw:construction_ef": 128},
            embedding_function=self.embedding_fn
        )
        self.ttl_seconds = ttl_seconds
        # Асинхронные блокировки по record_id для защиты от race conditions
        self._locks = defaultdict(asyncio.Lock)

    # Логгирование исключений
    def _log_exception(self, message: str, exc: Exception):
        print(f"[LongMemory] {message}: {type(exc).__name__} - {exc}")

    # Адаптивный выбор числа похожих записей (top_k) по длине текста
    def _adaptive_top_k(self, text: str, max_k: int = 5) -> int:
        length = len(text)
        if length < 100:
            return 1
        elif length < 300:
            return 3
        return max_k

    def _current_timestamp(self) -> float:
        return time.time()

    def _is_expired(self, last_used: float, threshold: float) -> bool:
        return last_used < threshold

    # Обновление timestamp "_last_used" при обращении к записи
    async def _touch_record(self, record_id: str):
        lock = self._locks[record_id]
        async with lock:
            try:
                record = self.collection.get(ids=[record_id])
                if record["metadatas"]:
                    metadata = record["metadatas"][0]
                    metadata["_last_used"] = self._current_timestamp()
                    text = record["documents"][0]
                    self.collection.update(ids=[record_id], documents=[text], metadatas=[metadata])
            except Exception as e:
                self._log_exception(f"_touch_record failed for {record_id}", e)

    # Добавление новой записи в долговременную память
    async def add_record(self, text: str, record_id: Optional[str] = None, metadata: Optional[dict] = None) -> Optional[str]:
        try:
            record_id = record_id or str(uuid.uuid4())
            metadata = metadata or {}
            now = self._current_timestamp()
            metadata.update({"_created": now, "_last_used": now})
            self.collection.add(documents=[text], ids=[record_id], metadatas=[metadata])
            return record_id
        except Exception as e:
            self._log_exception("add_record failed", e)
            return None

    # Удаление записи по ID
    async def delete_record(self, record_id: str):
        try:
            self.collection.delete(ids=[record_id])
        except Exception as e:
            self._log_exception(f"delete_record failed for {record_id}", e)

    # Обновление существующей записи или создание новой, если не существует
    async def upsert_record(self, text: str, record_id: str, metadata: Optional[dict] = None):
        try:
            now = self._current_timestamp()
            metadata = metadata or {}
            try:
                record = self.collection.get(ids=[record_id])
            except Exception:
                record = {"ids": []}
            if record["ids"]:
                old_meta = record["metadatas"][0] or {}
                old_meta.update(metadata)
                old_meta["_last_used"] = now
                self.collection.update(ids=[record_id], documents=[text], metadatas=[old_meta])
                return record_id
            else:
                metadata.update({"_created": now, "_last_used": now})
                self.collection.add(documents=[text], ids=[record_id], metadatas=[metadata])
                return record_id
        except Exception as e:
            self._log_exception("upsert_record failed", e)
            return None

    # Пакетное добавление документов
    async def batch_add(self, texts: List[str], ids: Optional[List[str]] = None, metadatas: Optional[List[dict]] = None):
        try:
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in texts]
            if metadatas is None:
                metadatas = [{} for _ in texts]
            now = self._current_timestamp()
            for meta in metadatas:
                meta.update({"_created": now, "_last_used": now})
            self.collection.add(documents=texts, ids=ids, metadatas=metadatas)
            return ids
        except Exception as e:
            self._log_exception("batch_add failed", e)
            return []

    # Получение всех записей (фильтрация по TTL)
    async def get_all_records(self) -> List[dict]:
        try:
            results = self.collection.get()
            for record_id in results["ids"]:
                await self._touch_record(record_id)
            return [
                {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                for i in range(len(results["documents"]))
                if not self._is_expired(results["metadatas"][i].get("_last_used", 0), self._current_timestamp() - (self.ttl_seconds or 0))
            ]
        except Exception as e:
            self._log_exception("get_all_records failed", e)
            return []

    # Получение записей, связанных с конкретным пользователем
    async def get_user_memory(self, user_id: str) -> List[dict]:
        try:
            results = self.collection.get(where={"user_id": user_id})
            for record_id in results["ids"]:
                await self._touch_record(record_id)
            return [
                {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                }
                for i in range(len(results["documents"]))
                if not self._is_expired(results["metadatas"][i].get("_last_used", 0), self._current_timestamp() - (self.ttl_seconds or 0))
            ]
        except Exception as e:
            self._log_exception(f"get_user_memory failed for {user_id}", e)
            return []

    # Очистка устаревших записей на основе TTL
    async def cleanup_expired(self, *, before: Optional[float] = None):
        if self.ttl_seconds is None:
            return
        try:
            before = before or self._current_timestamp() - self.ttl_seconds
            expired = self.collection.get(where={"_last_used": {"$lt": before}})
            ids_to_delete = expired["ids"]
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
        except Exception as e:
            self._log_exception("cleanup_expired failed", e)