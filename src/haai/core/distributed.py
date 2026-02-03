"""
Distributed computing framework for HAAI.
Provides message passing, task distribution, and coordination.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json
import logging
import uuid
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class Message:
    """Distributed message."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: MessagePriority = MessagePriority.NORMAL
    sender: str = ""
    recipient: str = ""
    topic: str = ""
    payload: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    
    def to_bytes(self) -> bytes:
        return json.dumps({
            'message_id': self.message_id,
            'priority': self.priority.value,
            'sender': self.sender,
            'recipient': self.recipient,
            'topic': self.topic,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'reply_to': self.reply_to
        }).encode()
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        parsed = json.loads(data.decode())
        return cls(
            message_id=parsed['message_id'],
            priority=MessagePriority(parsed['priority']),
            sender=parsed['sender'],
            recipient=parsed['recipient'],
            topic=parsed['topic'],
            payload=parsed['payload'],
            timestamp=datetime.fromisoformat(parsed['timestamp']),
            correlation_id=parsed.get('correlation_id'),
            reply_to=parsed.get('reply_to')
        )


class MessageBus(ABC):
    """Abstract message bus for distributed communication."""
    
    @abstractmethod
    async def publish(self, message: Message) -> None:
        """Publish a message to the bus."""
        pass
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic and return subscription ID."""
        pass
    
    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe from a topic."""
        pass
    
    @abstractmethod
    async def request(self, message: Message, timeout: float = 5.0) -> Message:
        """Send a request and wait for response."""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the message bus."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the message bus."""
        pass


