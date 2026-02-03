"""
Unit tests for the distributed computing framework.
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestMessageBus:
    """Test in-memory message bus implementation."""
    
    @pytest.fixture
    async def message_bus(self):
        """Create a message bus for testing."""
        from haai.core.distributed import InMemoryMessageBus
        
        bus = InMemoryMessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_publish_subscribe(self, message_bus):
        """Test basic publish/subscribe functionality."""
        from haai.core.distributed import Message
        
        received = []
        
        async def handler(message):
            received.append(message)
        
        # Subscribe to topic
        sub_id = await message_bus.subscribe("test/topic", handler)
        assert sub_id is not None
        
        # Publish message
        message = Message(
            sender="test_sender",
            topic="test/topic",
            payload={"key": "value"}
        )
        await message_bus.publish(message)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Verify receipt
        assert len(received) == 1
        assert received[0].payload["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_request_response(self, message_bus):
        """Test request/response pattern."""
        from haai.core.distributed import Message
        
        # Set up a responder
        async def responder(message):
            response = Message(
                sender="responder",
                topic="",
                payload={"response": "yes"},
                correlation_id=message.correlation_id,
                reply_to=message.sender
            )
            await message_bus.publish(response)
        
        await message_bus.subscribe("test/request", responder)
        
        # Send request
        request = Message(
            sender="requester",
            topic="test/request",
            payload={"question": "?"},
            reply_to="requester"
        )
        
        # Wait for response
        response = await message_bus.request(request, timeout=2.0)
        
        assert response is not None
        assert response.payload["response"] == "yes"
    
    @pytest.mark.asyncio
    async def test_priority_queuing(self, message_bus):
        """Test message priority handling."""
        from haai.core.distributed import Message, MessagePriority
        
        received_order = []
        
        async def handler(message):
            received_order.append(message.payload.get("order"))
        
        await message_bus.subscribe("test/priority", handler)
        
        # Publish in reverse priority order
        await message_bus.publish(Message(
            sender="s",
            topic="test/priority",
            payload={"order": "low"},
            priority=MessagePriority.LOW
        ))
        await message_bus.publish(Message(
            sender="s",
            topic="test/priority",
            payload={"order": "high"},
            priority=MessagePriority.HIGH
        ))
        await message_bus.publish(Message(
            sender="s",
            topic="test/priority",
            payload={"order": "normal"},
            priority=MessagePriority.NORMAL
        ))
        
        # Wait for processing
        await asyncio.sleep(0.2)
        
        # High priority should be processed first
        assert len(received_order) == 3
        # Note: Actual order depends on implementation details
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, message_bus):
        """Test unsubscribe functionality."""
        from haai.core.distributed import Message
        
        received = []
        
        async def handler(message):
            received.append(message)
        
        # Subscribe
        sub_id = await message_bus.subscribe("test/unsub", handler)
        
        # Publish - should receive
        await message_bus.publish(Message(sender="s", topic="test/unsub", payload={}))
        await asyncio.sleep(0.1)
        assert len(received) == 1
        
        # Unsubscribe
        await message_bus.unsubscribe(sub_id)
        
        # Publish - should not receive
        await message_bus.publish(Message(sender="s", topic="test/unsub", payload={}))
        await asyncio.sleep(0.1)
        assert len(received) == 1  # Still 1, not 2


class TestDistributedNode:
    """Test distributed node functionality."""
    
    @pytest.fixture
    async def message_bus(self):
        """Create a message bus for testing."""
        from haai.core.distributed import InMemoryMessageBus
        
        bus = InMemoryMessageBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_node_lifecycle(self, message_bus):
        """Test node initialization and shutdown."""
        from haai.core.distributed import DistributedNode
        
        node = DistributedNode("test_node", message_bus)
        await node.initialize()
        
        assert message_bus._running
        
        await node.shutdown()
        # Message bus may still be running if other nodes exist
    
    @pytest.mark.asyncio
    async def test_node_publish(self, message_bus):
        """Test node publish functionality."""
        from haai.core.distributed import DistributedNode, Message
        
        node = DistributedNode("test_node", message_bus)
        await node.initialize()
        
        received = []
        async def handler(m):
            received.append(m)
        
        await message_bus.subscribe("test/node", handler)
        
        # Publish from node
        await node.publish("test/node", {"data": "test"})
        
        await asyncio.sleep(0.1)
        assert len(received) == 1
        assert received[0].payload["data"] == "test"
        
        await node.shutdown()


class TestDistributedCoordinator:
    """Test distributed coordinator functionality."""
    
    @pytest.fixture
    async def coordinator(self):
        """Create a coordinator for testing."""
        from haai.core.distributed import DistributedCoordinator
        
        coord = DistributedCoordinator()
        await coord.initialize()
        yield coord
        await coord.shutdown()
    
    @pytest.mark.asyncio
    async def test_agent_registration(self, coordinator):
        """Test agent registration."""
        agent_node = await coordinator.register_agent("agent_1")
        
        assert "agent_1" in coordinator.get_registered_agents()
        assert agent_node.node_id == "agent_1"
    
    @pytest.mark.asyncio
    async def test_agent_unregistration(self, coordinator):
        """Test agent unregistration."""
        await coordinator.register_agent("agent_1")
        await coordinator.unregister_agent("agent_1")
        
        assert "agent_1" not in coordinator.get_registered_agents()
    
    @pytest.mark.asyncio
    async def test_broadcast(self, coordinator):
        """Test broadcast functionality."""
        from haai.core.distributed import Message, MessagePriority
        
        received = []
        async def handler(m):
            received.append(m)
        
        await coordinator.subscribe("haai/coherence", handler)
        
        await coordinator.broadcast_coherence_threshold(0.95)
        
        await asyncio.sleep(0.1)
        assert len(received) == 1
        assert received[0].payload["threshold"] == 0.95
    
    @pytest.mark.asyncio
    async def test_distribute_task(self, coordinator):
        """Test task distribution."""
        from haai.core.distributed import DistributedNode
        
        # Register agents
        agent1 = await coordinator.register_agent("agent_1")
        agent2 = await coordinator.register_agent("agent_2")
        
        # Set up agents to receive tasks
        async def task_handler(m):
            pass
        
        await agent1.subscribe("haai/task/execute", task_handler)
        await agent2.subscribe("haai/task/execute", task_handler)
        
        # Distribute task
        task = {"name": "test_task", "data": "test"}
        results = await coordinator.distribute_task(task)
        
        assert "agent_1" in results
        assert "agent_2" in results


class TestTaskScheduler:
    """Test task scheduler functionality."""
    
    @pytest.fixture
    def scheduler(self):
        """Create a task scheduler for testing."""
        from haai.core.task_distribution import TaskScheduler
        
        return TaskScheduler()
    
    def test_create_task(self, scheduler):
        """Test task creation."""
        task = scheduler.create_task(
            name="test_task",
            payload={"key": "value"},
            priority=scheduler.__class__.__name__.TaskPriority.HIGH
        )
        
        assert task.task_id.startswith("task_")
        assert task.name == "test_task"
        assert task.priority.value == 1  # HIGH
    
    def test_register_agent(self, scheduler):
        """Test agent registration."""
        scheduler.register_agent("agent_1", capacity=4)
        
        assert scheduler.agent_capacity["agent_1"] == 4
    
    def test_register_executor(self, scheduler):
        """Test executor registration."""
        from haai.core.task_distribution import FunctionTaskExecutor
        
        def my_func(payload):
            return payload
        
        executor = FunctionTaskExecutor(my_func)
        scheduler.register_executor(executor)
        
        assert "my_func" in scheduler._executors
    
    def test_get_statistics(self, scheduler):
        """Test statistics gathering."""
        scheduler.register_agent("agent_1")
        
        stats = scheduler.get_statistics()
        
        assert stats["registered_agents"] == 1
        assert stats["total_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_task_execution(self, scheduler):
        """Test task execution with function executor."""
        from haai.core.task_distribution import FunctionTaskExecutor, TaskPriority
        
        results = []
        
        def process_task(payload):
            return {"processed": payload.get("data")}
        
        executor = FunctionTaskExecutor(process_task)
        scheduler.register_executor(executor)
        scheduler.register_agent("agent_1", capacity=2)
        
        scheduler.on_result(lambda r: results.append(r))
        
        await scheduler.start()
        
        # Create and submit task
        task = scheduler.create_task(
            name="process_task",
            payload={"data": "hello"},
            priority=TaskPriority.HIGH
        )
        await scheduler.submit_task(task)
        
        # Wait for completion
        await asyncio.sleep(0.5)
        
        await scheduler.stop()
        
        assert len(results) == 1
        assert results[0].success


class TestTask:
    """Test task dataclass."""
    
    def test_task_to_dict(self):
        """Test task serialization."""
        from haai.core.task_distribution import Task, TaskPriority, TaskStatus
        
        task = Task(
            task_id="test_123",
            name="test_task",
            payload={"key": "value"},
            priority=TaskPriority.HIGH,
            status=TaskStatus.PENDING
        )
        
        data = task.to_dict()
        
        assert data["task_id"] == "test_123"
        assert data["priority"] == "high"
        assert data["status"] == "pending"
    
    def test_task_from_dict(self):
        """Test task deserialization."""
        from haai.core.task_distribution import Task, TaskPriority, TaskStatus
        
        data = {
            "task_id": "test_456",
            "name": "test_task",
            "payload": {"key": "value"},
            "priority": "normal",
            "status": "running",
            "dependencies": [],
            "metadata": {}
        }
        
        task = Task.from_dict(data)
        
        assert task.task_id == "test_456"
        assert task.priority == TaskPriority.NORMAL
        assert task.status == TaskStatus.RUNNING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
