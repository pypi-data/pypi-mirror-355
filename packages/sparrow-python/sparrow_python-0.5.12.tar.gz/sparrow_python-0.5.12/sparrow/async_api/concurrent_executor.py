import asyncio
import time
import itertools
from asyncio import Queue
from typing import Any, Iterable, Optional, Callable, AsyncIterator, AsyncGenerator, Union, Awaitable
from dataclasses import dataclass, field
import heapq

from ..decorators.core import async_retry
from .interface import RequestResult
from .progress import ProgressTracker, ProgressBarConfig


@dataclass
class TaskItem:
    """任务项，支持优先级"""
    priority: int
    task_id: int
    data: Any
    meta: Optional[dict] = field(default_factory=dict)
    
    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class ExecutionResult:
    """执行结果"""
    task_id: int
    data: Any
    status: str  # 'success' or 'error'
    meta: Optional[dict] = None
    latency: float = 0.0
    error: Optional[Exception] = None
    retry_count: int = 0  # 重试次数


@dataclass
class StreamingExecutionResult:
    """流式执行结果"""
    completed_tasks: list[ExecutionResult]
    progress: Optional[ProgressTracker]
    is_final: bool


class RateLimiter:
    """速率限制器"""

    def __init__(self, max_qps: Optional[float] = None):
        self.max_qps = max_qps
        self.min_interval = 1 / max_qps if max_qps else 0
        self.last_request_time = 0

    async def acquire(self):
        if not self.max_qps:
            return

        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request_time = time.time()