class InMemoryMessageBus(MessageBus):
    """In-memory message bus for single-node deployment."""
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Callable]] = {}
        self._queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in MessagePriority
        }
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._response_futures: Dict[str, asyncio.Future] = {}
        self._lock = threading.Lock()
        self._subscription_ids: Dict[str, str] = {}  # handler -> sub_id
        self._counter = 0
    
    async def start(self) -> None:
        """Start the message bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("InMemoryMessageBus started")
    
    async def stop(self) -> None:
        """Stop the message bus."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("InMemoryMessageBus stopped")
    
    async def _worker(self) -> None:
        """Process messages from queues."""
        while self._running:
            try:
                # Process in priority order
                for priority in MessagePriority:
                    queue = self._queues[priority]
                    try:
                        message = await asyncio.wait_for(
                            queue.get(), timeout=0.1
                        )
                        await self._dispatch(message)
                    except asyncio.TimeoutError:
                        continue
            except Exception as e:
                logger.error(f"Message bus worker error: {e}")
    
    async def _dispatch(self, message: Message) -> None:
        """Dispatch message to handlers."""
        handlers = self._subscriptions.get(message.topic, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Handler error for topic {message.topic}: {e}")
        
        # Handle reply-to
        if message.reply_to and message.correlation_id:
            future = self._response_futures.pop(message.correlation_id, None)
            if future and not future.done():
                future.set_result(message)
    
    async def publish(self, message: Message) -> None:
        """Publish a message to the appropriate queue."""
        await self._queues[message.priority].put(message)
    
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic."""
        with self._lock:
            self._counter += 1
            sub_id = f"sub_{self._counter}"
            
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            self._subscriptions[topic].append(handler)
            self._subscription_ids[id(handler)] = sub_id
            logger.info(f"Subscribed to topic: {topic}")
            return sub_id
    
    async def unsubscribe(self, subscription_id: str) -> None:
        """Unsubscribe by subscription ID."""
        # Remove from subscriptions
        for topic, handlers in self._subscriptions.items():
            for handler in handlers:
                if self._subscription_ids.get(id(handler)) == subscription_id:
                    handlers.remove(handler)
                    del self._subscription_ids[id(handler)]
                    logger.info(f"Unsubscribed: {subscription_id}")
                    return
    
    async def request(self, message: Message, timeout: float = 5.0) -> Message:
        """Send a request and wait for response."""
        if not message.correlation_id:
            message.correlation_id = str(uuid.uuid4())
        
        future = asyncio.Future()
        self._response_futures[message.correlation_id] = future
        
        await self.publish(message)
        
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._response_futures.pop(message.correlation_id, None)
            raise TimeoutError(f"Request timed out after {timeout}s")
    
    def get_subscribers(self, topic: str) -> List[Callable]:
        """Get all handlers for a topic (for testing)."""
        return self._subscriptions.get(topic, [])
    
    def get_queue_size(self, priority: MessagePriority) -> int:
        """Get the size of a priority queue."""
        return self._queues[priority].qsize()


class DistributedNode:
    """Represents a node in the distributed system."""
    
    def __init__(self, node_id: str, message_bus: MessageBus = None):
        self.node_id = node_id
        self.message_bus = message_bus or InMemoryMessageBus()
        self._subscriptions: List[str] = []
    
    async def initialize(self) -> None:
        """Initialize the node."""
        await self.message_bus.start()
        logger.info(f"DistributedNode {self.node_id} initialized")
    
    async def shutdown(self) -> None:
        """Shutdown the node."""
        for sub_id in self._subscriptions:
            await self.message_bus.unsubscribe(sub_id)
        await self.message_bus.stop()
        logger.info(f"DistributedNode {self.node_id} shutdown")
    
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic."""
        sub_id = await self.message_bus.subscribe(topic, handler)
        self._subscriptions.append(sub_id)
        return sub_id
    
    async def publish(self, topic: str, payload: Dict, 
                      priority: MessagePriority = MessagePriority.NORMAL,
                      recipient: str = None) -> None:
        """Publish a message."""
        message = Message(
            sender=self.node_id,
            recipient=recipient or "",
            topic=topic,
            payload=payload,
            priority=priority
        )
        await self.message_bus.publish(message)
    
    async def request(self, recipient: str, topic: str, payload: Dict,
                      timeout: float = 5.0) -> Message:
        """Send a request to a specific recipient."""
        message = Message(
            sender=self.node_id,
            recipient=recipient,
            topic=topic,
            payload=payload,
            reply_to=self.node_id
        )
        return await self.message_bus.request(message, timeout)


class DistributedCoordinator:
    """Coordinates distributed HAAI agents."""
    
    def __init__(self, message_bus: MessageBus = None):
        self.message_bus = message_bus or InMemoryMessageBus()
        self.node_id = f"coordinator-{uuid.uuid4().hex[:8]}"
        self._subscriptions: List[str] = []
        self._agents: Dict[str, DistributedNode] = {}
    
    async def initialize(self) -> None:
        """Initialize the coordinator."""
        await self.message_bus.start()
        
        # Subscribe to system topics
        self._subscriptions.append(
            await self.subscribe("haai/coherence", self._handle_coherence)
        )
        self._subscriptions.append(
            await self.subscribe("haai/agent/status", self._handle_status)
        )
        self._subscriptions.append(
            await self.subscribe("haai/agent/heartbeat", self._handle_heartbeat)
        )
        self._subscriptions.append(
            await self.subscribe("haai/task/result", self._handle_task_result)
        )
        
        logger.info(f"DistributedCoordinator initialized: {self.node_id}")
    
    async def shutdown(self) -> None:
        """Shutdown the coordinator."""
        for sub_id in self._subscriptions:
            await self.message_bus.unsubscribe(sub_id)
        await self.message_bus.stop()
        logger.info("DistributedCoordinator shutdown")
    
    async def subscribe(self, topic: str, handler: Callable) -> str:
        """Subscribe to a topic."""
        return await self.message_bus.subscribe(topic, handler)
    
    async def register_agent(self, agent_id: str) -> DistributedNode:
        """Register a new agent with the coordinator."""
        node = DistributedNode(
            node_id=agent_id,
            message_bus=self.message_bus
        )
        self._agents[agent_id] = node
        
        # Subscribe to agent-specific topic
        await node.subscribe(f"haai/agent/{agent_id}/response", lambda m: None)
        
        logger.info(f"Agent registered: {agent_id}")
        return node
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self._agents:
            await self._agents[agent_id].shutdown()
            del self._agents[agent_id]
            logger.info(f"Agent unregistered: {agent_id}")
    
    async def broadcast_coherence_threshold(
        self, threshold: float
    ) -> None:
        """Broadcast coherence threshold to all agents."""
        message = Message(
            sender=self.node_id,
            topic="haai/coherence/threshold",
            payload={'threshold': threshold}
        )
        await self.message_bus.publish(message)
    
    async def broadcast_shutdown(self) -> None:
        """Broadcast shutdown signal to all agents."""
        message = Message(
            sender=self.node_id,
            topic="haai/system/shutdown",
            payload={}
        )
        await self.message_bus.publish(message)
    
    async def get_agent_status(self, agent_id: str, timeout: float = 5.0) -> Dict:
        """Request status from a specific agent."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not found: {agent_id}")
        
        node = self._agents[agent_id]
        response = await self.request(
            agent_id,
            "haai/agent/status/request",
            {}
        )
        return response.payload
    
    async def distribute_task(self, task: Dict, agent_ids: List[str] = None) -> Dict:
        """Distribute a task to available agents."""
        target_agents = agent_ids or list(self._agents.keys())
        
        results = {}
        for agent_id in target_agents:
            if agent_id in self._agents:
                node = self._agents[agent_id]
                await node.publish(
                    "haai/task/execute",
                    payload=task,
                    priority=MessagePriority.HIGH
                )
                results[agent_id] = "task_dispatched"
        
        return results
    
    async def _handle_coherence(self, message: Message) -> None:
        """Handle coherence signals from agents."""
        logger.info(f"Received coherence update from {message.sender}")
        # Process coherence data
    
    async def _handle_status(self, message: Message) -> None:
        """Handle agent status updates."""
        logger.info(f"Received status from {message.sender}")
        # Process status update
    
    async def _handle_heartbeat(self, message: Message) -> None:
        """Handle agent heartbeats."""
        agent_id = message.sender
        if agent_id in self._agents:
            # Update last seen timestamp
            pass
    
    async def _handle_task_result(self, message: Message) -> None:
        """Handle task completion results."""
        logger.info(f"Task result from {message.sender}: {message.payload}")
        # Process result
    
    async def request(self, recipient: str, topic: str, payload: Dict,
                      timeout: float = 5.0) -> Message:
        """Send a request to a specific recipient."""
        message = Message(
            sender=self.node_id,
            recipient=recipient,
            topic=topic,
            payload=payload,
            reply_to=self.node_id
        )
        return await self.message_bus.request(message, timeout)
    
    def get_registered_agents(self) -> List[str]:
        """Get list of registered agent IDs."""
        return list(self._agents.keys())
    
    def get_coordinator_id(self) -> str:
        """Get the coordinator's node ID."""
        return self.node_id
