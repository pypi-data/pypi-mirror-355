import asyncio
import itertools
import os
import queue
import threading
import time
import weakref
from concurrent.futures import _base
from concurrent.futures.thread import _shutdown as GLOBAL_INTERPRETER_SHUTDOWN_FLAG
from functools import wraps

from .futures import AsyncFuture
from .futures import AsyncThread
from .scaling import ScalingMixin
from .utils import AsyncThreadSafeEvent
from .utils import AsyncThreadSafeQueue
from .utils import StringWeakReafableKey
from .workers import AsyncWorkerContext
from .workers import AsyncWorkItem
from .workers import async_worker_thread_target


class Scale:
    """
    Глобальный интерфейс для запуска задач в масштабируемом пуле воркеров.
    """
    _executors = set()

    def __init__(self, executor_count=4):
        self._executor_count = executor_count
        # Инициализируем воркеры, cnt потом будет означать количество задач в очереди каждого воркера.
        # Изначально они имеют номера от 0 до executor_count - 1, и задача из глобальной очереди будет отправляться на воркер с наименьшим cnt
        self._terminating = False
        self._initialized = False

    async def _initialize(self):
        try:
            loop = asyncio.get_running_loop()
            self._loop = loop
            self._owns_loop = False
        except RuntimeError:
            loop = asyncio.new_event_loop()
            self._owns_loop = True
            asyncio.set_event_loop(loop)
            self._loop = loop
            self._loop_thread = threading.Thread(target=loop.run_forever, daemon=True)  # Используем не AsyncThread, потому что им нужен ивентлуп
            self._loop_thread.start()

        self._executors = [AsyncThreadPoolExecutor(thread_name_prefix=f'Scale-Executor-{i}', auto_scaling=True) for i in range(self._executor_count)]
        self._executor_load = {executor: cnt for cnt, executor in enumerate(self._executors)}

        """Инициализировать все executor'ы."""
        for i, executor in enumerate(self._executors):
            try:
                # Отправить фиктивную задачу для инициализации воркеров
                dummy_future = await executor.submit(lambda: None)
                await dummy_future
            except Exception as e:
                _base.LOGGER.error(f'Ошибка инициализации executor {i}: {e}')

        self._initialized = True

    async def _submit(self, fn, /, *args, **kwargs):
        """
        Отправить задачу на выполнение.
        """
        if not self._initialized:  # Ленивая инициализация
            await self._initialize()
        curr_loads = []
        for executor in self._executors:
            self._executor_load[executor] = executor.get_queue_size()
            curr_loads.append([executor, self._executor_load[executor]])
        min_load = min(curr_loads, key=lambda x: x[1])

        executor = min_load[0]  # TODO: optimize this shit
        future = await executor.submit(fn, *args, **kwargs)
        return future
    
    async def submit(self, fn, callback, /, *args, **kwargs):
        if self._terminating:
            raise RuntimeError('Scale is terminating')
        future: AsyncFuture = await self._submit(fn, *args, **kwargs)
        if callback:
            future.add_done_callback(Scale.future_callback, callback)
        return future
    
    @staticmethod
    def future_callback(future, /, fn):
        result = future.result()
        return fn(result)

    def scale(self, callback=None):
        """
        Декоратор для scale-функции. Scale функция при await'е возвращает future. Таким образом, функция запускается в отдельном потоке и возвращает future.
        Результат функции получается при await'е future.
        Работает как с sync, так и с async функциями.
        param callback: функция, которая будет вызвана при завершении future с результатом этого future в качестве первого аргумента.
        Пример использования:

        @scale.scale
        async def some_work():
            ... # долгая задача
        result = await some_work() # отправили на выполнение и получили future
        ... # делаем какую-то работу
        await result # получаем результат выполнения функции
        """
        def decorator(fn, /, *args, **kwargs):
            @wraps(fn)
            async def wrapper(*args, **kwargs):
                if self._terminating:
                    raise RuntimeError('Scale is terminating')
                future: AsyncFuture = await self._submit(fn, *args, **kwargs)
                if callback:
                    future.add_done_callback(Scale.future_callback, callback)
                return future
            return wrapper
        return decorator
    
    async def _stop(self):
        self._terminating = True
        while not all(x[1]._done_event.is_set() for x in self._futures.values()):
            await asyncio.sleep(0.1)
        for executor in self._executors:
            await executor.shutdown(wait=True)
        try:
            if self._owns_loop:
                _base.LOGGER.debug('Stopping loop')
                self._loop.stop()
                _base.LOGGER.debug('Loop stopped')
        except Exception as e:
            _base.LOGGER.error(f'Ошибка при завершении Scale: {e}')
            raise

    def stop(self):
        try:
            self._loop.run_until_complete(self._stop)
        except RuntimeError:
            pass  # Loop уже остановлен

    def __del__(self):
        """Автоматическая очистка при сборке мусора."""
        if hasattr(self, '_initialized') and self._initialized and not self._terminating:
            try:
                self.stop()
            except Exception:
                pass  # Игнорировать ошибки при cleanup


