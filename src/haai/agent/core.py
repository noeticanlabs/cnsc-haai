"""
HAAI Agent Core Architecture

Implements the core agent lifecycle management, state persistence,
communication protocols, resource management, and health monitoring.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta

from ..core import CoherenceEngine, HierarchicalAbstraction, GateSystem, RailSystem
from ..nsc import NSCProcessor, GLLLEncoder, GHLLProcessor
from ..nsc.gml import GMLMemory


class AgentStatus(Enum):
    """Agent lifecycle status states."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    SUSPENDED = "suspended"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class AgentState:
    """Persistent agent state that can be serialized and restored."""
    agent_id: str
    status: AgentStatus
    created_at: datetime
    last_active: datetime
    current_task: Optional[str] = None
    reasoning_level: int = 0
    coherence_score: float = 1.0
    attention_budget: float = 100.0
    learning_state: Dict[str, Any] = field(default_factory=dict)
    tool_registry: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_log: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize agent state to dictionary."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "current_task": self.current_task,
            "reasoning_level": self.reasoning_level,
            "coherence_score": self.coherence_score,
            "attention_budget": self.attention_budget,
            "learning_state": self.learning_state,
            "tool_registry": self.tool_registry,
            "performance_metrics": self.performance_metrics,
            "error_log": self.error_log
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Deserialize agent state from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            status=AgentStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            current_task=data.get("current_task"),
            reasoning_level=data.get("reasoning_level", 0),
            coherence_score=data.get("coherence_score", 1.0),
            attention_budget=data.get("attention_budget", 100.0),
            learning_state=data.get("learning_state", {}),
            tool_registry=data.get("tool_registry", {}),
            performance_metrics=data.get("performance_metrics", {}),
            error_log=data.get("error_log", [])
        )


class ResourceMonitor:
    """Monitors and manages agent resource usage."""
    
    def __init__(self, max_memory_mb: float = 1024, max_cpu_percent: float = 80):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.current_memory_mb = 0.0
        self.current_cpu_percent = 0.0
        self.memory_history: List[float] = []
        self.cpu_history: List[float] = []
        
    def update_usage(self, memory_mb: float, cpu_percent: float) -> None:
        """Update current resource usage."""
        self.current_memory_mb = memory_mb
        self.current_cpu_percent = cpu_percent
        self.memory_history.append(memory_mb)
        self.cpu_history.append(cpu_percent)
        
        # Keep only last 100 measurements
        if len(self.memory_history) > 100:
            self.memory_history.pop(0)
        if len(self.cpu_history) > 100:
            self.cpu_history.pop(0)
    
    def is_resource_available(self, required_memory: float = 0, required_cpu: float = 0) -> bool:
        """Check if required resources are available."""
        return (self.current_memory_mb + required_memory <= self.max_memory_mb and
                self.current_cpu_percent + required_cpu <= self.max_cpu_percent)
    
    def get_average_usage(self) -> Dict[str, float]:
        """Get average resource usage over history."""
        if not self.memory_history:
            return {"memory_mb": 0.0, "cpu_percent": 0.0}
        
        return {
            "memory_mb": sum(self.memory_history) / len(self.memory_history),
            "cpu_percent": sum(self.cpu_history) / len(self.cpu_history)
        }


class HealthChecker:
    """Monitors agent health and performs diagnostics."""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.last_check = datetime.now()
        self.health_score = 1.0
        self.check_history: List[Dict[str, Any]] = []
        
    async def perform_health_check(self, agent: "HAAIAgent") -> Dict[str, Any]:
        """Perform comprehensive health check."""
        current_time = datetime.now()
        
        # Check coherence score
        coherence_health = min(1.0, agent.state.coherence_score)
        
        # Check resource usage
        resource_health = 1.0
        if not agent.resource_monitor.is_resource_available():
            resource_health = 0.5
        
        # Check error rate
        recent_errors = len([e for e in agent.state.error_log 
                           if current_time - datetime.fromisoformat(e.split("|")[1]) < timedelta(hours=1)])
        error_health = max(0.0, 1.0 - (recent_errors / 10.0))
        
        # Check response time
        response_health = 1.0  # Would be calculated from actual response times
        
        # Calculate overall health score
        self.health_score = (coherence_health + resource_health + error_health + response_health) / 4.0
        
        check_result = {
            "timestamp": current_time.isoformat(),
            "health_score": self.health_score,
            "coherence_health": coherence_health,
            "resource_health": resource_health,
            "error_health": error_health,
            "response_health": response_health,
            "recent_errors": recent_errors
        }
        
        self.check_history.append(check_result)
        if len(self.check_history) > 50:
            self.check_history.pop(0)
            
        self.last_check = current_time
        return check_result


