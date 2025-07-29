import asyncio
import time
from concurrent.futures import _base

import anyio


class AsyncWorkerContext:
    
    @classmethod
    def prepare(cls, initializer, initargs):
        if initializer is not None:
            if not callable(initializer):
                raise TypeError("initializer must be a callable")
        def create_context():
            return cls(initializer, initargs)
        def resolve_task(fn, args, kwargs):
            return (fn, args, kwargs)
        return create_context, resolve_task
    
    def __init__(self, initializer, initargs):
        self.initializer = initializer
        self.initargs = initargs

    async def run(self, task):
        fn, args, kwargs = task
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        else:
            return await anyio.to_thread.run_sync(fn, *args, **kwargs)

    async def initialize(self):
        if self.initializer is not None:
            if asyncio.iscoroutinefunction(self.initializer):
                await self.initializer(*self.initargs)
            else:
                await anyio.to_thread.run_sync(self.initializer, *self.initargs)

    async def finalize(self):
        pass


class AsyncWorkItem:
    def __init__(self, future, task, task_id=None):
        self.future = future
        self.task = task
        self.task_id = task_id  

    async def run(self, ctx):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            result = await ctx.run(self.task)
        except BaseException as exc:
            try:
                if not self.future.done():
                    self.future.set_exception(exc)
                else:
                    _base.LOGGER.debug(f'Future уже завершен при установке исключения: {exc}')
            except Exception as set_exc_error:
                _base.LOGGER.error(f'Не удалось установить исключение для future: {set_exc_error}')
            self = None
        else:
            try:
                if not self.future.done():
                    self.future.set_result(result)
                else:
                    _base.LOGGER.debug('Future уже завершен при установке результата')
            except Exception as set_res_error:
                _base.LOGGER.error(f'Не удалось установить результат для future: {set_res_error}')


async def async_worker_thread_target(actual_async_thread_instance, executor_weak_ref, ctx, work_queue):
    """
    Целевая функция для AsyncThread workers с поддержкой автотерминации.
    Выполняется в отдельном потоке и обрабатывает async work items.
    """
    worker_thread = actual_async_thread_instance
    worker_name = getattr(worker_thread, 'name', 'Unknown')

    _base.LOGGER.debug(f'Воркер {worker_name} стартует (core={getattr(worker_thread, "is_core_worker", False)})')

    try:
        await ctx.initialize()
    except BaseException:
        _base.LOGGER.critical(f'Исключение в асинхронном инициализаторе для {worker_name}:', exc_info=True)
        executor = executor_weak_ref()
        if executor is not None:
            await executor._initializer_failed()
        return

    try:
        while True:
            try:
                work_item = await work_queue.get(timeout=1.0) 
            except asyncio.TimeoutError:
                executor = executor_weak_ref()
                if executor is None or executor._shutdown_event.is_set():
                    _base.LOGGER.debug(f'Воркер {worker_name} завершается: executor shutdown')
                    break

                if getattr(worker_thread, 'is_core_worker', False):
                    continue

                if worker_thread.should_terminate_due_to_idle():
                    _base.LOGGER.debug(f'Non-core воркер {worker_name} завершается из-за бездействия')
                    break

                continue
            except asyncio.CancelledError:
                _base.LOGGER.debug(f'Воркер {worker_name} получил CancelledError - завершение')
                break

            if hasattr(worker_thread, '_idle_cycles'):
                worker_thread._idle_cycles = 0

            worker_thread.update_activity()

            if work_item is None:
                _base.LOGGER.debug(f'Воркер {worker_name} получил shutdown сигнал')

                executor = executor_weak_ref()
                if getattr(worker_thread, 'is_core_worker', False) and executor and not executor._shutdown_event.is_set():
                    _base.LOGGER.debug(f'Core воркер {worker_name} игнорирует преждевременный shutdown')
                    continue

                await work_queue.put(None)
                break

            try:
                start_time = time.time()

                executor = executor_weak_ref()
                if executor and hasattr(executor, '_track_task_start') and hasattr(work_item, 'task_id'):
                    executor._track_task_start(work_item.task_id)

                await work_item.run(ctx)

                worker_thread.tasks_executed += 1
                execution_time = time.time() - start_time
                worker_thread.total_execution_time += execution_time

                executor = executor_weak_ref()
                if executor and hasattr(executor, 'metrics'):
                    executor.metrics.tasks_completed += 1

                _base.LOGGER.debug(f'Воркер {worker_name} завершил задачу, продолжает работу')


            except Exception as exc:
                _base.LOGGER.error(f'Исключение в work_item.run ({worker_name}): {exc}', exc_info=True)
                if hasattr(work_item, 'future') and not work_item.future.done():
                    work_item.future.set_exception(exc)

    except asyncio.CancelledError:
        _base.LOGGER.debug(f'Воркер {worker_name} отменен при завершении программы')
    except BaseException as e:
        _base.LOGGER.critical(f'Необработанное исключение в воркере {worker_name}: {e}', exc_info=True)
    finally:
        await ctx.finalize()

        executor = executor_weak_ref()
        if executor is not None:
            executor._worker_exited()
        _base.LOGGER.debug(f'Воркер {worker_name} завершился')
