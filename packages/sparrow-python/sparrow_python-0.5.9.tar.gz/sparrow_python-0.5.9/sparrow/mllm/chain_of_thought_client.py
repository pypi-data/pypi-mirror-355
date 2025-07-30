#! /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chain of Thought client for orchestrating multiple LLM calls.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

from sparrow.llm.openaiclient import OpenAIClient


class StepStatus(Enum):
    """步骤执行状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 执行超时
    CANCELLED = "cancelled"  # 执行取消


class ChainStatus(Enum):
    """链条执行状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    TIMEOUT = "timeout"      # 执行超时
    CANCELLED = "cancelled"  # 执行取消


@dataclass
class ExecutionConfig:
    """
    执行配置类。
    
    Attributes:
        step_timeout: 单个步骤的超时时间（秒），None表示无超时
        chain_timeout: 整个链条的超时时间（秒），None表示无超时
        max_retries: 单个步骤的最大重试次数
        retry_delay: 重试间隔时间（秒）
        enable_monitoring: 是否启用监控
        log_level: 日志级别 ("DEBUG", "INFO", "WARNING", "ERROR")
        enable_progress: 是否显示进度信息
    """
    step_timeout: Optional[float] = None
    chain_timeout: Optional[float] = None
    max_retries: int = 0
    retry_delay: float = 1.0
    enable_monitoring: bool = True
    log_level: str = "WARNING"
    enable_progress: bool = False


@dataclass
class StepExecutionInfo:
    """
    步骤执行信息。
    
    Attributes:
        step_name: 步骤名称
        status: 执行状态
        start_time: 开始时间
        end_time: 结束时间
        execution_time: 执行时间
        retry_count: 重试次数
        error: 错误信息
        memory_usage: 内存使用量（可选）
    """
    step_name: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    retry_count: int = 0
    error: Optional[str] = None
    memory_usage: Optional[float] = None


@dataclass
class ChainExecutionInfo:
    """
    链条执行信息。
    
    Attributes:
        chain_id: 链条ID
        status: 执行状态
        start_time: 开始时间
        end_time: 结束时间
        total_execution_time: 总执行时间
        steps_info: 各步骤执行信息
        total_steps: 总步骤数
        completed_steps: 已完成步骤数
        error: 错误信息
    """
    chain_id: str
    status: ChainStatus = ChainStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    total_execution_time: Optional[float] = None
    steps_info: List[StepExecutionInfo] = field(default_factory=list)
    total_steps: int = 0
    completed_steps: int = 0
    error: Optional[str] = None


class ChainMonitor(ABC):
    """链条监控器抽象基类"""
    
    @abstractmethod
    async def on_chain_start(self, chain_info: ChainExecutionInfo) -> None:
        """链条开始执行时调用"""
        pass
    
    @abstractmethod
    async def on_chain_end(self, chain_info: ChainExecutionInfo) -> None:
        """链条执行结束时调用"""
        pass
    
    @abstractmethod
    async def on_step_start(self, step_info: StepExecutionInfo, chain_info: ChainExecutionInfo) -> None:
        """步骤开始执行时调用"""
        pass
    
    @abstractmethod
    async def on_step_end(self, step_info: StepExecutionInfo, chain_info: ChainExecutionInfo) -> None:
        """步骤执行结束时调用"""
        pass
    
    @abstractmethod
    async def on_error(self, error: Exception, chain_info: ChainExecutionInfo) -> None:
        """发生错误时调用"""
        pass
    
    @abstractmethod
    async def on_timeout(self, timeout_type: str, chain_info: ChainExecutionInfo) -> None:
        """超时时调用"""
        pass


