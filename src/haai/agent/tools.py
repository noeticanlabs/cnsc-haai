"""
HAAI Tool Integration Framework

Implements tool discovery and registration, execution and result integration,
selection and optimization, usage learning and adaptation, and safety validation.
"""

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable, Union
from datetime import datetime
import json
import hashlib


class ToolType(Enum):
    """Types of tools supported by the framework."""
    FUNCTION = "function"
    API = "api"
    DATABASE = "database"
    FILE = "file"
    COMPUTATION = "computation"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"


class ToolStatus(Enum):
    """Tool execution status."""
    REGISTERED = "registered"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class ToolPriority(Enum):
    """Tool execution priority."""
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class ToolCapability:
    """Describes the capabilities of a tool."""
    input_types: List[str]
    output_types: List[str]
    operations: List[str]
    domains: List[str]
    complexity_score: float
    reliability_score: float
    resource_requirements: Dict[str, Any]
    
    def can_handle(self, input_type: str, operation: str, domain: str = "general") -> bool:
        """Check if tool can handle specific input, operation, and domain."""
        return (input_type in self.input_types and 
                operation in self.operations and
                (domain == "general" or domain in self.domains))


@dataclass
class ToolExecution:
    """Represents a tool execution request and result."""
    execution_id: str
    tool_id: str
    input_data: Dict[str, Any]
    parameters: Dict[str, Any]
    timestamp: datetime
    status: ToolStatus = ToolStatus.REGISTERED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution to dictionary."""
        return {
            "execution_id": self.execution_id,
            "tool_id": self.tool_id,
            "input_data": self.input_data,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "resource_usage": self.resource_usage,
            "metadata": self.metadata
        }


@dataclass
class ToolDefinition:
    """Definition of a tool in the registry."""
    tool_id: str
    name: str
    description: str
    tool_type: ToolType
    capability: ToolCapability
    function: Callable
    priority: ToolPriority = ToolPriority.MEDIUM
    max_concurrent_executions: int = 1
    timeout: float = 30.0
    safety_requirements: Dict[str, Any] = field(default_factory=dict)
    usage_statistics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.usage_statistics:
            self.usage_statistics = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_used": None
            }


class ToolValidator:
    """Validates tools for safety and correctness."""
    
    def __init__(self):
        self.validation_rules: Dict[str, Callable] = {
            "input_validation": self._validate_inputs,
            "output_validation": self._validate_outputs,
            "resource_validation": self._validate_resources,
            "security_validation": self._validate_security,
            "coherence_validation": self._validate_coherence
        }
        
    async def validate_tool_execution(self, tool_def: ToolDefinition, 
                                   execution: ToolExecution) -> Dict[str, Any]:
        """Validate tool execution before and after execution."""
        validation_results = {}
        
        # Pre-execution validation
        pre_validation = await self._pre_execution_validation(tool_def, execution)
        validation_results["pre_execution"] = pre_validation
        
        if not pre_validation["valid"]:
            execution.status = ToolStatus.ERROR
            execution.error = f"Pre-execution validation failed: {pre_validation['errors']}"
            return validation_results
        
        # Execute validation
        validation_results["execution"] = {"valid": True, "message": "Execution validated"}
        
        # Post-execution validation (will be called after actual execution)
        validation_results["post_execution"] = {"pending": True}
        
        return validation_results
    
    async def _pre_execution_validation(self, tool_def: ToolDefinition, 
                                      execution: ToolExecution) -> Dict[str, Any]:
        """Perform pre-execution validation."""
        errors = []
        warnings = []
        
        # Input validation
        input_result = self._validate_inputs(tool_def, execution.input_data)
        if not input_result["valid"]:
            errors.extend(input_result["errors"])
        
        # Resource validation
        resource_result = self._validate_resources(tool_def, execution.parameters)
        if not resource_result["valid"]:
            errors.extend(resource_result["errors"])
        
        # Security validation
        security_result = self._validate_security(tool_def, execution)
        if not security_result["valid"]:
            errors.extend(security_result["errors"])
        
        # Coherence validation
        coherence_result = self._validate_coherence(tool_def, execution)
        if not coherence_result["valid"]:
            warnings.extend(coherence_result["warnings"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_inputs(self, tool_def: ToolDefinition, 
                        input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against tool requirements."""
        errors = []
        
        # Check required input types
        if not tool_def.capability.input_types:
            errors.append("Tool has no defined input types")
            return {"valid": False, "errors": errors}
        
        # Simplified validation - in practice would be more sophisticated
        input_type = input_data.get("type", "unknown")
        if input_type not in tool_def.capability.input_types:
            errors.append(f"Input type '{input_type}' not supported by tool")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_outputs(self, tool_def: ToolDefinition, 
                         output_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate output data against tool capabilities."""
        errors = []
        
        # Check output types
        output_type = output_data.get("type", "unknown")
        if output_type not in tool_def.capability.output_types:
            errors.append(f"Output type '{output_type}' not expected from tool")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_resources(self, tool_def: ToolDefinition, 
                          parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate resource requirements."""
        errors = []
        
        # Check memory requirements
        required_memory = parameters.get("memory_mb", 0)
        max_memory = tool_def.capability.resource_requirements.get("max_memory_mb", 1024)
        
        if required_memory > max_memory:
            errors.append(f"Required memory ({required_memory}MB) exceeds tool limit ({max_memory}MB)")
        
        # Check timeout
        timeout = parameters.get("timeout", tool_def.timeout)
        if timeout > tool_def.timeout * 2:  # Allow some flexibility
            errors.append(f"Requested timeout ({timeout}s) exceeds tool limit ({tool_def.timeout}s)")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_security(self, tool_def: ToolDefinition, 
                         execution: ToolExecution) -> Dict[str, Any]:
        """Validate security requirements."""
        errors = []
        
        # Check for potentially dangerous operations
        dangerous_operations = ["delete", "remove", "format", "execute", "eval"]
        operation = execution.input_data.get("operation", "")
        
        if any(dangerous in operation.lower() for dangerous in dangerous_operations):
            if not execution.parameters.get("confirmed", False):
                errors.append(f"Dangerous operation '{operation}' requires confirmation")
        
        # Check access permissions
        required_permissions = tool_def.safety_requirements.get("permissions", [])
        provided_permissions = execution.parameters.get("permissions", [])
        
        for permission in required_permissions:
            if permission not in provided_permissions:
                errors.append(f"Missing required permission: {permission}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _validate_coherence(self, tool_def: ToolDefinition, 
                          execution: ToolExecution) -> Dict[str, Any]:
        """Validate coherence requirements."""
        warnings = []
        
        # Check if tool operation aligns with coherence requirements
        coherence_threshold = tool_def.safety_requirements.get("coherence_threshold", 0.7)
        current_coherence = execution.input_data.get("coherence_score", 1.0)
        
        if current_coherence < coherence_threshold:
            warnings.append(f"Input coherence ({current_coherence}) below threshold ({coherence_threshold})")
        
        return {
            "valid": True,
            "warnings": warnings
        }


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.tool_categories: Dict[str, List[str]] = defaultdict(list)
        self.tool_dependencies: Dict[str, List[str]] = defaultdict(list)
        self.validator = ToolValidator()
        
    def register_tool(self, tool_id: str, name: str, description: str,
                     tool_type: ToolType, capability: ToolCapability,
                     function: Callable, **kwargs) -> bool:
        """Register a new tool."""
        try:
            # Validate function signature
            sig = inspect.signature(function)
            if not self._validate_function_signature(sig):
                return False
            
            tool_def = ToolDefinition(
                tool_id=tool_id,
                name=name,
                description=description,
                tool_type=tool_type,
                capability=capability,
                function=function,
                **kwargs
            )
            
            self.tools[tool_id] = tool_def
            
            # Categorize tool
            for domain in capability.domains:
                self.tool_categories[domain].append(tool_id)
            
            logging.info(f"Tool registered: {tool_id} ({name})")
            return True
            
        except Exception as e:
            logging.error(f"Failed to register tool {tool_id}: {e}")
            return False
    
    def _validate_function_signature(self, signature: inspect.Signature) -> bool:
        """Validate that function has appropriate signature."""
        # Check for required parameters
        required_params = ["input_data", "parameters"]
        param_names = list(signature.parameters.keys())
        
        return all(param in param_names for param in required_params)
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool."""
        if tool_id in self.tools:
            tool_def = self.tools[tool_id]
            
            # Remove from categories
            for domain in tool_def.capability.domains:
                if tool_id in self.tool_categories[domain]:
                    self.tool_categories[domain].remove(tool_id)
            
            # Remove from registry
            del self.tools[tool_id]
            
            logging.info(f"Tool unregistered: {tool_id}")
            return True
        
        return False
    
    def find_tools(self, input_type: str = None, operation: str = None,
                  domain: str = None, tool_type: ToolType = None) -> List[str]:
        """Find tools matching specific criteria."""
        matching_tools = []
        
        for tool_id, tool_def in self.tools.items():
            # Check input type
            if input_type and input_type not in tool_def.capability.input_types:
                continue
            
            # Check operation
            if operation and operation not in tool_def.capability.operations:
                continue
            
            # Check domain
            if domain and domain not in tool_def.capability.domains:
                continue
            
            # Check tool type
            if tool_type and tool_def.tool_type != tool_type:
                continue
            
            matching_tools.append(tool_id)
        
        return matching_tools
    
    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get tool definition by ID."""
        return self.tools.get(tool_id)
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """Get statistics about registered tools."""
        stats = {
            "total_tools": len(self.tools),
            "tools_by_type": defaultdict(int),
            "tools_by_domain": defaultdict(int),
            "most_used_tools": [],
            "reliability_scores": {}
        }
        
        for tool_def in self.tools.values():
            stats["tools_by_type"][tool_def.tool_type.value] += 1
            for domain in tool_def.capability.domains:
                stats["tools_by_domain"][domain] += 1
            
            # Calculate reliability
            total_exec = tool_def.usage_statistics["total_executions"]
            successful_exec = tool_def.usage_statistics["successful_executions"]
            reliability = successful_exec / total_exec if total_exec > 0 else 0.0
            stats["reliability_scores"][tool_def.tool_id] = reliability
        
        # Most used tools
        tools_by_usage = sorted(
            self.tools.items(),
            key=lambda x: x[1].usage_statistics["total_executions"],
            reverse=True
        )
        stats["most_used_tools"] = [
            {"tool_id": tool_id, "usage_count": tool_def.usage_statistics["total_executions"]}
            for tool_id, tool_def in tools_by_usage[:10]
        ]
        
        return dict(stats)


class ToolSelector:
    """Selects optimal tools for specific tasks."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.selection_history: List[Dict[str, Any]] = []
        self.selection_weights: Dict[str, float] = {}
        
    def select_tool(self, input_data: Dict[str, Any], operation: str,
                   domain: str = "general", constraints: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Select the best tool for the given task."""
        constraints = constraints or {}
        
        # Find candidate tools
        candidate_tools = self.registry.find_tools(
            input_type=input_data.get("type"),
            operation=operation,
            domain=domain
        )
        
        if not candidate_tools:
            return None
        
        # Score each candidate
        tool_scores = {}
        for tool_id in candidate_tools:
            score = self._calculate_tool_score(tool_id, input_data, operation, constraints)
            tool_scores[tool_id] = score
        
        # Select best tool
        best_tool_id = max(tool_scores.keys(), key=lambda t: tool_scores[t])
        
        # Record selection
        self.selection_history.append({
            "timestamp": datetime.now().isoformat(),
            "selected_tool": best_tool_id,
            "candidates": candidate_tools,
            "scores": tool_scores,
            "input_type": input_data.get("type"),
            "operation": operation,
            "domain": domain
        })
        
        # Keep history manageable
        if len(self.selection_history) > 1000:
            self.selection_history.pop(0)
        
        return best_tool_id
    
    def _calculate_tool_score(self, tool_id: str, input_data: Dict[str, Any],
                            operation: str, constraints: Dict[str, Any]) -> float:
        """Calculate score for a tool based on multiple factors."""
        tool_def = self.registry.get_tool(tool_id)
        if not tool_def:
            return 0.0
        
        score = 0.0
        
        # Base score from capability match
        if tool_def.capability.can_handle(
            input_data.get("type", "unknown"),
            operation,
            constraints.get("domain", "general")
        ):
            score += 0.3
        
        # Reliability score
        total_exec = tool_def.usage_statistics["total_executions"]
        if total_exec > 0:
            reliability = tool_def.usage_statistics["successful_executions"] / total_exec
            score += reliability * 0.3
        
        # Performance score (inverse of average execution time)
        avg_time = tool_def.usage_statistics["average_execution_time"]
        if avg_time > 0:
            performance_score = min(1.0, 1.0 / (avg_time + 1.0))
            score += performance_score * 0.2
        
        # Complexity score (prefer appropriate complexity)
        task_complexity = constraints.get("complexity", 0.5)
        tool_complexity = tool_def.capability.complexity_score
        complexity_match = 1.0 - abs(task_complexity - tool_complexity)
        score += complexity_match * 0.1
        
        # Priority score
        score += tool_def.priority.value / 3.0 * 0.1
        
        return score
    
    def get_selection_insights(self) -> Dict[str, Any]:
        """Get insights about tool selection patterns."""
        if not self.selection_history:
            return {"message": "No selection history available"}
        
        # Analyze selection patterns
        tool_selections = defaultdict(int)
        operation_patterns = defaultdict(lambda: defaultdict(int))
        
        for selection in self.selection_history:
            tool_id = selection["selected_tool"]
            operation = selection["operation"]
            
            tool_selections[tool_id] += 1
            operation_patterns[operation][tool_id] += 1
        
        return {
            "total_selections": len(self.selection_history),
            "most_selected_tools": sorted(tool_selections.items(), key=lambda x: x[1], reverse=True)[:10],
            "operation_preferences": dict(operation_patterns),
            "selection_diversity": len(tool_selections) / len(self.registry.tools) if self.registry.tools else 0
        }


class ToolExecutor:
    """Executes tools and manages their lifecycle."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.active_executions: Dict[str, ToolExecution] = {}
        self.execution_history: List[ToolExecution] = []
        self.validator = ToolValidator()
        self.max_concurrent_executions = 10
        
    async def execute_tool(self, tool_id: str, input_data: Dict[str, Any],
                         parameters: Optional[Dict[str, Any]] = None) -> ToolExecution:
        """Execute a tool with given input and parameters."""
        parameters = parameters or {}
        
        # Get tool definition
        tool_def = self.registry.get_tool(tool_id)
        if not tool_def:
            raise ValueError(f"Tool not found: {tool_id}")
        
        # Check concurrent execution limit
        active_count = sum(1 for exec in self.active_executions.values() 
                          if exec.tool_id == tool_id and exec.status == ToolStatus.BUSY)
        if active_count >= tool_def.max_concurrent_executions:
            raise RuntimeError(f"Tool {tool_id} has reached maximum concurrent executions")
        
        # Create execution record
        execution = ToolExecution(
            execution_id=f"exec_{int(time.time() * 1000000)}",
            tool_id=tool_id,
            input_data=input_data,
            parameters=parameters,
            timestamp=datetime.now(),
            status=ToolStatus.REGISTERED
        )
        
        # Validate execution
        validation_results = await self.validator.validate_tool_execution(tool_def, execution)
        if not validation_results["pre_execution"]["valid"]:
            execution.status = ToolStatus.ERROR
            execution.error = f"Validation failed: {validation_results['pre_execution']['errors']}"
            return execution
        
        # Start execution
        self.active_executions[execution.execution_id] = execution
        execution.status = ToolStatus.BUSY
        
        try:
            # Execute tool function
            start_time = time.time()
            
            result = await self._execute_tool_function(tool_def, input_data, parameters)
            
            execution_time = time.time() - start_time
            execution.execution_time = execution_time
            execution.result = result
            execution.status = ToolStatus.ACTIVE
            
            # Update tool statistics
            self._update_tool_statistics(tool_def, execution_time, True)
            
        except Exception as e:
            execution.status = ToolStatus.ERROR
            execution.error = str(e)
            execution.execution_time = time.time() - start_time
            
            # Update tool statistics
            self._update_tool_statistics(tool_def, execution.execution_time, False)
            
            logging.error(f"Tool execution failed: {tool_id} - {e}")
        
        # Move to history
        self.execution_history.append(execution)
        del self.active_executions[execution.execution_id]
        
        # Keep history manageable
        if len(self.execution_history) > 1000:
            self.execution_history.pop(0)
        
        return execution
    
    async def _execute_tool_function(self, tool_def: ToolDefinition,
                                   input_data: Dict[str, Any],
                                   parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual tool function."""
        # Check if function is async
        if inspect.iscoroutinefunction(tool_def.function):
            result = await tool_def.function(input_data, parameters)
        else:
            # Run sync function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, tool_def.function, input_data, parameters
            )
        
        return result
    
    def _update_tool_statistics(self, tool_def: ToolDefinition, 
                               execution_time: float, success: bool) -> None:
        """Update tool usage statistics."""
        stats = tool_def.usage_statistics
        stats["total_executions"] += 1
        stats["total_execution_time"] += execution_time
        stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
        stats["last_used"] = datetime.now().isoformat()
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
    
    def get_execution_status(self, execution_id: str) -> Optional[ToolExecution]:
        """Get status of a specific execution."""
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # Check history
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution
        
        return None
    
    def get_active_executions(self) -> List[ToolExecution]:
        """Get all currently active executions."""
        return list(self.active_executions.values())
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self.execution_history:
            return {"message": "No execution history"}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for e in self.execution_history if e.status == ToolStatus.ACTIVE)
        failed_executions = sum(1 for e in self.execution_history if e.status == ToolStatus.ERROR)
        
        execution_times = [e.execution_time for e in self.execution_history if e.execution_time > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        tool_performance = defaultdict(lambda: {"total": 0, "successful": 0, "time": 0})
        for execution in self.execution_history:
            tool_id = execution.tool_id
            tool_performance[tool_id]["total"] += 1
            if execution.status == ToolStatus.ACTIVE:
                tool_performance[tool_id]["successful"] += 1
            tool_performance[tool_id]["time"] += execution.execution_time
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "average_execution_time": avg_execution_time,
            "tool_performance": dict(tool_performance),
            "currently_active": len(self.active_executions)
        }