class AsyncThreadPoolExecutor(ScalingMixin):
    """
    Executor, использующий AsyncThread с автоматическим масштабированием.
    """

    _counter = itertools.count().__next__

    @classmethod
    def prepare_context(cls, initializer, initargs, **ctxkwargs):
        """Подготовить создание контекста для AsyncWorkerContext."""
        if initializer is not None and not callable(initializer):
            raise TypeError('initializer должен быть вызываемым объектом')

        def create_context():
            return AsyncWorkerContext(initializer, initargs)

        def resolve_task(fn, args, kwargs):
            return (fn, args, kwargs)

        return create_context, resolve_task

    def __init__(self, max_workers=None, thread_name_prefix='', initializer=None, initargs=(), auto_scaling=True, **scaling_config):
        if max_workers is None:
            max_workers = os.cpu_count() * 100  # Это не всегда существующие воркеры, а предел автомасштабирования
        if max_workers <= 0:
            raise ValueError('max_workers должен быть больше 0')

        self._max_workers = max_workers

        (
            self._create_worker_context,
            self._resolve_work_item_task,
        ) = type(self).prepare_context(initializer, initargs)  # Создает функции для создания контекста и разрешения задачи

        self._work_queue = AsyncThreadSafeQueue()
        self._threads = weakref.WeakSet()  # weakset для автоматического удаления воркеров
        self._worker_count = 0
        self._busy_workers = 0  

        self._shutdown_event = AsyncThreadSafeEvent()
        self._shutdown_lock = threading.Lock()

        self._broken_lock = threading.Lock()
        self._broken_message = ''
        self._broken = False

        self._thread_name_prefix = thread_name_prefix or (f'AsyncThreadPool-{type(self)._counter()}')
        self._executor_weakref = weakref.ref(self, self._weakref_callback)

        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self._main_loop = None

        self._auto_scaling_enabled = auto_scaling

        super().__init__()

        self._last_queue_size = 0
        self._task_id_counter = 0

        if auto_scaling:
            self.configure_scaling(max_workers=max_workers, **scaling_config)

    def sleep(self):
        """
        Убивает всех воркеров, кроме кор-воркеров
        """
        for thread in self._threads:
            if not getattr(thread, 'is_core_worker', False) and thread.is_alive():
                thread.mark_for_termination()

    @staticmethod
    def _weakref_callback(executor_ref):
        """Callback при сборке мусора executor."""
        _base.LOGGER.debug('Сработал weakref callback исполнителя.')

    async def submit(self, fn, /, *args, **kwargs):
        """Отправить задачу на выполнение."""
        if self._broken or self._shutdown_event.is_set() or GLOBAL_INTERPRETER_SHUTDOWN_FLAG:
            raise RuntimeError('Исполнитель недоступен')

        if self._main_loop is None:
            try:
                self._main_loop = asyncio.get_running_loop()
            except RuntimeError:
                raise RuntimeError('Невозможно получить main loop')

        future = AsyncFuture()
        task_tuple = self._resolve_work_item_task(fn, args, kwargs)

        # Создать work item с ID для трекинга
        task_id = self._task_id_counter
        self._task_id_counter += 1
        work_item = AsyncWorkItem(future, task_tuple, task_id=task_id)

        # Отследить время отправки
        if hasattr(self, '_track_task_submit'):
            self._track_task_submit(task_id)

        # Обновить метрики
        if hasattr(self, 'metrics'):
            self.metrics.tasks_submitted += 1

        await self._ensure_workers_and_scaling()

        await self._work_queue.put(work_item)

        return future

    async def _ensure_workers_and_scaling(self):
        """Обеспечить наличие воркеров и запустить автомасштабирование."""
        min_workers = getattr(self.scaling_config, 'core_workers', 2) if self._auto_scaling_enabled else 1

        if self._worker_count < min_workers:
            workers_needed = min_workers - self._worker_count
            _base.LOGGER.info(f'Создаем {workers_needed} core воркеров (текущих: {self._worker_count}, нужно: {min_workers})')
            await self._create_initial_workers(workers_needed)

        if self._auto_scaling_enabled and (not hasattr(self, '_scaling_task') or self._scaling_task is None or self._scaling_task.done()):
            try:
                await self.start_scaling()
            except Exception as e:
                _base.LOGGER.error(f'Ошибка запуска автомасштабирования: {e}')

    async def _create_initial_workers(self, count: int):
        """Создать начальные воркеры для немедленного выполнения задач."""
        workers_to_create = min(count, self._max_workers - self._worker_count)

        for i in range(workers_to_create):
            if self._shutdown_event.is_set():
                break

            thread_name = f'{self._thread_name_prefix}-Worker-{self._worker_count}'
            ctx = self._create_worker_context()

            core_workers_limit = getattr(self.scaling_config, 'core_workers', 2)
            is_core = self._worker_count < core_workers_limit
            idle_timeout = float('inf') if is_core else getattr(self.scaling_config, 'worker_idle_timeout', 30.0)

            _base.LOGGER.debug(f'Создаем воркер {thread_name}: is_core={is_core}, idle_timeout={idle_timeout}')

            worker_thread = AsyncThread(
                target=async_worker_thread_target,
                args=(self._executor_weakref, ctx, self._work_queue),
                name=thread_name,
                daemon=True,
                main_loop=self._main_loop,
                idle_timeout=idle_timeout,
                is_core_worker=is_core,
                is_child=False,
            )

            self._threads.add(worker_thread)
            self._worker_count += 1
            worker_thread.start()

    def _worker_exited(self):
        """Вызывается когда worker поток завершается."""
        self._worker_count -= 1

    async def _initializer_failed(self):
        """Обработать ошибку инициализатора."""
        with self._broken_lock:
            if self._broken:
                return
            self._broken = True
            self._broken_message = 'Произошла ошибка при инициализации асинхронного воркера, пул больше не может быть использован.'
            _base.LOGGER.error(self._broken_message)

    async def _signal_shutdown_to_workers(self, clear_queue=True):
        """Сигнализировать завершение всем worker потокам."""
        if clear_queue:
            cancelled_count = 0
            _base.LOGGER.debug(f'Очистка очереди задач ({self._work_queue.qsize()} элементов) и отмена Futures...')
            while True:
                try:
                    work_item = self._work_queue.get_nowait()
                    if work_item is None:  # Если это None-сигнал, вернуть его обратно для другого воркера
                        await self._work_queue.put(None)
                        continue  # Не считать его как отмененную задачу
                    if hasattr(work_item, 'future') and not work_item.future.done():
                        try:
                            work_item.future.cancel()
                            cancelled_count += 1
                        except Exception as e_cancel:
                            _base.LOGGER.error(f'Ошибка при отмене future в _signal_shutdown_to_workers: {e_cancel}', exc_info=True)
                except queue.Empty:
                    break  # Очередь пуста
                except Exception as e_get:
                    _base.LOGGER.error(f'Ошибка при извлечении из очереди в _signal_shutdown_to_workers: {e_get}', exc_info=True)
                    break

            if cancelled_count > 0:
                _base.LOGGER.info(f'Отменено {cancelled_count} невыполненных задач из очереди.')

        num_threads_to_signal = len(self._threads) 
        _base.LOGGER.debug(f'Отправка {num_threads_to_signal} None-сигналов воркерам...')
        for i in range(num_threads_to_signal):
            try:
                await self._work_queue.put(None)
            except Exception as e_put_none:
                _base.LOGGER.error(f'Ошибка при отправке None-сигнала ({i + 1}/{num_threads_to_signal}): {e_put_none}', exc_info=True)

    async def shutdown(self, wait=True, *, cancel_futures=False, timeout=30.0):
        """Завершить executor."""
        with self._shutdown_lock:
            if self._shutdown_event.is_set():
                _base.LOGGER.debug('Shutdown уже вызван, повторный вызов игнорируется.')
                return
            self._shutdown_event.set()

        _base.LOGGER.info(f'Начинается shutdown executor (воркеров: {self._worker_count}, задач в очереди: {self._work_queue.qsize()})')

        if hasattr(self, 'stop_scaling'):
            try:
                _base.LOGGER.debug('Остановка автомасштабирования...')
                await self.stop_scaling()
            except Exception as e:
                _base.LOGGER.error(f'Ошибка остановки автомасштабирования: {e}', exc_info=True)


        if wait and not cancel_futures and self._work_queue.qsize() > 0:
            _base.LOGGER.info(f'Ожидание завершения {self._work_queue.qsize()} задач (таймаут: {timeout}s)...')
            wait_start_time = time.monotonic()
            while self._work_queue.qsize() > 0 and (time.monotonic() - wait_start_time) < timeout:
                try:
                    await asyncio.sleep(0.2) 
                except asyncio.CancelledError:
                    _base.LOGGER.warning('Ожидание завершения задач прервано (CancelledError).')
                    cancel_futures = True  # Переходим к принудительной отмене
                    break

            remaining_tasks = self._work_queue.qsize()
            if remaining_tasks > 0:
                _base.LOGGER.warning(f'Timeout ({timeout}s) при ожидании задач: остается {remaining_tasks}. Переход к принудительной отмене.')
                cancel_futures = True

        _base.LOGGER.debug(f'Сигнализация завершения воркерам (cancel_futures={cancel_futures}).')
        await self._signal_shutdown_to_workers(clear_queue=cancel_futures)

        if wait:
            _base.LOGGER.debug(f'Ожидание завершения всех потоков (таймаут: {timeout}s)...')
            await self._wait_for_threads(timeout=timeout)

        _base.LOGGER.info('Shutdown executor завершен.')

    async def _wait_for_threads(self, timeout=10.0):
        """Ожидать завершения всех потоков с timeout."""
        active_threads = [t for t in list(self._threads) if t.is_alive()]
        if not active_threads:
            _base.LOGGER.debug('Нет активных потоков для ожидания.')
            return

        _base.LOGGER.debug(f'Ожидание завершения {len(active_threads)} активных потоков (таймаут: {timeout}s)...')

        join_tasks = [thread.join() for thread in active_threads]

        try:
            results = await asyncio.wait_for(asyncio.gather(*join_tasks, return_exceptions=True), timeout=timeout)

            for i, res in enumerate(results):
                thread_name = active_threads[i].name or f'Thread-{i}'
                if isinstance(res, Exception):
                    _base.LOGGER.warning(f'Поток {thread_name} завершился с ошибкой во время join: {type(res).__name__}: {res}')
                else:
                    _base.LOGGER.debug(f'Поток {thread_name} успешно завершен (joined).')

        except asyncio.TimeoutError:
            _base.LOGGER.warning(
                f'Timeout ({timeout}s) при ожидании завершения потоков. {len([t for t in active_threads if t.is_alive()])} потоков могут быть еще активны.'
            )
        except asyncio.CancelledError:
            _base.LOGGER.warning('_wait_for_threads был отменен.')
        except Exception as e:  # Другие неожиданные ошибки
            _base.LOGGER.error(f'Неожиданная ошибка в _wait_for_threads: {e}', exc_info=True)

        final_alive_count = len([t for t in self._threads if t.is_alive()])
        _base.LOGGER.debug(f'Завершение ожидания потоков. Осталось активных: {final_alive_count}')

    def get_worker_stats(self):
        """Получить детальную статистику всех воркеров."""
        stats = []
        for thread in self._threads:
            if hasattr(thread, 'get_worker_stats'):
                stats.append(thread.get_worker_stats())
        return stats

    def get_queue_size(self):
        """Получить размер очереди."""
        return self._work_queue.qsize()

    def get_executor_stats(self):
        """Получить общую статистику executor'а."""
        base_stats = {
            'total_workers': self._worker_count,
            'active_threads': len([t for t in self._threads if t.is_alive()]),
            'queue_size': self._work_queue.qsize(),
        }

        return base_stats

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown(wait=True)
        return False