class AgentLifecycle:
    """Manages agent lifecycle transitions and operations."""
    
    def __init__(self):
        self.transition_handlers: Dict[AgentStatus, List[Callable]] = {
            status: [] for status in AgentStatus
        }
        
    def add_transition_handler(self, from_status: AgentStatus, to_status: AgentStatus, 
                              handler: Callable) -> None:
        """Add handler for specific status transition."""
        if to_status not in self.transition_handlers:
            self.transition_handlers[to_status] = []
        self.transition_handlers[to_status].append(handler)
    
    async def transition_to(self, agent: "HAAIAgent", new_status: AgentStatus) -> bool:
        """Transition agent to new status."""
        old_status = agent.state.status
        
        if old_status == new_status:
            return True
            
        # Validate transition
        if not self._is_valid_transition(old_status, new_status):
            logging.warning(f"Invalid status transition: {old_status} -> {new_status}")
            return False
        
        # Execute transition handlers
        handlers = self.transition_handlers.get(new_status, [])
        for handler in handlers:
            try:
                await handler(agent, old_status, new_status)
            except Exception as e:
                logging.error(f"Error in transition handler: {e}")
                agent.state.error_log.append(f"Transition error|{datetime.now().isoformat()}|{str(e)}")
        
        agent.state.status = new_status
        agent.state.last_active = datetime.now()
        
        logging.info(f"Agent {agent.state.agent_id} transitioned: {old_status} -> {new_status}")
        return True
    
    def _is_valid_transition(self, from_status: AgentStatus, to_status: AgentStatus) -> bool:
        """Check if status transition is valid."""
        valid_transitions = {
            AgentStatus.INITIALIZING: [AgentStatus.ACTIVE, AgentStatus.ERROR, AgentStatus.TERMINATED],
            AgentStatus.ACTIVE: [AgentStatus.IDLE, AgentStatus.SUSPENDED, AgentStatus.ERROR, AgentStatus.TERMINATING],
            AgentStatus.IDLE: [AgentStatus.ACTIVE, AgentStatus.SUSPENDED, AgentStatus.ERROR, AgentStatus.TERMINATING],
            AgentStatus.SUSPENDED: [AgentStatus.ACTIVE, AgentStatus.ERROR, AgentStatus.TERMINATING],
            AgentStatus.TERMINATING: [AgentStatus.TERMINATED, AgentStatus.ERROR],
            AgentStatus.ERROR: [AgentStatus.ACTIVE, AgentStatus.TERMINATING],
            AgentStatus.TERMINATED: []  # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, [])


class AgentCoordinator:
    """Manages communication and coordination between multiple agents."""
    
    def __init__(self):
        self.registered_agents: Dict[str, "HAAIAgent"] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.coordination_protocols: Dict[str, Callable] = {}
        
    def register_agent(self, agent: "HAAIAgent") -> None:
        """Register an agent for coordination."""
        self.registered_agents[agent.state.agent_id] = agent
        logging.info(f"Agent {agent.state.agent_id} registered for coordination")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from coordination."""
        if agent_id in self.registered_agents:
            del self.registered_agents[agent_id]
            logging.info(f"Agent {agent_id} unregistered from coordination")
    
    async def send_message(self, from_agent_id: str, to_agent_id: str, 
                          message: Dict[str, Any]) -> bool:
        """Send message between agents."""
        if to_agent_id not in self.registered_agents:
            return False
        
        message_envelope = {
            "from": from_agent_id,
            "to": to_agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        
        await self.message_queue.put(message_envelope)
        return True
    
    async def broadcast_message(self, from_agent_id: str, message: Dict[str, Any]) -> None:
        """Broadcast message to all registered agents."""
        for agent_id in self.registered_agents:
            if agent_id != from_agent_id:
                await self.send_message(from_agent_id, agent_id, message)
    
    async def process_messages(self) -> None:
        """Process messages in the coordination queue."""
        while True:
            try:
                envelope = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                to_agent_id = envelope["to"]
                
                if to_agent_id in self.registered_agents:
                    agent = self.registered_agents[to_agent_id]
                    await agent.receive_message(envelope)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"Error processing coordination message: {e}")


class HAAIAgent:
    """Main HAAI Agent that integrates all foundational components."""
    
    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.config = config or {}
        
        # Initialize agent state
        self.state = AgentState(
            agent_id=self.agent_id,
            status=AgentStatus.INITIALIZING,
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Initialize core components
        self.coherence_engine = CoherenceEngine()
        self.hierarchical_abstraction = HierarchicalAbstraction()
        self.gate_system = GateSystem()
        self.rail_system = RailSystem()
        
        # Initialize NSC components
        self.nsc_processor = NSCProcessor()
        self.glll_encoder = GLLLEncoder()
        self.ghll_processor = GHLLProcessor()
        self.gml_memory = GMLMemory()
        
        # Initialize agent infrastructure
        self.lifecycle = AgentLifecycle()
        self.resource_monitor = ResourceMonitor()
        self.health_checker = HealthChecker()
        self.coordinator: Optional[AgentCoordinator] = None
        
        # Task management
        self.current_tasks: Set[str] = set()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # Setup logging
        self.logger = logging.getLogger(f"haai.agent.{self.agent_id}")
        
        # Initialize the agent
        asyncio.create_task(self._initialize())
    
    async def _initialize(self) -> None:
        """Initialize the agent and all its components."""
        try:
            self.logger.info(f"Initializing HAAI Agent {self.agent_id}")
            
            # Initialize core systems
            await self.coherence_engine.initialize()
            await self.hierarchical_abstraction.initialize()
            await self.gate_system.initialize()
            await self.rail_system.initialize()
            
            # Initialize NSC systems
            await self.nsc_processor.initialize()
            await self.glll_encoder.initialize()
            await self.ghll_processor.initialize()
            await self.gml_memory.initialize()
            
            # Setup lifecycle handlers
            self._setup_lifecycle_handlers()
            
            # Transition to active state
            await self.lifecycle.transition_to(self, AgentStatus.ACTIVE)
            
            self.logger.info(f"HAAI Agent {self.agent_id} initialized successfully")
            await self._trigger_event("agent_initialized", {"agent_id": self.agent_id})
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            self.state.error_log.append(f"Initialization error|{datetime.now().isoformat()}|{str(e)}")
            await self.lifecycle.transition_to(self, AgentStatus.ERROR)
    
    def _setup_lifecycle_handlers(self) -> None:
        """Setup lifecycle transition handlers."""
        async def on_active(agent, old_status, new_status):
            self.logger.info("Agent becoming active - starting background tasks")
            asyncio.create_task(self._background_tasks())
        
        async def on_terminating(agent, old_status, new_status):
            self.logger.info("Agent terminating - cleaning up resources")
            await self._cleanup()
        
        self.lifecycle.add_transition_handler(AgentStatus.INITIALIZING, AgentStatus.ACTIVE, on_active)
        self.lifecycle.add_transition_handler(AgentStatus.ACTIVE, AgentStatus.TERMINATING, on_terminating)
    
    async def _background_tasks(self) -> None:
        """Run background tasks for the agent."""
        while self.state.status in [AgentStatus.ACTIVE, AgentStatus.IDLE]:
            try:
                # Process task queue
                if not self.task_queue.empty():
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
                    await self._process_task(task)
                
                # Update resource monitoring
                # In a real implementation, this would get actual system metrics
                self.resource_monitor.update_usage(
                    memory_mb=100.0 + len(self.current_tasks) * 10.0,
                    cpu_percent=10.0 + len(self.current_tasks) * 5.0
                )
                
                # Perform health checks periodically
                if (datetime.now() - self.health_checker.last_check).seconds > self.health_checker.check_interval:
                    await self.health_checker.perform_health_check(self)
                
                await asyncio.sleep(0.1)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in background tasks: {e}")
                self.state.error_log.append(f"Background task error|{datetime.now().isoformat()}|{str(e)}")
                await asyncio.sleep(1.0)
    
    async def _process_task(self, task: Dict[str, Any]) -> None:
        """Process a single task from the queue."""
        task_id = task.get("task_id", str(uuid.uuid4()))
        task_type = task.get("type", "unknown")
        
        self.current_tasks.add(task_id)
        self.state.current_task = task_id
        
        try:
            self.logger.info(f"Processing task {task_id}: {task_type}")
            
            # Task processing would be implemented here
            # This is where the reasoning engine, attention system, etc. would be used
            
            await asyncio.sleep(0.1)  # Simulate task processing
            
        except Exception as e:
            self.logger.error(f"Error processing task {task_id}: {e}")
            self.state.error_log.append(f"Task error|{datetime.now().isoformat()}|{task_id}|{str(e)}")
        finally:
            self.current_tasks.discard(task_id)
            if self.state.current_task == task_id:
                self.state.current_task = None
    
    async def _cleanup(self) -> None:
        """Clean up agent resources."""
        self.logger.info("Cleaning up agent resources")
        
        # Cancel all running tasks
        for task_id in list(self.current_tasks):
            self.current_tasks.discard(task_id)
        
        # Cleanup components
        await self.coherence_engine.cleanup()
        await self.hierarchical_abstraction.cleanup()
        await self.gate_system.cleanup()
        await self.rail_system.cleanup()
        await self.nsc_processor.cleanup()
        await self.glll_encoder.cleanup()
        await self.ghll_processor.cleanup()
        
        # Unregister from coordinator if registered
        if self.coordinator:
            self.coordinator.unregister_agent(self.agent_id)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task and return results."""
        if self.state.status != AgentStatus.ACTIVE:
            raise RuntimeError(f"Agent not active, current status: {self.state.status}")
        
        task_id = str(uuid.uuid4())
        task["task_id"] = task_id
        
        # Add task to queue
        await self.task_queue.put(task)
        
        # Wait for task completion (simplified)
        while task_id in self.current_tasks:
            await asyncio.sleep(0.1)
        
        return {"task_id": task_id, "status": "completed"}
    
    async def receive_message(self, message_envelope: Dict[str, Any]) -> None:
        """Receive a message from another agent."""
        self.logger.info(f"Received message from {message_envelope['from']}")
        await self._trigger_event("message_received", message_envelope)
    
    def add_event_callback(self, event_type: str, callback: Callable) -> None:
        """Add callback for specific event type."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    async def _trigger_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Trigger event callbacks."""
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event callback: {e}")
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get current agent state snapshot."""
        return {
            "agent_state": self.state.to_dict(),
            "resource_usage": self.resource_monitor.get_average_usage(),
            "health": {
                "score": self.health_checker.health_score,
                "last_check": self.health_checker.last_check.isoformat()
            },
            "active_tasks": list(self.current_tasks),
            "queue_size": self.task_queue.qsize()
        }
    
    async def save_state(self, filepath: str) -> None:
        """Save agent state to file."""
        state_data = self.get_state_snapshot()
        with open(filepath, 'w') as f:
            json.dump(state_data, f, indent=2)
        self.logger.info(f"Agent state saved to {filepath}")
    
    async def load_state(self, filepath: str) -> None:
        """Load agent state from file."""
        with open(filepath, 'r') as f:
            state_data = json.load(f)
        
        self.state = AgentState.from_dict(state_data["agent_state"])
        self.logger.info(f"Agent state loaded from {filepath}")
    
    async def shutdown(self) -> None:
        """Shutdown the agent gracefully."""
        self.logger.info(f"Shutting down HAAI Agent {self.agent_id}")
        await self.lifecycle.transition_to(self, AgentStatus.TERMINATING)
        await self.lifecycle.transition_to(self, AgentStatus.TERMINATED)
        self.logger.info(f"HAAI Agent {self.agent_id} shutdown complete")