class ToolLearningSystem:
    """Learns and adapts tool usage patterns."""
    
    def __init__(self, registry: ToolRegistry, selector: ToolSelector, executor: ToolExecutor):
        self.registry = registry
        self.selector = selector
        self.executor = executor
        self.usage_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.performance_models: Dict[str, Dict[str, float]] = {}
        
    def record_execution(self, execution: ToolExecution) -> None:
        """Record tool execution for learning."""
        tool_id = execution.tool_id
        
        # Extract features for learning
        features = {
            "input_type": execution.input_data.get("type", "unknown"),
            "operation": execution.input_data.get("operation", "unknown"),
            "execution_time": execution.execution_time,
            "success": execution.status == ToolStatus.ACTIVE,
            "timestamp": execution.timestamp.isoformat(),
            "parameters": execution.parameters
        }
        
        self.usage_patterns[tool_id].append(features)
        
        # Keep pattern history manageable
        if len(self.usage_patterns[tool_id]) > 100:
            self.usage_patterns[tool_id].pop(0)
        
        # Update performance model
        self._update_performance_model(tool_id, features)
    
    def _update_performance_model(self, tool_id: str, features: Dict[str, Any]) -> None:
        """Update performance model for a tool."""
        if tool_id not in self.performance_models:
            self.performance_models[tool_id] = {
                "avg_execution_time": 0.0,
                "success_rate": 0.0,
                "usage_count": 0,
                "last_updated": datetime.now().isoformat()
            }
        
        model = self.performance_models[tool_id]
        model["usage_count"] += 1
        
        # Update execution time
        current_avg = model["avg_execution_time"]
        new_time = features["execution_time"]
        model["avg_execution_time"] = (current_avg * (model["usage_count"] - 1) + new_time) / model["usage_count"]
        
        # Update success rate
        pattern_history = self.usage_patterns[tool_id]
        successful_count = sum(1 for p in pattern_history if p["success"])
        model["success_rate"] = successful_count / len(pattern_history)
        
        model["last_updated"] = datetime.now().isoformat()
    
    def predict_tool_performance(self, tool_id: str, input_data: Dict[str, Any],
                               parameters: Dict[str, Any]) -> Dict[str, float]:
        """Predict performance of a tool for specific inputs."""
        if tool_id not in self.performance_models:
            return {"predicted_time": 10.0, "predicted_success": 0.5, "confidence": 0.1}
        
        model = self.performance_models[tool_id]
        
        # Simple prediction based on historical performance
        base_time = model["avg_execution_time"]
        base_success = model["success_rate"]
        
        # Adjust based on input characteristics
        input_complexity = len(str(input_data)) / 1000.0  # Simplified complexity
        time_adjustment = 1.0 + input_complexity * 0.1
        
        predicted_time = base_time * time_adjustment
        predicted_success = base_success * (1.0 - input_complexity * 0.05)
        confidence = min(1.0, model["usage_count"] / 50.0)
        
        return {
            "predicted_time": predicted_time,
            "predicted_success": predicted_success,
            "confidence": confidence
        }
    
    def recommend_tool_improvements(self, tool_id: str) -> List[str]:
        """Recommend improvements for a tool based on usage patterns."""
        if tool_id not in self.usage_patterns:
            return ["No usage data available for recommendations"]
        
        recommendations = []
        patterns = self.usage_patterns[tool_id]
        
        # Analyze failure patterns
        failed_patterns = [p for p in patterns if not p["success"]]
        if len(failed_patterns) / len(patterns) > 0.2:  # More than 20% failures
            recommendations.append("High failure rate detected - consider improving error handling")
        
        # Analyze performance patterns
        slow_patterns = [p for p in patterns if p["execution_time"] > 5.0]
        if len(slow_patterns) / len(patterns) > 0.3:  # More than 30% slow executions
            recommendations.append("Many slow executions detected - consider optimization")
        
        # Analyze usage patterns
        input_types = set(p["input_type"] for p in patterns)
        if len(input_types) == 1:
            recommendations.append("Tool used with single input type - consider expanding capabilities")
        
        return recommendations


