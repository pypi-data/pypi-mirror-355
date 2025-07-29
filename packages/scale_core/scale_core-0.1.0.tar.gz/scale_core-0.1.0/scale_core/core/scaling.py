import asyncio
import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional

from scale.core.futures import AsyncThread
from scale.core.workers import async_worker_thread_target

try:
    import psutil
except ImportError:
    psutil = None
from concurrent.futures import _base


@dataclass
class AutoScalingConfig:
    """Конфигурация для автоматического масштабирования воркеров."""

    # Основные параметры
    core_workers: int = max(2, os.cpu_count())
    max_workers: int = 2000
    min_workers: int = 1

    # БОЛЕЕ АГРЕССИВНЫЕ пороги масштабирования
    scale_up_utilization: float = 0.6  # 60% воркеров заняты (было 0.8)
    scale_down_utilization: float = 0.1  # 10% воркеров заняты (было 0.2)

    # БОЛЕЕ АГРЕССИВНЫЕ параметры очереди
    queue_pressure_threshold: float = 1.0  # 1 задача на воркера (было 2.0)
    max_queue_wait_time: float = 0.05  # 50ms максимальное время ожидания (было 0.1)

    # БОЛЕЕ БЫСТРОЕ масштабирование
    scale_up_factor: float = 1.0  # Добавлять 100% от текущих воркеров (было 0.5)
    scale_down_factor: float = 0.1  # Убирать 10% воркеров (было 0.25)
    burst_scale_factor: float = 3.0  # При всплесках утраивать воркеров (было 2.0)

    # БОЛЕЕ БЫСТРЫЕ проверки
    worker_idle_timeout: float = 15.0  # Секунд бездействия (было 30.0)
    scaling_check_interval: float = 0.5  # Интервал проверки (было 1.0)
    metrics_history_size: int = 30  # Размер истории метрик (было 60)

    # Параметры памяти
    max_memory_mb: Optional[float] = None
    memory_pressure_threshold: float = 0.9

    # МЕНЬШИЕ batch'и для быстрого реагирования
    worker_batch_size: int = 5  # (было 20)
    batch_creation_delay: float = 0.001  # (было 0.01)