class ConcurrentExecutor:
    """
    通用并发执行器
    
    可以对任意的异步函数进行并发调度，支持：
    - 并发数量控制
    - QPS限制
    - 进度跟踪
    - 重试机制
    - 流式结果返回
    - 优先级调度
    - 自定义错误处理
    
    Example
    -------
    
    # 定义一个异步函数
    async def my_async_task(data, meta=None):
        await asyncio.sleep(0.1)  # 模拟异步操作
        return f"processed: {data}"
    
    # 创建执行器
    executor = ConcurrentExecutor(
        concurrency_limit=5,
        max_qps=10,
        retry_times=3
    )
    
    # 准备任务数据
    tasks_data = [f"task_{i}" for i in range(100)]
    
    # 批量执行
    results, progress = await executor.execute_batch(
        async_func=my_async_task,
        tasks_data=tasks_data,
        show_progress=True
    )
    
    # 优先级执行
    priority_tasks = [
        TaskItem(priority=1, task_id=0, data="高优先级任务"),
        TaskItem(priority=3, task_id=1, data="低优先级任务"),
        TaskItem(priority=2, task_id=2, data="中优先级任务"),
    ]
    
    results, _ = await executor.execute_priority_batch(
        async_func=my_async_task,
        priority_tasks=priority_tasks
    )
    """

    def __init__(
            self,
            concurrency_limit: int,
            max_qps: Optional[float] = None,
            retry_times: int = 3,
            retry_delay: float = 0.3,
            error_handler: Optional[Callable[[Exception, Any, int], bool]] = None
    ):
        self._concurrency_limit = concurrency_limit
        self._rate_limiter = RateLimiter(max_qps)
        self._semaphore = asyncio.Semaphore(concurrency_limit)
        self.retry_times = retry_times
        self.retry_delay = retry_delay
        self.error_handler = error_handler  # 自定义错误处理函数

    async def _execute_single_task(
            self,
            async_func: Callable[..., Awaitable[Any]],
            task_data: Any,
            task_id: int,
            meta: Optional[dict] = None,
            **kwargs
    ) -> ExecutionResult:
        """执行单个异步任务"""
        retry_count = 0
        last_error = None
        
        async with self._semaphore:
            while retry_count <= self.retry_times:
                try:
                    await self._rate_limiter.acquire()
                    
                    start_time = time.time()
                    result = await async_func(task_data, meta=meta, **kwargs)
                    latency = time.time() - start_time

                    return ExecutionResult(
                        task_id=task_id,
                        data=result,
                        status="success",
                        meta=meta,
                        latency=latency,
                        retry_count=retry_count
                    )

                except Exception as e:
                    last_error = e
                    retry_count += 1
                    
                    # 调用自定义错误处理函数
                    if self.error_handler:
                        should_retry = self.error_handler(e, task_data, retry_count)
                        if not should_retry:
                            break
                    
                    if retry_count <= self.retry_times:
                        await asyncio.sleep(self.retry_delay)

            # 所有重试都失败了
            return ExecutionResult(
                task_id=task_id,
                data=None,
                status='error',
                meta=meta,
                latency=time.time() - start_time if 'start_time' in locals() else 0,
                error=last_error,
                retry_count=retry_count - 1
            )

    async def _process_with_concurrency_window(
            self,
            async_func: Callable[..., Awaitable[Any]],
            tasks_data: Iterable[Any],
            progress: Optional[ProgressTracker] = None,
            batch_size: int = 1,
            **kwargs
    ) -> AsyncGenerator[StreamingExecutionResult, Any]:
        """
        使用滑动窗口方式处理并发任务，支持流式返回结果
        """

        async def handle_completed_tasks(done_tasks, batch, is_final=False):
            """处理已完成的任务"""
            for task in done_tasks:
                result = await task
                if progress:
                    # 将ExecutionResult转换为RequestResult以兼容ProgressTracker
                    # 对于错误情况，需要构造包含错误信息的data字典
                    progress_data = result.data
                    if result.status == 'error' and result.error:
                        progress_data = {
                            'error': result.error.__class__.__name__,
                            'detail': str(result.error)
                        }
                    
                    request_result = RequestResult(
                        request_id=result.task_id,
                        data=progress_data,
                        status=result.status,
                        meta=result.meta,
                        latency=result.latency
                    )
                    progress.update(request_result)
                batch.append(result)

            if len(batch) >= batch_size or (is_final and batch):
                if is_final and progress:
                    progress.summary()
                yield StreamingExecutionResult(
                    completed_tasks=sorted(batch, key=lambda x: x.task_id),
                    progress=progress,
                    is_final=is_final
                )
                batch.clear()

        task_id = 0
        active_tasks = set()
        completed_batch = []

        # 处理任务数据
        for data in tasks_data:
            if len(active_tasks) >= self._concurrency_limit:
                done, active_tasks = await asyncio.wait(
                    active_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                async for result in handle_completed_tasks(done, completed_batch):
                    yield result

            active_tasks.add(asyncio.create_task(
                self._execute_single_task(async_func, data, task_id, **kwargs)
            ))
            task_id += 1

        # 处理剩余任务
        if active_tasks:
            done, _ = await asyncio.wait(active_tasks)
            async for result in handle_completed_tasks(done, completed_batch, is_final=True):
                yield result

    async def execute_batch(
            self,
            async_func: Callable[..., Awaitable[Any]],
            tasks_data: Iterable[Any],
            total_tasks: Optional[int] = None,
            show_progress: bool = True,
            **kwargs
    ) -> tuple[list[ExecutionResult], Optional[ProgressTracker]]:
        """
        批量执行异步任务
        
        Args:
            async_func: 要执行的异步函数，函数签名应为 async def func(data, meta=None, **kwargs)
            tasks_data: 任务数据列表
            total_tasks: 总任务数量，如果不提供会自动计算
            show_progress: 是否显示进度
            **kwargs: 传递给异步函数的额外参数
            
        Returns:
            (结果列表, 进度跟踪器)
        """
        progress = None
        
        if total_tasks is None and show_progress:
            tasks_data, data_for_counting = itertools.tee(tasks_data)
            total_tasks = sum(1 for _ in data_for_counting)

        if show_progress and total_tasks is not None:
            progress = ProgressTracker(
                total_tasks,
                concurrency=self._concurrency_limit,
                config=ProgressBarConfig()
            )

        results = []
        async for result in self._process_with_concurrency_window(
                async_func=async_func,
                tasks_data=tasks_data,
                progress=progress,
                **kwargs
        ):
            results.extend(result.completed_tasks)

        # 按任务ID排序
        results = sorted(results, key=lambda x: x.task_id)
        return results, progress

    async def _stream_execute(
            self,
            queue: Queue,
            async_func: Callable[..., Awaitable[Any]],
            tasks_data: Iterable[Any],
            total_tasks: Optional[int] = None,
            show_progress: bool = True,
            batch_size: Optional[int] = None,
            **kwargs
    ):
        """流式执行任务并将结果放入队列"""
        progress = None
        if batch_size is None:
            batch_size = self._concurrency_limit
            
        if total_tasks is None and show_progress:
            tasks_data, data_for_counting = itertools.tee(tasks_data)
            total_tasks = sum(1 for _ in data_for_counting)

        if show_progress and total_tasks is not None:
            progress = ProgressTracker(
                total_tasks,
                concurrency=self._concurrency_limit,
                config=ProgressBarConfig()
            )

        async for result in self._process_with_concurrency_window(
                async_func=async_func,
                tasks_data=tasks_data,
                progress=progress,
                batch_size=batch_size,
                **kwargs
        ):
            await queue.put(result)

        await queue.put(None)

    async def aiter_execute_batch(
            self,
            async_func: Callable[..., Awaitable[Any]],
            tasks_data: Iterable[Any],
            total_tasks: Optional[int] = None,
            show_progress: bool = True,
            batch_size: Optional[int] = None,
            **kwargs
    ) -> AsyncIterator[StreamingExecutionResult]:
        """
        流式批量执行异步任务
        
        Args:
            async_func: 要执行的异步函数
            tasks_data: 任务数据列表
            total_tasks: 总任务数量
            show_progress: 是否显示进度
            batch_size: 每次返回的批次大小
            **kwargs: 传递给异步函数的额外参数
            
        Yields:
            StreamingExecutionResult: 包含已完成任务的结果
        """
        queue = Queue()
        task = asyncio.create_task(self._stream_execute(
            queue=queue,
            async_func=async_func,
            tasks_data=tasks_data,
            total_tasks=total_tasks,
            show_progress=show_progress,
            batch_size=batch_size,
            **kwargs
        ))
        
        try:
            while True:
                result = await queue.get()
                if result is None:
                    break
                yield result
        finally:
            if not task.done():
                task.cancel()

    def execute_batch_sync(
            self,
            async_func: Callable[..., Awaitable[Any]],
            tasks_data: Iterable[Any],
            total_tasks: Optional[int] = None,
            show_progress: bool = True,
            **kwargs
    ) -> tuple[list[ExecutionResult], Optional[ProgressTracker]]:
        """同步版本的批量执行"""
        try:
            # 检查是否已经在事件循环中
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用新的线程执行
            import concurrent.futures
            import threading
            
            def run_in_thread():
                return asyncio.run(self.execute_batch(
                    async_func=async_func,
                    tasks_data=tasks_data,
                    total_tasks=total_tasks,
                    show_progress=show_progress,
                    **kwargs
                ))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
                
        except RuntimeError:
            # 没有运行的事件循环，可以直接使用 asyncio.run
            return asyncio.run(self.execute_batch(
                async_func=async_func,
                tasks_data=tasks_data,
                total_tasks=total_tasks,
                show_progress=show_progress,
                **kwargs
            ))

    async def execute_priority_batch(
            self,
            async_func: Callable[..., Awaitable[Any]],
            priority_tasks: list[TaskItem],
            show_progress: bool = True,
            **kwargs
    ) -> tuple[list[ExecutionResult], Optional[ProgressTracker]]:
        """
        按优先级批量执行任务
        
        Args:
            async_func: 要执行的异步函数
            priority_tasks: 带优先级的任务列表 (优先级数字越小越优先)
            show_progress: 是否显示进度
            **kwargs: 传递给异步函数的额外参数
            
        Returns:
            (结果列表, 进度跟踪器)
        """
        # 创建优先级队列
        task_queue = []
        for task in priority_tasks:
            heapq.heappush(task_queue, task)
        
        progress = None
        if show_progress:
            progress = ProgressTracker(
                len(priority_tasks),
                concurrency=self._concurrency_limit,
                config=ProgressBarConfig()
            )

        results = []
        active_tasks = set()
        
        while task_queue or active_tasks:
            # 启动新任务直到达到并发限制
            while len(active_tasks) < self._concurrency_limit and task_queue:
                task_item = heapq.heappop(task_queue)
                coroutine = self._execute_single_task(
                    async_func=async_func,
                    task_data=task_item.data,
                    task_id=task_item.task_id,
                    meta=task_item.meta,
                    **kwargs
                )
                active_tasks.add(asyncio.create_task(coroutine))
            
            # 等待至少一个任务完成
            if active_tasks:
                done, active_tasks = await asyncio.wait(
                    active_tasks,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in done:
                    result = await task
                    results.append(result)
                    
                    if progress:
                        # 转换为RequestResult以兼容ProgressTracker
                        request_result = RequestResult(
                            request_id=result.task_id,
                            data=result.data,
                            status=result.status,
                            meta=result.meta,
                            latency=result.latency
                        )
                        progress.update(request_result)
        
        if progress:
            progress.summary()
        
        # 按任务ID排序
        results = sorted(results, key=lambda x: x.task_id)
        return results, progress

    def add_custom_error_handler(self, handler: Callable[[Exception, Any, int], bool]):
        """
        添加自定义错误处理函数
        
        Args:
            handler: 错误处理函数，签名为 (error, task_data, retry_count) -> should_retry
        """
        self.error_handler = handler 