class ToolFramework:
    """Main tool framework that integrates all components."""
    
    def __init__(self):
        self.logger = logging.getLogger("haai.tool_framework")
        
        # Initialize components
        self.registry = ToolRegistry()
        self.selector = ToolSelector(self.registry)
        self.executor = ToolExecutor(self.registry)
        self.learning_system = ToolLearningSystem(self.registry, self.selector, self.executor)
        
        # Framework state
        self.is_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the tool framework."""
        if self.is_initialized:
            return
        
        # Register built-in tools
        await self._register_builtin_tools()
        
        self.is_initialized = True
        self.logger.info("Tool framework initialized")
    
    async def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        # Example built-in tools
        
        # Data transformation tool
        await self.register_tool(
            tool_id="transform_data",
            name="Data Transformer",
            description="Transforms data between different formats",
            tool_type=ToolType.TRANSFORMATION,
            capability=ToolCapability(
                input_types=["json", "xml", "text"],
                output_types=["json", "xml", "text"],
                operations=["transform", "convert", "format"],
                domains=["general", "data_processing"],
                complexity_score=0.3,
                reliability_score=0.9,
                resource_requirements={"max_memory_mb": 100, "timeout": 10.0}
            ),
            function=self._transform_data_function
        )
        
        # Validation tool
        await self.register_tool(
            tool_id="validate_data",
            name="Data Validator",
            description="Validates data against schemas and rules",
            tool_type=ToolType.VALIDATION,
            capability=ToolCapability(
                input_types=["json", "xml", "text"],
                output_types=["validation_result"],
                operations=["validate", "check", "verify"],
                domains=["general", "data_quality"],
                complexity_score=0.2,
                reliability_score=0.95,
                resource_requirements={"max_memory_mb": 50, "timeout": 5.0}
            ),
            function=self._validate_data_function
        )
    
    async def register_tool(self, tool_id: str, name: str, description: str,
                          tool_type: ToolType, capability: ToolCapability,
                          function: Callable, **kwargs) -> bool:
        """Register a new tool in the framework."""
        success = self.registry.register_tool(
            tool_id, name, description, tool_type, capability, function, **kwargs
        )
        
        if success:
            self.logger.info(f"Tool registered in framework: {tool_id}")
        
        return success
    
    async def execute_task(self, input_data: Dict[str, Any], operation: str,
                          domain: str = "general", constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a task using the optimal tool."""
        constraints = constraints or {}
        
        # Select best tool
        tool_id = self.selector.select_tool(input_data, operation, domain, constraints)
        if not tool_id:
            return {
                "success": False,
                "error": "No suitable tool found for the task",
                "input_data": input_data,
                "operation": operation
            }
        
        # Execute tool
        try:
            execution = await self.executor.execute_tool(tool_id, input_data, constraints)
            
            # Record execution for learning
            self.learning_system.record_execution(execution)
            
            return {
                "success": execution.status == ToolStatus.ACTIVE,
                "tool_id": tool_id,
                "execution_id": execution.execution_id,
                "result": execution.result,
                "execution_time": execution.execution_time,
                "error": execution.error
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_id": tool_id
            }
    
    async def _transform_data_function(self, input_data: Dict[str, Any], 
                                     parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Built-in data transformation function."""
        # Simplified transformation logic
        data = input_data.get("data", {})
        target_format = parameters.get("target_format", "json")
        
        if target_format == "json":
            result = {"transformed_data": data, "format": "json"}
        elif target_format == "text":
            result = {"transformed_data": str(data), "format": "text"}
        else:
            result = {"transformed_data": data, "format": target_format}
        
        return result
    
    async def _validate_data_function(self, input_data: Dict[str, Any], 
                                    parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Built-in data validation function."""
        # Simplified validation logic
        data = input_data.get("data", {})
        schema = parameters.get("schema", {})
        
        is_valid = True
        errors = []
        
        # Basic validation checks
        if schema.get("required_fields"):
            required_fields = schema["required_fields"]
            for field in required_fields:
                if field not in data:
                    is_valid = False
                    errors.append(f"Missing required field: {field}")
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "validated_data": data
        }
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get comprehensive framework status."""
        return {
            "is_initialized": self.is_initialized,
            "registry": self.registry.get_tool_statistics(),
            "selector": self.selector.get_selection_insights(),
            "executor": self.executor.get_execution_statistics(),
            "learning": {
                "tools_tracked": len(self.learning_system.usage_patterns),
                "performance_models": len(self.learning_system.performance_models)
            }
        }
    
    async def shutdown(self) -> None:
        """Shutdown the tool framework."""
        # Wait for active executions to complete
        active_executions = self.executor.get_active_executions()
        if active_executions:
            self.logger.info(f"Waiting for {len(active_executions)} active executions to complete")
            # In a real implementation, would wait for executions to complete
        
        self.is_initialized = False
        self.logger.info("Tool framework shutdown complete")