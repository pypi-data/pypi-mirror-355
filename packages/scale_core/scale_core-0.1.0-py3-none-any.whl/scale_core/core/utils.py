import asyncio
import queue
import threading
import time
import weakref
from collections import deque


class StringWeakReafableKey:
    """
    Класс для создания слабо ссылающихся ключей.
    Используется для создания ключей для weakref.WeakKeyDictionary.
    Больше не используется в коде, но пусть будет.
    """
    _keys_instances = weakref.WeakValueDictionary()
    _lock = threading.Lock()

    def __new__(cls, key):
        with cls._lock:
            if key in cls._keys_instances:
                return cls._keys_instances[key]

            instance = super().__new__(cls)
            cls._keys_instances[key] = instance
            return instance

    def __init__(self, key):
        if hasattr(self, '_key'):
            return
        self._key = key

    def __str__(self):
        return self._key

    def __repr__(self):
        return f'{self._key}'


class AsyncThreadSafeEvent:
    """
    Асинхронное потокобезопасное событие, которое можно ожидать как из async, так и из sync кода.
    Аналог asyncio.Event | threading.Event.
    """

    def __init__(self):
        self._is_set = False
        self._lock = threading.RLock()
        self._waiters = set()  # Set of (future, loop) tuples for async waiters
        self._sync_event = threading.Event()  # For sync waiters

    def is_set(self):
        with self._lock:
            return self._is_set

    def set(self):
        with self._lock:
            if self._is_set:
                return

            self._is_set = True

            # Notify sync waiters
            self._sync_event.set()

            # Notify async waiters
            for future, loop in list(self._waiters):
                if not future.cancelled():
                    loop.call_soon_threadsafe(future.set_result, True)

            self._waiters.clear()

    def clear(self):
        with self._lock:
            self._is_set = False
            self._sync_event.clear()

    async def wait(self, timeout=None):
        with self._lock:
            if self._is_set:
                return True

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        with self._lock:
            if self._is_set:
                return True

            self._waiters.add((future, loop))

        try:
            if timeout is None:
                return await future
            else:
                return await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            with self._lock:
                self._waiters.discard((future, loop))
            return False
        except asyncio.CancelledError:
            with self._lock:
                self._waiters.discard((future, loop))
            raise

    def wait_sync(self, timeout=None):
        return self._sync_event.wait(timeout)


class AsyncThreadSafeQueue:
    """
    Асинхронная потокобезопасная очередь, которая работает между потоками и event loops.
    Аналог queue.Queue | asyncio.Queue.
    """

    def __init__(self, maxsize=0):
        self._queue = deque()
        self._maxsize = maxsize
        self._lock = threading.RLock()
        self._not_empty = AsyncThreadSafeEvent()
        self._not_full = AsyncThreadSafeEvent()
        self._getters = set()  # Set of (future, loop) tuples
        self._getter_lock = threading.Lock()  # Отдельный lock для getters

        if maxsize <= 0:
            self._not_full.set()

    def qsize(self):
        with self._lock:
            return len(self._queue)

    def empty(self):
        with self._lock:
            return len(self._queue) == 0

    def full(self):
        with self._lock:
            if self._maxsize <= 0:
                return False
            return len(self._queue) >= self._maxsize

    async def put(self, item, timeout=None):
        if self._maxsize > 0:
            while True:
                with self._lock:
                    if len(self._queue) < self._maxsize:
                        break

                if not await self._not_full.wait(timeout):
                    raise asyncio.TimeoutError('Таймаут при добавлении в очередь')

        with self._lock:
            self._queue.append(item)

            self._not_empty.set()

            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                self._not_full.clear()

        with self._getter_lock:
            getter_to_notify = None
            for future, loop in list(self._getters):
                if not future.cancelled():
                    getter_to_notify = (future, loop)
                    self._getters.discard((future, loop))
                    break

            if getter_to_notify:
                future, loop = getter_to_notify
                with self._lock:
                    if self._queue:
                        try:
                            gotten_item = self._queue.popleft()
                            loop.call_soon_threadsafe(self._safe_set_result, future, gotten_item)
                        except IndexError:
                            # Кто-то другой забрал элемент
                            pass

    def _safe_set_result(self, future, result):
        try:
            if not future.done():
                future.set_result(result)
        except Exception:
            # Future уже завершен, игнорируем
            pass

    def put_nowait(self, item):
        with self._lock:
            if self._maxsize > 0 and len(self._queue) >= self._maxsize:
                raise queue.Full('Очередь заполнена')

            self._queue.append(item)
            self._not_empty.set()

        with self._getter_lock:
            getter_to_notify = None
            for future, loop in list(self._getters):
                if not future.cancelled():
                    getter_to_notify = (future, loop)
                    self._getters.discard((future, loop))
                    break

            if getter_to_notify:
                future, loop = getter_to_notify
                with self._lock:
                    if self._queue:
                        try:
                            gotten_item = self._queue.popleft()
                            loop.call_soon_threadsafe(self._safe_set_result, future, gotten_item)
                        except IndexError:
                            pass

    async def get(self, timeout=None):
        with self._lock:
            if self._queue:
                item = self._queue.popleft()

                if self._maxsize > 0:
                    self._not_full.set()

                if not self._queue:
                    self._not_empty.clear()

                return item

        loop = asyncio.get_running_loop()
        future = loop.create_future()

        with self._getter_lock:
            with self._lock:
                if self._queue:
                    item = self._queue.popleft()
                    if self._maxsize > 0:
                        self._not_full.set()
                    if not self._queue:
                        self._not_empty.clear()
                    return item

                self._getters.add((future, loop))

        try:
            if timeout is None:
                return await future
            else:
                return await asyncio.wait_for(future, timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            with self._getter_lock:
                self._getters.discard((future, loop))
            raise

    def get_nowait(self):
        with self._lock:
            if not self._queue:
                raise queue.Empty('Очередь пуста')

            item = self._queue.popleft()

            if self._maxsize > 0:
                self._not_full.set()

            if not self._queue:
                self._not_empty.clear()

            return item

    def put_sync(self, item, block=True, timeout=None):
        if not block:
            return self.put_nowait(item)

        start_time = time.time()
        while True:
            try:
                return self.put_nowait(item)
            except queue.Full:
                if timeout is not None and time.time() - start_time >= timeout:
                    raise
                time.sleep(0.001)  # Small sleep to prevent busy waiting

    def get_sync(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            try:
                return self.get_nowait()
            except queue.Empty:
                if timeout is not None and time.time() - start_time >= timeout:
                    raise
                time.sleep(0.001)  # Small sleep to prevent busy waiting
