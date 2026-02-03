"""
Task distribution system for distributed HAAI computation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import asyncio
import logging
import uuid
import time

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Task:
    """Distributed task."""
    task_id: str
    name: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'payload': self.payload,
            'priority': self.priority.value,
            'status': self.status.value,
            'assigned_agent': self.assigned_agent,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'dependencies': self.dependencies,
            'metadata': self.metadata,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary."""
        return cls(
            task_id=data['task_id'],
            name=data['name'],
            payload=data['payload'],
            priority=TaskPriority(data['priority']),
            status=TaskStatus(data['status']),
            assigned_agent=data.get('assigned_agent'),
            result=data.get('result'),
            error=data.get('error'),
            created_at=data.get('created_at', time.time()),
            started_at=data.get('started_at'),
            completed_at=data.get('completed_at'),
            dependencies=data.get('dependencies', []),
            metadata=data.get('metadata', {}),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_id: Optional[str] = None
    timestamp: float = field(default_factory=lambda: time.time())


class TaskExecutor:
    """Base class for task executors."""
    
    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task and return result."""
        pass
    
    @abstractmethod
    def can_execute(self, task: Task) -> bool:
        """Check if executor can execute this task."""
        pass


class FunctionTaskExecutor(TaskExecutor):
    """Task executor that runs Python functions."""
    
    def __init__(self, func: Callable):
        self.func = func
        self.name = func.__name__
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute the function task."""
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(task.payload)
            else:
                result = self.func(task.payload)
            
            return TaskResult(
                task_id=task.task_id,
                success=True,
                result=result,
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    def can_execute(self, task: Task) -> bool:
        """Check if this executor can handle the task."""
        return task.name == self.name or task.metadata.get('executor') == self.name


class TaskScheduler:
    """Distributes tasks across available agents."""
    
    def __init__(self, message_bus=None):
        self.message_bus = message_bus
        self.tasks: Dict[str, Task] = {}
        self.agent_capacity: Dict[str, int] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._result_queue: asyncio.Queue = asyncio.Queue()
        self._executors: Dict[str, TaskExecutor] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._result_worker_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable] = []
    
    def register_executor(self, executor: TaskExecutor) -> None:
        """Register a task executor."""
        self._executors[executor.name] = executor
        logger.info(f"Registered task executor: {executor.name}")
    
    def register_agent(self, agent_id: str, capacity: int = 4) -> None:
        """Register an agent with the scheduler."""
        self.agent_capacity[agent_id] = capacity
        logger.info(f"Registered agent: {agent_id} (capacity: {capacity})")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agent_capacity:
            del self.agent_capacity[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
    
    async def submit_task(self, task: Task) -> str:
        """Submit a task for execution."""
        self.tasks[task.task_id] = task
        await self._task_queue.put(task)
        logger.info(f"Task submitted: {task.task_id} ({task.name})")
        return task.task_id
    
    def submit_task_sync(self, task: Task) -> str:
        """Submit a task synchronously."""
        self.tasks[task.task_id] = task
        # Note: In async context, use submit_task
        logger.info(f"Task submitted (sync): {task.task_id}")
        return task.task_id
    
    def create_task(
        self,
        name: str,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None,
        metadata: Dict = None
    ) -> Task:
        """Create a new task."""
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            name=name,
            payload=payload,
            priority=priority,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        return task
    
    async def get_task_result(self, task_id: str, timeout: float = None) -> TaskResult:
        """Get the result of a task."""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        # Wait for task completion
        while task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            await asyncio.sleep(0.1)
            if timeout:
                elapsed = time.time() - task.created_at
                if elapsed > timeout:
                    raise TimeoutError(f"Task {task_id} timed out")
        
        return TaskResult(
            task_id=task_id,
            success=task.status == TaskStatus.COMPLETED,
            result=task.result,
            error=task.error
        )
    
    def on_result(self, callback: Callable) -> None:
        """Register a callback for task results."""
        self._callbacks.append(callback)
    
    async def start(self) -> None:
        """Start the task scheduler."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_tasks())
        self._result_worker_task = asyncio.create_task(self._process_results())
        logger.info("TaskScheduler started")
    
    async def stop(self) -> None:
        """Stop the task scheduler."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        if self._result_worker_task:
            self._result_worker_task.cancel()
            try:
                await self._result_worker_task
            except asyncio.CancelledError:
                pass
        logger.info("TaskScheduler stopped")
    
    async def _process_tasks(self) -> None:
        """Process tasks from the queue."""
        while self._running:
            try:
                task = await asyncio.wait_for(
                    self._task_queue.get(), timeout=1.0
                )
                await self._execute_task(task)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error: {e}")
    
    async def _process_results(self) -> None:
        """Process task results."""
        while self._running:
            try:
                result = await asyncio.wait_for(
                    self._result_queue.get(), timeout=1.0
                )
                
                # Update task status
                task = self.tasks.get(result.task_id)
                if task:
                    task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                    task.result = result.result
                    task.error = result.error
                    task.completed_at = time.time()
                    
                    # Release agent capacity
                    if task.assigned_agent and task.assigned_agent in self.agent_capacity:
                        self.agent_capacity[task.assigned_agent] += 1
                
                # Call result callbacks
                for callback in self._callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(result)
                        else:
                            callback(result)
                    except Exception as e:
                        logger.error(f"Result callback error: {e}")
                        
            except asyncio.TimeoutError:
                continue
    
    async def _execute_task(self, task: Task) -> None:
        """Execute a task on an available agent."""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        
        try:
            # Find available agent with capacity
            agent_id = await self._find_available_agent()
            
            if agent_id:
                # Reserve capacity
                self.agent_capacity[agent_id] -= 1
                task.assigned_agent = agent_id
                
                # Find executor
                executor = self._find_executor(task)
                
                if executor:
                    # Execute the task
                    result = await executor.execute(task)
                    result.agent_id = agent_id
                    await self._result_queue.put(result)
                else:
                    # No executor found, mark as failed
                    result = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error=f"No executor found for task: {task.name}"
                    )
                    await self._result_queue.put(result)
            else:
                # No agent available, requeue
                await self._task_queue.put(task)
                await asyncio.sleep(0.1)
                
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            await self._result_queue.put(TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e)
            ))
    
    async def _find_available_agent(self) -> Optional[str]:
        """Find an agent with available capacity."""
        for agent_id, capacity in self.agent_capacity.items():
            if capacity > 0:
                return agent_id
        return None
    
    def _find_executor(self, task: Task) -> Optional[TaskExecutor]:
        """Find an executor for the task."""
        # First try by name
        if task.name in self._executors:
            return self._executors[task.name]
        
        # Then try by metadata
        executor_name = task.metadata.get('executor')
        if executor_name and executor_name in self._executors:
            return self._executors[executor_name]
        
        # Return any executor that can handle it
        for executor in self._executors.values():
            if executor.can_execute(task):
                return executor
        
        return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks."""
        return [task.to_dict() for task in self.tasks.values()]
    
    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return self._task_queue.qsize()
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self.tasks.values() if t.status == TaskStatus.RUNNING)
        
        return {
            'total_tasks': len(self.tasks),
            'completed': completed,
            'failed': failed,
            'pending': pending,
            'running': running,
            'queue_size': self._task_queue.qsize(),
            'registered_agents': len(self.agent_capacity),
            'registered_executors': len(self._executors)
        }