class WorkerMetrics:
    """Сбор и анализ метрик воркеров."""

    def __init__(self, history_size: int = 60):
        self.history_size = history_size

        # Временные ряды метрик
        self.queue_size_history = deque(maxlen=history_size)
        self.utilization_history = deque(maxlen=history_size)
        self.task_rate_history = deque(maxlen=history_size)
        self.wait_time_history = deque(maxlen=history_size)
        self.memory_usage_history = deque(maxlen=history_size)

        # Текущие метрики
        self.active_workers = 0
        self.busy_workers = 0
        self.core_workers = 0
        self.tasks_completed = 0
        self.tasks_submitted = 0

        # Временные метки
        self.last_metric_time = time.time()
        self.last_task_count = 0

        self._lock = asyncio.Lock()

    async def update_metrics(self, queue_size: int, active_workers: int, busy_workers: int, core_workers: int, avg_wait_time: float = 0.0):
        """Обновить метрики."""
        current_time = time.time()

        async with self._lock:
            # Рассчитать утилизацию
            utilization = busy_workers / max(1, active_workers)

            # Рассчитать темп задач
            time_delta = current_time - self.last_metric_time
            if time_delta > 0:
                tasks_delta = self.tasks_completed - self.last_task_count
                task_rate = tasks_delta / time_delta
            else:
                task_rate = 0.0

            # Получить использование памяти
            try:
                if psutil:
                    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                else:
                    memory_usage = 0.0
            except:
                memory_usage = 0.0

            # Обновить временные ряды
            self.queue_size_history.append(queue_size)
            self.utilization_history.append(utilization)
            self.task_rate_history.append(task_rate)
            self.wait_time_history.append(avg_wait_time)
            self.memory_usage_history.append(memory_usage)

            # Обновить текущие значения
            self.active_workers = active_workers
            self.busy_workers = busy_workers
            self.core_workers = core_workers
            self.last_metric_time = current_time
            self.last_task_count = self.tasks_completed

    async def get_avg_utilization(self, window_size: int = 10) -> float:
        """Получить среднюю утилизацию за окно времени."""
        async with self._lock:
            if not self.utilization_history:
                return 0.0
            recent_data = list(self.utilization_history)[-window_size:]
            return sum(recent_data) / len(recent_data) if recent_data else 0.0

    async def get_avg_queue_size(self, window_size: int = 10) -> float:
        """Получить средний размер очереди."""
        async with self._lock:
            if not self.queue_size_history:
                return 0.0
            recent_data = list(self.queue_size_history)[-window_size:]
            return sum(recent_data) / len(recent_data) if recent_data else 0.0

    async def get_task_rate_trend(self, window_size: int = 10) -> float:
        """Получить тренд темпа задач (положительный = рост, отрицательный = спад)."""
        async with self._lock:
            if len(self.task_rate_history) < window_size:
                return 0.0

            recent_data = list(self.task_rate_history)[-window_size:]
            if len(recent_data) < 2:
                return 0.0

            # Простой линейный тренд
            mid_point = len(recent_data) // 2
            first_half = sum(recent_data[:mid_point]) / mid_point if mid_point > 0 else 0
            second_half_len = len(recent_data) - mid_point
            second_half = sum(recent_data[mid_point:]) / second_half_len if second_half_len > 0 else 0

            return second_half - first_half

    async def predict_load(self, seconds_ahead: int = 10) -> float:
        """Предсказать нагрузку на N секунд вперед."""
        async with self._lock:
            if len(self.task_rate_history) < 5:
                return 0.0

            # Получить текущий темп и тренд
            recent_rate = await self.get_avg_task_rate()
            trend = await self.get_task_rate_trend()

            # Простая экстраполяция
            predicted_rate = recent_rate + (trend * seconds_ahead)
            return max(0.0, predicted_rate * seconds_ahead)  # Общее количество задач

    async def get_avg_task_rate(self, window_size: int = 5) -> float:
        """Получить средний темп задач."""
        async with self._lock:
            if not self.task_rate_history:
                return 0.0
            recent_data = list(self.task_rate_history)[-window_size:]
            return sum(recent_data) / len(recent_data) if recent_data else 0.0

    async def get_memory_usage(self) -> float:
        """Получить текущее использование памяти в MB."""
        async with self._lock:
            if not self.memory_usage_history:
                return 0.0
            return self.memory_usage_history[-1]

    async def is_memory_pressure(self, max_memory_mb: Optional[float]) -> bool:
        """Проверить давление памяти."""
        if max_memory_mb is None:
            return False

        current_memory = await self.get_memory_usage()
        return current_memory >= max_memory_mb * 0.9  # 90% от лимита

    async def detect_burst(self) -> bool:
        """Определить всплеск нагрузки."""
        if len(self.task_rate_history) < 10:
            return False

        async with self._lock:
            recent_rate = await self.get_avg_task_rate(window_size=3)
            baseline_rate = await self.get_avg_task_rate(window_size=10)

        return recent_rate > baseline_rate * 3  # Троекратное увеличение = всплеск


class LoadPredictor:
    """Предиктивный анализ нагрузки."""

    def __init__(self, metrics: WorkerMetrics):
        self.metrics = metrics
        self.time_patterns: Dict[int, float] = {}  # Паттерны по времени дня
        self.day_patterns: Dict[int, float] = {}  # Паттерны по дням недели

    async def learn_patterns(self):
        """Изучить паттерны нагрузки по времени."""
        current_time = time.localtime()
        hour = current_time.tm_hour
        day_of_week = current_time.tm_wday

        current_rate = await self.metrics.get_avg_task_rate()

        # Обновить паттерны (простое скользящее среднее)
        if hour in self.time_patterns:
            self.time_patterns[hour] = 0.9 * self.time_patterns[hour] + 0.1 * current_rate
        else:
            self.time_patterns[hour] = current_rate

        if day_of_week in self.day_patterns:
            self.day_patterns[day_of_week] = 0.9 * self.day_patterns[day_of_week] + 0.1 * current_rate
        else:
            self.day_patterns[day_of_week] = current_rate

    async def predict_future_load(self, minutes_ahead: int = 5) -> float:
        """Предсказать нагрузку через N минут."""
        # Комбинировать тренд-анализ с паттернами времени
        trend_prediction = await self.metrics.predict_load(seconds_ahead=minutes_ahead * 60)

        # Получить ожидаемую нагрузку по времени
        future_time = time.localtime(time.time() + minutes_ahead * 60)
        hour_pattern = self.time_patterns.get(future_time.tm_hour, 0.0)
        day_pattern = self.day_patterns.get(future_time.tm_wday, 0.0)

        # Взвешенная комбинация предсказаний
        pattern_weight = 0.3 if self.time_patterns else 0.0
        trend_weight = 1.0 - pattern_weight

        return trend_weight * trend_prediction + pattern_weight * (hour_pattern + day_pattern) / 2


