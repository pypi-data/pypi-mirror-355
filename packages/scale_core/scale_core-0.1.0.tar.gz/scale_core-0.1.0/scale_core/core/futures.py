import asyncio
import threading
import time
from concurrent.futures import _base
from threading import Thread

from .utils import AsyncThreadSafeEvent


class AsyncThread(Thread):
    """Поток, который может выполнять async функции используя main event loop."""

    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None, main_loop=None, idle_timeout=None, is_core_worker=False, is_child=True):
        super().__init__(target=target, args=args, kwargs=kwargs or {}, daemon=daemon, name=name)
        self._completion_event = AsyncThreadSafeEvent()
        self._result = None
        self._exception = None
        self._main_loop = main_loop

        # Параметры автотерминации
        self.idle_timeout = idle_timeout or 30.0  # Секунд бездействия
        self._idle_cycles = 0
        self.is_core_worker = is_core_worker  # Core воркеры не умирают
        self.last_activity = time.time()
        self._should_terminate = AsyncThreadSafeEvent()

        # Статистика
        self.tasks_executed = 0
        self.total_execution_time = 0.0
        self.created_at = time.time()

        # misc
        self.is_child = is_child  # Данный флаг по умолчанию тру, и false ставится только внутри AsyncThreadPoolExecutor, чтобы он корректно обрабатывал все.

    def update_activity(self):
        """Обновить время последней активности."""
        self.last_activity = time.time()

    def request_termination(self):
        """Запросить терминацию потока."""
        self._should_terminate.set()

    def is_termination_requested(self) -> bool:
        """Проверить, запрошена ли терминация."""
        return self._should_terminate.is_set()

    def run(self):
        try:
            if self._target is not None:
                if asyncio.iscoroutinefunction(self._target):
                    if self._main_loop is None:
                        _base.LOGGER.error(f'Поток {self.name or "UnknownThread"}: Main event loop не предоставлен для async функции')
                        self._exception = RuntimeError('Main event loop не предоставлен для async функции')
                        return  # Переход к finally

                    if not self._main_loop.is_running():
                        _base.LOGGER.error(f'Поток {self.name or "UnknownThread"}: Main event loop не запущен. Closed: {self._main_loop.is_closed()}')
                        self._exception = RuntimeError(f'Main event loop не запущен. Closed: {self._main_loop.is_closed()}')
                        return  # Переход к finally

                    if not self.is_child:
                        all_args = (self,) + self._args
                    else:
                        all_args = self._args
                    coro_future = asyncio.run_coroutine_threadsafe(self._target(*all_args, **self._kwargs), self._main_loop)
                    try:
                        self._result = coro_future.result()
                    except asyncio.CancelledError:
                        _base.LOGGER.debug(f'Поток {self.name or "UnknownThread"}: задача coro_future была отменена.')
                        self._exception = asyncio.CancelledError('Задача в run_coroutine_threadsafe была отменена')
                    except Exception as e:
                        _base.LOGGER.error(f'Поток {self.name or "UnknownThread"}: исключение при ожидании coro_future.result(): {e}', exc_info=True)
                        self._exception = e

                else:  # Sync target
                    self._result = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            _base.LOGGER.error(f'Поток {self.name or "UnknownThread"}: необработанное BaseException в run: {type(e).__name__}: {e}', exc_info=True)
            self._exception = e
        finally:
            _base.LOGGER.debug(
                f'Поток {self.name or "UnknownThread"}: установка _completion_event в finally. Exception: {type(self._exception).__name__ if self._exception else "None"}'
            )
            self._completion_event.set()

            # Очистка ссылок
            if hasattr(self, '_target'):
                del self._target
            if hasattr(self, '_args'):
                del self._args
            if hasattr(self, '_kwargs'):
                del self._kwargs

    async def join(self, timeout=None):
        await self._completion_event.wait(timeout)

        if self._exception:
            raise self._exception
        return self._result

    def get_worker_stats(self) -> dict:
        """Получить статистику воркера."""
        uptime = time.time() - self.created_at
        idle_time = time.time() - self.last_activity
        avg_execution_time = self.total_execution_time / self.tasks_executed if self.tasks_executed > 0 else 0.0

        return {
            'name': self.name,
            'is_core_worker': self.is_core_worker,
            'tasks_executed': self.tasks_executed,
            'uptime_seconds': uptime,
            'idle_time_seconds': idle_time,
            'avg_execution_time': avg_execution_time,
            'total_execution_time': self.total_execution_time,
            'is_alive': self.is_alive(),
            'should_terminate': self.should_terminate_due_to_idle(),
        }

    def mark_for_termination(self):
        """Пометить воркера для graceful termination."""
        self._marked_for_termination = True
        self.idle_timeout = 5.0  

    def should_terminate_due_to_idle(self) -> bool:
        if getattr(self, '_marked_for_termination', False):
            return True

        if self.idle_timeout == float('inf'):
            return False

        return time.time() - self.last_activity > self.idle_timeout