class DefaultChainMonitor(ChainMonitor):
    """默认链条监控器实现"""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self.log_levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}
        self.current_level = self.log_levels.get(config.log_level, 1)
    
    def _should_log(self, level: str) -> bool:
        return self.log_levels.get(level, 1) >= self.current_level
    
    def _log(self, level: str, message: str) -> None:
        if self._should_log(level):
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    async def on_chain_start(self, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            self._log("INFO", f"链条 {chain_info.chain_id} 开始执行")
    
    async def on_chain_end(self, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            status_msg = f"链条 {chain_info.chain_id} 执行结束 - 状态: {chain_info.status.value}"
            if chain_info.total_execution_time:
                status_msg += f", 总耗时: {chain_info.total_execution_time:.2f}秒"
            status_msg += f", 完成步骤: {chain_info.completed_steps}/{chain_info.total_steps}"
            self._log("INFO", status_msg)
    
    async def on_step_start(self, step_info: StepExecutionInfo, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            progress = f"({chain_info.completed_steps + 1}/{chain_info.total_steps})"
            self._log("DEBUG", f"步骤 {step_info.step_name} 开始执行 {progress}")
            
            if self.config.enable_progress:
                progress_percent = ((chain_info.completed_steps + 1) / chain_info.total_steps) * 100
                print(f"执行进度: {progress_percent:.1f}% - {step_info.step_name}")
    
    async def on_step_end(self, step_info: StepExecutionInfo, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            status_msg = f"步骤 {step_info.step_name} 执行完成 - 状态: {step_info.status.value}"
            if step_info.execution_time:
                status_msg += f", 耗时: {step_info.execution_time:.2f}秒"
            if step_info.retry_count > 0:
                status_msg += f", 重试次数: {step_info.retry_count}"
            self._log("DEBUG", status_msg)
    
    async def on_error(self, error: Exception, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            self._log("ERROR", f"链条 {chain_info.chain_id} 发生错误: {str(error)}")
    
    async def on_timeout(self, timeout_type: str, chain_info: ChainExecutionInfo) -> None:
        if self.config.enable_monitoring:
            self._log("WARNING", f"链条 {chain_info.chain_id} {timeout_type}超时")


class ExecutionController:
    """执行控制器"""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        self._cancelled = False
    
    def cancel(self) -> None:
        """取消执行"""
        self._cancelled = True
    
    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled
    
    async def check_timeout(self, start_time: float, timeout: Optional[float]) -> bool:
        """检查是否超时"""
        if timeout is None:
            return False
        return (time.time() - start_time) > timeout


@dataclass
class StepResult:
    """
    单个步骤的执行结果。
    
    Attributes:
        step_name: 步骤名称
        messages: 发送给LLM的消息列表
        response: LLM的响应内容
        model_params: 使用的模型参数
        execution_time: 执行时间（秒）
        status: 执行状态
        retry_count: 重试次数
        error: 错误信息（如果有）
    """
    step_name: str
    messages: List[Dict[str, Any]]
    response: str
    model_params: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None
    status: StepStatus = StepStatus.COMPLETED
    retry_count: int = 0
    error: Optional[str] = None


@dataclass
class Context:
    """
    链条执行的上下文信息。
    
    Attributes:
        query: 初始用户查询（可选，用于通用场景）
        history: 所有步骤的执行历史
        custom_data: 自定义数据字典，用于存储任意额外信息
        execution_info: 链条执行信息（用于监控）
    """
    history: List[StepResult] = field(default_factory=list)
    query: Optional[str] = None
    custom_data: Dict[str, Any] = field(default_factory=dict)
    execution_info: Optional[ChainExecutionInfo] = None
    
    def get_last_response(self) -> Optional[str]:
        """获取最后一个步骤的响应。"""
        return self.history[-1].response if self.history else None
    
    def get_response_by_step(self, step_name: str) -> Optional[str]:
        """根据步骤名称获取响应。"""
        for step_result in self.history:
            if step_result.step_name == step_name:
                return step_result.response
        return None
    
    def get_step_count(self) -> int:
        """获取已执行的步骤数量。"""
        return len(self.history)
    
    def add_custom_data(self, key: str, value: Any) -> None:
        """添加自定义数据。"""
        self.custom_data[key] = value
    
    def get_custom_data(self, key: str, default: Any = None) -> Any:
        """获取自定义数据。"""
        return self.custom_data.get(key, default)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要信息"""
        total_time = sum(s.execution_time or 0 for s in self.history)
        total_retries = sum(s.retry_count for s in self.history)
        failed_steps = [s.step_name for s in self.history if s.status == StepStatus.FAILED]
        
        return {
            "total_steps": len(self.history),
            "total_execution_time": total_time,
            "total_retries": total_retries,
            "failed_steps": failed_steps,
            "success_rate": len([s for s in self.history if s.status == StepStatus.COMPLETED]) / len(self.history) if self.history else 0
        }


@dataclass
class Step:
    """
    定义思想链中的一个步骤。

    Attributes:
        name: 步骤的唯一名称。
        prepare_messages_fn: 一个可调用对象，接收上下文（Context），返回用于LLM调用的消息列表（List[Dict]）。
        get_next_step_fn: 一个可调用对象，接收当前步骤的响应（str）和完整上下文（Context），返回下一个步骤的名称（str）或None表示结束。
        model_params: 调用LLM时使用的模型参数，例如 model, temperature等。
    """
    name: str
    prepare_messages_fn: Callable[[Context], List[Dict[str, Any]]]
    get_next_step_fn: Callable[[str, Context], Optional[str]]
    model_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LinearStep:
    """
    定义线性链条中的一个步骤（简化版本）。
    
    Attributes:
        name: 步骤的唯一名称。
        prepare_messages_fn: 一个可调用对象，接收上下文（Context），返回用于LLM调用的消息列表（List[Dict]）。
        model_params: 调用LLM时使用的模型参数，例如 model, temperature等。
    """
    name: str
    prepare_messages_fn: Callable[[Context], List[Dict[str, Any]]]
    model_params: Dict[str, Any] = field(default_factory=dict)


class ChainOfThoughtClient:
    """
    一个客户端，用于执行由多个步骤组成的思想链（Chain of Thought）。
    它允许根据一个模型调用的结果动态决定下一个调用的模型和内容。
    """

    def __init__(self, openai_client: OpenAIClient, execution_config: Optional[ExecutionConfig] = None):
        """
        初始化思想链客户端。

        Args:
            openai_client: 一个 OpenAIClient 实例，用于执行底层的LLM调用。
            execution_config: 执行配置，如果为None则使用默认配置。
        """
        self.openai_client = openai_client
        self.steps: Dict[str, Step] = {}
        self.execution_config = execution_config or ExecutionConfig()
        self.monitor: ChainMonitor = DefaultChainMonitor(self.execution_config)
        self._chain_counter = 0

    def set_monitor(self, monitor: ChainMonitor) -> None:
        """设置自定义监控器"""
        self.monitor = monitor

    def add_step(self, step: Step):
        """
        向客户端注册一个步骤。

        Args:
            step: 一个 Step 实例。
        """
        if step.name in self.steps:
            raise ValueError(f"步骤 '{step.name}' 已存在。请确保每个步骤名称唯一。")
        self.steps[step.name] = step

    def add_steps(self, steps: List[Step]):
        """
        向客户端批量注册多个步骤。

        Args:
            steps: Step 实例的列表。
        """
        for step in steps:
            self.add_step(step)

    def create_linear_chain(self, linear_steps: List[LinearStep], chain_name: str = "linear_chain"):
        """
        创建一个线性的步骤链条，每个步骤按顺序执行。
        
        Args:
            linear_steps: LinearStep 实例的列表，按执行顺序排列。
            chain_name: 链条的名称前缀。
        """
        if not linear_steps:
            raise ValueError("线性链条至少需要一个步骤。")
        
        def create_next_step_fn(current_index: int, total_steps: int):
            """为线性链条创建next_step函数"""
            def next_step_fn(response: str, context: Context) -> Optional[str]:
                if current_index < total_steps - 1:
                    return f"{chain_name}_{current_index + 1}"
                else:
                    return None  # 结束链条
            return next_step_fn
        
        # 转换LinearStep为Step并注册
        for i, linear_step in enumerate(linear_steps):
            step_name = f"{chain_name}_{i}"
            full_step = Step(
                name=step_name,
                prepare_messages_fn=linear_step.prepare_messages_fn,
                get_next_step_fn=create_next_step_fn(i, len(linear_steps)),
                model_params=linear_step.model_params
            )
            self.add_step(full_step)
        
        return f"{chain_name}_0"  # 返回第一个步骤的名称

    def create_context(self, initial_data: Optional[Dict[str, Any]] = None) -> Context:
        """
        创建一个新的上下文对象。
        
        Args:
            initial_data: 初始数据字典，可以包含 'query' 和其他自定义字段
            
        Returns:
            新创建的Context对象
        """
        if initial_data is None:
            return Context()
        
        # 提取特殊字段
        query = initial_data.get('query')
        
        # 剩余字段作为custom_data
        custom_data = {k: v for k, v in initial_data.items() if k != 'query'}
        
        return Context(
            query=query,
            custom_data=custom_data
        )

    def _generate_chain_id(self) -> str:
        """生成链条ID"""
        self._chain_counter += 1
        return f"chain_{self._chain_counter}_{int(time.time())}"

    async def _execute_step_with_retry(
        self,
        step: Step,
        context: Context,
        controller: ExecutionController,
        step_info: StepExecutionInfo,
        chain_info: ChainExecutionInfo,
        show_step_details: bool = False
    ) -> Optional[str]:
        """执行单个步骤，包含重试逻辑"""
        last_error = None
        
        for attempt in range(self.execution_config.max_retries + 1):
            if controller.is_cancelled():
                step_info.status = StepStatus.CANCELLED
                return None
            
            step_info.retry_count = attempt
            
            try:
                # 准备消息
                messages = step.prepare_messages_fn(context)
                
                # 显示步骤详细信息 - 输入
                if show_step_details:
                    print(f"\n📝 步骤 '{step_info.step_name}' 输入消息:")
                    for i, msg in enumerate(messages):
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        print(f"   {i+1}. [{role}]: {content[:100]}{'...' if len(content) > 100 else ''}")
                    print(f"🔧 模型参数: {step.model_params}")
                    if attempt > 0:
                        print(f"🔄 重试第 {attempt} 次")
                
                # 执行LLM调用
                start_time = time.time()
                
                # 创建超时任务
                llm_task = self.openai_client.chat_completions(
                    messages=messages,
                    preprocess_msg=True,
                    show_progress=False,  # LLM调用的进度条始终关闭
                    **step.model_params
                )
                
                if self.execution_config.step_timeout:
                    response_content = await asyncio.wait_for(
                        llm_task, 
                        timeout=self.execution_config.step_timeout
                    )
                else:
                    response_content = await llm_task
                
                execution_time = time.time() - start_time
                step_info.execution_time = execution_time
                
                if response_content is None or not isinstance(response_content, str):
                    raise ValueError("LLM调用返回空响应")
                
                # 显示步骤详细信息 - 输出
                if show_step_details:
                    print(f"✅ 步骤 '{step_info.step_name}' 输出响应:")
                    print(f"   📄 响应内容: {response_content[:200]}{'...' if len(response_content) > 200 else ''}")
                    print(f"   ⏱️  执行时间: {execution_time:.3f}秒")
                    if attempt > 0:
                        print(f"   🔄 重试成功")
                
                step_info.status = StepStatus.COMPLETED
                return response_content
                
            except asyncio.TimeoutError:
                step_info.status = StepStatus.TIMEOUT
                step_info.error = f"步骤执行超时（{self.execution_config.step_timeout}秒）"
                if show_step_details:
                    print(f"⏰ 步骤 '{step_info.step_name}' 执行超时")
                    print(f"   ⚠️  超时时间: {self.execution_config.step_timeout}秒")
                await self.monitor.on_timeout("step", chain_info)
                last_error = TimeoutError(step_info.error)
                
            except Exception as e:
                step_info.status = StepStatus.FAILED
                step_info.error = str(e)
                if show_step_details:
                    print(f"❌ 步骤 '{step_info.step_name}' 执行失败")
                    print(f"   🐛 错误类型: {type(e).__name__}")
                    print(f"   📝 错误信息: {str(e)}")
                    if attempt < self.execution_config.max_retries:
                        print(f"   🔄 将在 {self.execution_config.retry_delay}秒后重试...")
                last_error = e
                await self.monitor.on_error(e, chain_info)
            
            # 如果不是最后一次尝试，等待重试间隔
            if attempt < self.execution_config.max_retries:
                await asyncio.sleep(self.execution_config.retry_delay)
        
        # 所有重试都失败了
        if last_error:
            raise last_error
        
        return None

    async def execute_chain(
        self,
        initial_step_name: str,
        initial_context: Optional[Union[Dict[str, Any], Context]] = None,
        show_step_details: bool = False
    ) -> Context:
        """
        异步执行一个完整的思想链。

        Args:
            initial_step_name: 起始步骤的名称。
            initial_context: 传递给第一个步骤的初始上下文，可以是字典或Context对象。
            show_step_details: 是否显示每个步骤的详细信息（输入消息、输出响应、执行时间等）。

        Returns:
            返回包含所有步骤历史记录的最终上下文。
        """
        if initial_step_name not in self.steps:
            raise ValueError(f"起始步骤 '{initial_step_name}' 未注册。")

        # 处理初始上下文
        if isinstance(initial_context, Context):
            context = initial_context
        elif isinstance(initial_context, dict):
            context = self.create_context(initial_context)
        else:
            context = Context()
        
        # 创建执行信息和控制器
        chain_id = self._generate_chain_id()
        chain_info = ChainExecutionInfo(
            chain_id=chain_id,
            status=ChainStatus.RUNNING,
            start_time=time.time()
        )
        context.execution_info = chain_info
        
        controller = ExecutionController(self.execution_config)
        
        # 估算总步骤数（简单预估）
        chain_info.total_steps = len(self.steps)  # 这是一个保守估计
        
        try:
            await self.monitor.on_chain_start(chain_info)
            
            current_step_name: Optional[str] = initial_step_name
            chain_start_time = time.time()

            while current_step_name:
                # 检查链条超时
                if self.execution_config.chain_timeout:
                    if await controller.check_timeout(chain_start_time, self.execution_config.chain_timeout):
                        chain_info.status = ChainStatus.TIMEOUT
                        await self.monitor.on_timeout("chain", chain_info)
                        break
                
                # 检查取消状态
                if controller.is_cancelled():
                    chain_info.status = ChainStatus.CANCELLED
                    break
                
                if current_step_name not in self.steps:
                    raise ValueError(f"执行过程中发现未注册的步骤 '{current_step_name}'。")

                step = self.steps[current_step_name]
                
                # 创建步骤执行信息
                step_info = StepExecutionInfo(
                    step_name=current_step_name,
                    status=StepStatus.RUNNING,
                    start_time=time.time()
                )
                
                chain_info.steps_info.append(step_info)
                await self.monitor.on_step_start(step_info, chain_info)

                try:
                    # 执行步骤（包含重试逻辑）
                    response_content = await self._execute_step_with_retry(
                        step, context, controller, step_info, chain_info, show_step_details
                    )
                    
                    if response_content is None:
                        break  # 步骤执行失败或被取消
                    
                    step_info.end_time = time.time()
                    step_info.execution_time = step_info.end_time - (step_info.start_time or 0)
                    
                    # 记录步骤结果
                    step_result = StepResult(
                        step_name=current_step_name,
                        messages=step.prepare_messages_fn(context),
                        response=response_content,
                        model_params=step.model_params,
                        execution_time=step_info.execution_time,
                        status=step_info.status,
                        retry_count=step_info.retry_count,
                        error=step_info.error
                    )
                    context.history.append(step_result)
                    
                    chain_info.completed_steps += 1
                    await self.monitor.on_step_end(step_info, chain_info)

                    # 决定下一步
                    next_step_name = step.get_next_step_fn(response_content, context)
                    current_step_name = next_step_name
                    
                except Exception as e:
                    step_info.status = StepStatus.FAILED
                    step_info.error = str(e)
                    step_info.end_time = time.time()
                    
                    await self.monitor.on_step_end(step_info, chain_info)
                    await self.monitor.on_error(e, chain_info)
                    
                    chain_info.status = ChainStatus.FAILED
                    chain_info.error = str(e)
                    break

            # 设置链条结束状态
            chain_info.end_time = time.time()
            chain_info.total_execution_time = chain_info.end_time - chain_info.start_time
            
            if chain_info.status == ChainStatus.RUNNING:
                chain_info.status = ChainStatus.COMPLETED
            
            await self.monitor.on_chain_end(chain_info)

        except Exception as e:
            chain_info.status = ChainStatus.FAILED
            chain_info.error = str(e)
            chain_info.end_time = time.time()
            if chain_info.start_time:
                chain_info.total_execution_time = chain_info.end_time - chain_info.start_time
            
            await self.monitor.on_error(e, chain_info)
            await self.monitor.on_chain_end(chain_info)
            raise

        return context

    async def execute_chains_batch(
        self,
        chain_requests: List[Dict[str, Any]],
        show_step_details: bool = False
    ) -> List[Context]:
        """
        并发执行多个思想链。

        Args:
            chain_requests: 一个请求列表，每个请求是一个字典，包含 'initial_step_name' 和 'initial_context'。
                例如: [{'initial_step_name': 'step1', 'initial_context': {'query': '你好'}}]
            show_step_details: 是否显示每个步骤的详细信息（输入消息、输出响应、执行时间等）。

        Returns:
            一个结果列表，每个元素是对应调用链的最终上下文。
        """
        tasks = []
        for request in chain_requests:
            task = self.execute_chain(
                initial_step_name=request['initial_step_name'],
                initial_context=request.get('initial_context'),
                show_step_details=show_step_details
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                # 创建一个错误上下文
                error_context = Context()
                error_context.execution_info = ChainExecutionInfo(
                    chain_id=self._generate_chain_id(),
                    status=ChainStatus.FAILED,
                    error=str(result)
                )
                final_results.append(error_context)
            else:
                final_results.append(result)
        
        return final_results 