class ScalingMixin:
    """Mixin для автоматического масштабирования воркеров."""

    def __init__(self, *args, **kwargs):
        # Сначала инициализировать атрибуты масштабирования
        self.scaling_config = AutoScalingConfig()
        self.metrics = WorkerMetrics(self.scaling_config.metrics_history_size)
        self.predictor = LoadPredictor(self.metrics)

        # Состояние масштабирования
        self._scaling_task: Optional[asyncio.Task] = None
        self._last_scale_time = 0.0
        self._scaling_lock = None  # Будет создан позже
        self._terminating_workers = set()  # Воркеры в процессе терминации

        # Отслеживание времени ожидания задач
        self._task_submit_times = {}  # task_id -> submit_time
        self._task_id_counter = 0
        self._task_wait_times = deque(maxlen=100)

        # ВАЖНО: Обнулить счетчики
        self.metrics.tasks_completed = 0
        self.metrics.tasks_submitted = 0

        # Затем вызвать супер-конструктор
        super().__init__(*args, **kwargs)

    def configure_scaling(self, **config_kwargs):
        """Настроить параметры масштабирования."""
        for key, value in config_kwargs.items():
            if hasattr(self.scaling_config, key):
                setattr(self.scaling_config, key, value)

    async def start_scaling(self):
        """Запустить процесс автоматического масштабирования."""
        if self._scaling_lock is None:
            self._scaling_lock = asyncio.Lock()

        if self._scaling_task is None or self._scaling_task.done():
            self._scaling_task = asyncio.create_task(self._scaling_loop())

    async def stop_scaling(self):
        """Остановить процесс автоматического масштабирования."""
        if self._scaling_task and not self._scaling_task.done():
            self._scaling_task.cancel()
            try:
                await self._scaling_task
            except asyncio.CancelledError:
                pass
            self._scaling_task = None

    async def _scaling_loop(self):
        """Основной цикл масштабирования."""
        try:
            while not self._shutdown_event.is_set():
                await asyncio.sleep(self.scaling_config.scaling_check_interval)

                try:
                    await self._perform_scaling_check()
                except asyncio.CancelledError:
                    _base.LOGGER.debug('Задача масштабирования отменена.')
                    break
                except Exception as e:
                    _base.LOGGER.error(f'Ошибка в цикле масштабирования: {e}', exc_info=True)

        except asyncio.CancelledError:
            _base.LOGGER.debug('Основной цикл масштабирования отменен.')
        except KeyboardInterrupt:
            _base.LOGGER.info('KeyboardInterrupt получен в цикле масштабирования.')
        finally:
            _base.LOGGER.debug('Цикл масштабирования завершен.')

    async def _perform_scaling_check(self):
        """Выполнить проверку и масштабирование."""
        try:
            queue_size = 0
            try:
                queue_size = self._work_queue.qsize()
            except (AttributeError, RuntimeError):
                queue_size = getattr(self, '_last_queue_size', 0)

            self._last_queue_size = queue_size
            avg_wait_time = self._calculate_avg_wait_time()

            await self.metrics.update_metrics(
                queue_size=queue_size,
                active_workers=self._worker_count,
                busy_workers=getattr(self, '_busy_workers', 0),
                core_workers=self.scaling_config.core_workers,
                avg_wait_time=avg_wait_time,
            )

            # Изучить паттерны
            await self.predictor.learn_patterns()

            # Принять решение о масштабировании
            if self._scaling_lock:
                try:
                    # Использовать timeout для избежания deadlock
                    await asyncio.wait_for(self._scaling_lock.acquire(), timeout=0.1)
                    try:
                        scaling_decision = await self._make_scaling_decision()

                        if scaling_decision['action'] != 'none':
                            _base.LOGGER.debug(f'Решение о масштабировании: {scaling_decision}')

                        if scaling_decision['action'] == 'scale_up':
                            await self._scale_up(scaling_decision['workers'])
                        elif scaling_decision['action'] == 'scale_down':
                            await self._scale_down(scaling_decision['workers'])
                        elif scaling_decision['action'] == 'burst_scale':
                            await self._burst_scale(scaling_decision['workers'])
                        elif scaling_decision['action'] == 'predictive_scale':
                            await self._predictive_scale(scaling_decision['workers'])
                    finally:
                        self._scaling_lock.release()
                except asyncio.TimeoutError:
                    _base.LOGGER.warning('Таймаут ожидания scaling lock')

        except Exception as e:
            _base.LOGGER.error(f'Ошибка в _perform_scaling_check: {e}', exc_info=True)

    async def _make_scaling_decision(self) -> Dict[str, Any]:
        """Принять решение о масштабировании."""
        current_time = time.time()

        # Проверить ограничения памяти
        if await self.metrics.is_memory_pressure(self.scaling_config.max_memory_mb):
            return {'action': 'none', 'reason': 'memory_pressure'}

        # Кулдаун между масштабированиями
        if current_time - self._last_scale_time < 2.0:  # 2 секунды кулдаун
            return {'action': 'none', 'reason': 'cooldown'}

        try:
            queue_size = self._work_queue.qsize()
        except:
            queue_size = getattr(self, '_last_queue_size', 0)

        try:
            utilization = await self.metrics.get_avg_utilization(window_size=3)
            avg_wait_time = self._calculate_avg_wait_time()

            # === УПРОЩЕННЫЕ ПРАВИЛА МАСШТАБИРОВАНИЯ ===

            # 1. КРИТИЧЕСКОЕ масштабирование вверх - очередь растет быстро
            queue_per_worker = queue_size / max(1, self._worker_count)

            if queue_per_worker > 50:  # >50 задач на воркера = критично
                additional_workers = min(
                    self.scaling_config.max_workers - self._worker_count,
                    max(int(queue_size / 20), 10),  # 1 воркер на 20 задач или минимум 10
                )

                if additional_workers > 0:
                    _base.LOGGER.info(f'АВАРИЙНОЕ масштабирование: очередь={queue_size}, добавляем {additional_workers} воркеров')
                    return {'action': 'burst_scale', 'workers': additional_workers, 'reason': f'critical_queue: {queue_per_worker:.1f} tasks/worker'}

            # 2. Обычное масштабирование вверх - высокая утилизация
            if (
                utilization > self.scaling_config.scale_up_utilization
                and queue_per_worker > 5  # >5 задач на воркера
                and self._worker_count < self.scaling_config.max_workers
            ):
                additional_workers = min(
                    self.scaling_config.max_workers - self._worker_count,
                    max(int(self._worker_count * 0.2), 2),  # 20% или минимум 2
                )

                if additional_workers > 0:
                    return {
                        'action': 'scale_up',
                        'workers': additional_workers,
                        'reason': f'high_utilization: util={utilization:.2f}, queue_per_worker={queue_per_worker:.1f}',
                    }

            non_core_workers = self._worker_count - self.scaling_config.core_workers

            if (
                non_core_workers > 0  # Есть non-core воркеры
                and queue_size < 10  # Очередь почти пуста (было < очень мало)
                and utilization < 0.3  # Низкая утилизация (было 0.1)
                and avg_wait_time < 0.1
            ):
                workers_to_remove = min(
                    max(int(non_core_workers * 0.2), 1),  # 20% или минимум 1
                    non_core_workers,  # Не больше чем есть non-core
                )

                return {
                    'action': 'scale_down',
                    'workers': workers_to_remove,
                    'reason': f'low_load: queue={queue_size}, util={utilization:.2f}, non_core={non_core_workers}',
                }

            return {'action': 'none', 'reason': f'stable: queue={queue_size}, util={utilization:.2f}, workers={self._worker_count}'}

        except Exception as e:
            _base.LOGGER.error(f'Ошибка в _make_scaling_decision: {e}', exc_info=True)
            return {'action': 'none', 'reason': f'error: {e}'}

    async def _scale_up(self, workers_to_add: int):
        """Увеличить количество воркеров."""
        if workers_to_add <= 0:
            return

        _base.LOGGER.debug(f'Масштабирование вверх: добавляем {workers_to_add} воркеров')

        # Создавать воркеров пачками
        batch_size = self.scaling_config.worker_batch_size
        for i in range(0, workers_to_add, batch_size):
            current_batch = min(batch_size, workers_to_add - i)
            await self._create_worker_batch(current_batch)

            if i + batch_size < workers_to_add:  # Если есть еще пачки
                await asyncio.sleep(self.scaling_config.batch_creation_delay)

        self._last_scale_time = time.time()

    async def _scale_down(self, workers_to_remove: int):
        """Уменьшить количество воркеров способом."""
        if workers_to_remove <= 0:
            return

        _base.LOGGER.debug(f'Масштабирование вниз: помечаем {workers_to_remove} воркеров для терминации')

        workers_to_terminate = min(workers_to_remove, self._worker_count - self.scaling_config.core_workers)

        if workers_to_terminate <= 0:
            return

        # Найти и пометить non-core воркеров для терминации
        marked_count = 0
        for thread in list(self._threads):
            if marked_count >= workers_to_terminate:
                break

            # Пометить только non-core воркеров
            if not getattr(thread, 'is_core_worker', False) and thread.is_alive():
                thread.mark_for_termination()
                marked_count += 1
                _base.LOGGER.debug(f'Воркер {thread.name} помечен для терминации')

        self._last_scale_time = time.time()

    async def _burst_scale(self, workers_to_add: int):
        """Быстрое масштабирование при всплесках."""
        _base.LOGGER.info(f'Всплеск нагрузки: добавляем {workers_to_add} воркеров')
        await self._scale_up(workers_to_add)

    async def _predictive_scale(self, workers_to_add: int):
        """Предиктивное масштабирование."""
        _base.LOGGER.debug(f'Предиктивное масштабирование: добавляем {workers_to_add} воркеров')
        await self._scale_up(workers_to_add)

    async def _create_worker_batch(self, batch_size: int):
        """Создать пачку worker потоков с АДАПТИВНЫМ размером."""
        workers_created = 0

        # Адаптивный размер batch'а на основе текущей нагрузки
        current_tps = await self.metrics.get_avg_task_rate()
        queue_size = getattr(self, '_last_queue_size', 0)

        actual_batch_size = int(min(queue_size / current_tps, self._max_workers - self._worker_count))
        delay_between_workers = self.scaling_config.batch_creation_delay

        for i in range(actual_batch_size):
            if self._worker_count >= self._max_workers or self._shutdown_event.is_set():
                break

            thread_name = f'{self._thread_name_prefix}-Worker-{self._worker_count}'
            ctx = self._create_worker_context()

            # Динамически определить тип воркера
            is_core = self._worker_count < self.scaling_config.core_workers

            # Адаптивный timeout на основе текущей нагрузки
            if is_core:
                idle_timeout = float('inf')  # Core воркеры бессмертны
            else:
                # Длинный timeout при высокой нагрузке, короткий при низкой
                base_timeout = self.scaling_config.worker_idle_timeout
                load_factor = min(2.0, queue_size / max(1, self._worker_count * 5))
                idle_timeout = base_timeout * (1 + load_factor)

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
            workers_created += 1

            _base.LOGGER.debug(f'Создан адаптивный воркер {thread_name}: is_core={is_core}, timeout={idle_timeout:.1f}s')

            # Небольшая задержка между созданием воркеров
            if i < actual_batch_size - 1:
                await asyncio.sleep(delay_between_workers)

        return workers_created

    def _calculate_avg_wait_time(self) -> float:
        """Рассчитать среднее время ожидания задач в очереди."""
        if not self._task_wait_times:
            return 0.0
        return sum(self._task_wait_times) / len(self._task_wait_times)

    def _track_task_submit(self, task_id: int):
        """Отследить время отправки задачи."""
        self._task_submit_times[task_id] = time.time()

    def _track_task_start(self, task_id: int):
        """Отследить начало выполнения задачи."""
        if task_id in self._task_submit_times:
            wait_time = time.time() - self._task_submit_times.pop(task_id)
            self._task_wait_times.append(wait_time)

    async def get_scaling_stats(self) -> Dict[str, Any]:
        """Получить статистику масштабирования."""
        return {
            'active_workers': self._worker_count,
            'core_workers': self.scaling_config.core_workers,
            'max_workers': self.scaling_config.max_workers,
            'queue_size': self._work_queue.qsize(),
            'utilization': await self.metrics.get_avg_utilization(),
            'avg_wait_time': self._calculate_avg_wait_time(),
            'memory_usage_mb': await self.metrics.get_memory_usage(),
            'task_rate': await self.metrics.get_avg_task_rate(),
            'predicted_load': await self.predictor.predict_future_load(),
        }