class AsyncFuture(_base.Future):
    """
    Объект Future, который можно ожидать.
    """

    def __init__(self):
        super().__init__()
        self._event = AsyncThreadSafeEvent()
        self._lock = threading.Lock()

    async def _get_result_async_helper(self):
        """Вспомогательная корутина для реализации логики await."""
        if not self.done():
            await self._event.wait()

        if self.cancelled():
            raise asyncio.CancelledError()

        _exception = self.exception(timeout=0)
        if _exception is not None:
            raise _exception

        return self.result(timeout=0)

    def __await__(self):
        return self._get_result_async_helper().__await__()

    def not_finished(self):
        return self._state in [_base.PENDING, _base.RUNNING]

    def set_result(self, result):
        with self._lock:
            if not self.not_finished():
                _base.LOGGER.debug(f'Попытка установки результата для Future в состоянии {self._state} (ожидалось PENDING или RUNNING)')
                return
            try:
                super().set_result(result)
            except Exception as e:
                _base.LOGGER.error(f'Ошибка при вызове super().set_result() для Future: {e}', exc_info=True)
                if not self.not_finished():  # Если все еще pending, пытаемся установить ошибку
                    try:
                        self.set_exception(e)
                    except Exception as e_inner:
                        _base.LOGGER.error(f'Вложенная ошибка при попытке установить исключение после ошибки set_result: {e_inner}', exc_info=True)
            finally:
                # Устанавливаем событие только если состояние изменилось успешно или была ошибка,
                # но Future все равно должен сигнализировать о попытке завершения.
                self._event.set()

    def set_exception(self, exception):
        with self._lock:
            if not self.not_finished():
                _base.LOGGER.debug(f'Попытка установки исключения для Future в состоянии {self._state} (ожидалось PENDING или RUNNING)')
                return
            try:
                super().set_exception(exception)
            except Exception as e:
                _base.LOGGER.error(f'Ошибка при вызове super().set_exception() для Future: {e}', exc_info=True)
            finally:
                self._event.set()

    def cancel(self):
        with self._lock:
            if self.done():
                return False

            was_cancelled_by_super = super().cancel()

            if was_cancelled_by_super:
                self._event.set()
            return was_cancelled_by_super

    def set_running_or_notify_cancel(self):
        with self._lock:
            return super().set_running_or_notify_cancel()

    async def join_async(self, timeout=None):
        """Асинхронная версия join с улучшенной обработкой cancellation."""
        try:
            await self._completion_event.wait(timeout)

            if self._exception:
                raise self._exception
            return self._result
        except asyncio.CancelledError:
            _base.LOGGER.debug('Thread join cancelled')
            # Не re-raise, просто return None чтобы shutdown мог продолжиться
            return None
        
    def _invoke_callbacks(self):
        for callback, args, kwargs in self._done_callbacks:
            try:
                callback(self, *args, **kwargs)
            except Exception:
                _base.LOGGER.exception('exception calling callback for %r', self)
        
    def add_done_callback(self, fn, /, *args, **kwargs):
        """
        Переопределяет метод add_done_callback для AsyncFuture, чтобы передавать аргументы в callback.
        """
        with self._condition:
            if self._state not in [_base.CANCELLED, _base.CANCELLED_AND_NOTIFIED, _base.FINISHED]:
                self._done_callbacks.append((fn, args, kwargs))
                return
        try:
            fn(self, *args, **kwargs)
        except Exception:
            _base.LOGGER.exception('exception calling callback for %r', self)
