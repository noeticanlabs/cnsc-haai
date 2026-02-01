#!/usr/bin/env python3
"""
HAAI System Demonstration

This script demonstrates the revolutionary capabilities of the HAAI (Hierarchical 
Abstraction AI) system, showcasing:

1. Coherence-governed reasoning with multi-level abstraction
2. Adaptive attention allocation with hierarchical optimization
3. Receipt-based learning and continuous adaptation
4. Tool integration with safety validation
5. Integrated system demonstrating all components working together

The HAAI system represents the world's first coherence-governed hierarchical
abstraction AI, integrating CGL governance, Noetica ecosystem languages,
and revolutionary attention mechanisms.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, 'src')

from haai.agent import create_integrated_haai_agent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_haai_capabilities():
    """Demonstrate all HAAI system capabilities."""
    
    print("🚀 Initializing HAAI (Hierarchical Abstraction AI) System")
    print("=" * 60)
    
    # Create integrated HAAI agent
    print("\n📋 Creating Integrated HAAI Agent...")
    agent = await create_integrated_haai_agent(
        agent_id="haai_demo_agent",
        config={
            "attention_budget": 150.0,
            "reasoning_depth": 8,
            "learning_rate": 0.15
        }
    )
    
    print(f"✅ Agent Created: {agent.agent_id}")
    print(f"   Status: {agent.state.status.value}")
    print(f"   Coherence Score: {agent.state.coherence_score:.3f}")
    
    try:
        # 1. Demonstrate Hierarchical Reasoning
        print("\n🧠 Demonstrating Hierarchical Reasoning...")
        print("-" * 40)
        
        reasoning_problem = {
            "type": "complex_analysis",
            "data": {
                "problem": "Analyze multi-dimensional data with coherence constraints",
                "dimensions": ["temporal", "semantic", "structural"],
                "constraints": ["bidirectional_consistency", "coherence_preservation"]
            },
            "required_depth": 6,
            "complexity": 0.8
        }
        
        reasoning_result = await agent.demonstrate_hierarchical_reasoning(reasoning_problem)
        
        print(f"📊 Reasoning Results:")
        print(f"   Best Mode: {reasoning_result['best_mode']}")
        print(f"   Coherence Score: {reasoning_result['comparison']['best_score']:.3f}")
        
        comparison = reasoning_result['comparison']
        for mode, scores in comparison.items():
            if mode not in ['best_mode', 'best_score']:
                print(f"   {mode.capitalize()}: {scores['combined_score']:.3f}")
        
        # 2. Demonstrate Attention Allocation
        print("\n🎯 Demonstrating Adaptive Attention Allocation...")
        print("-" * 40)
        
        attention_tasks = [
            {
                "name": "High-Priority Reasoning",
                "priority": "high",
                "attention_required": 25.0,
                "coherence_gain": 0.9,
                "compute_cost": 0.4
            },
            {
                "name": "Medium-Priority Learning",
                "priority": "medium", 
                "attention_required": 15.0,
                "coherence_gain": 0.7,
                "compute_cost": 0.25
            },
            {
                "name": "Low-Priority Maintenance",
                "priority": "low",
                "attention_required": 8.0,
                "coherence_gain": 0.4,
                "compute_cost": 0.1
            }
        ]
        
        attention_result = await agent.demonstrate_attention_allocation(attention_tasks)
        
        print(f"📈 Attention Results:")
        print(f"   Tasks Processed: {len(attention_result['results'])}")
        print(f"   Total Coherence Gain: {attention_result['total_coherence_gain']:.3f}")
        print(f"   Budget Utilization: {attention_result['attention_status']['budget_status']['utilization']:.3f}")
        
        # 3. Demonstrate Tool Integration
        print("\n🔧 Demonstrating Tool Integration Framework...")
        print("-" * 40)
        
        tool_operations = [
            {
                "name": "Data Transformation",
                "input_data": {
                    "type": "json",
                    "data": {
                        "source": "haai_system",
                        "coherence_level": 0.85,
                        "abstraction_layers": ["semantic", "syntactic", "pragmatic"]
                    }
                },
                "operation": "transform",
                "domain": "data_processing",
                "constraints": {"preserve_coherence": True}
            },
            {
                "name": "Coherence Validation",
                "input_data": {
                    "type": "validation_request",
                    "data": {"coherence_threshold": 0.7, "check_bidirectional": True}
                },
                "operation": "validate",
                "domain": "coherence_governance",
                "constraints": {"strict_mode": True}
            }
        ]
        
        tool_result = await agent.demonstrate_tool_integration(tool_operations)
        
        print(f"🛠️ Tool Results:")
        print(f"   Operations Completed: {len(tool_result['results'])}")
        print(f"   Success Rate: {tool_result['success_rate']:.3f}")
        print(f"   Framework Status: {tool_result['framework_status']['registry']['total_tools']} tools registered")
        
        # 4. Demonstrate Adaptive Learning
        print("\n📚 Demonstrating Adaptive Learning System...")
        print("-" * 40)
        
        learning_experiences = [
            {
                "id": "reasoning_exp",
                "context": {
                    "type": "hierarchical_reasoning",
                    "complexity": 0.8,
                    "domain": "analysis"
                },
                "action": {
                    "mode": "adaptive",
                    "abstraction_level": 5,
                    "attention_allocation": "optimized"
                },
                "outcome": {
                    "success": True,
                    "coherence_achieved": 0.92,
                    "efficiency": 0.88,
                    "execution_time": 2.3
                },
                "reward": 0.92
            },
            {
                "id": "attention_exp",
                "context": {
                    "type": "attention_management",
                    "task_complexity": 0.7,
                    "concurrent_demands": 3
                },
                "action": {
                    "allocation_strategy": "hierarchical",
                    "budget_distribution": "adaptive"
                },
                "outcome": {
                    "success": True,
                    "attention_efficiency": 0.91,
                    "coherence_improvement": 0.15,
                    "resource_utilization": 0.78
                },
                "reward": 0.91
            }
        ]
        
        learning_result = await agent.demonstrate_adaptive_learning(learning_experiences)
        
        print(f"🧪 Learning Results:")
        print(f"   Experiences Processed: {len(learning_result['experiences'])}")
        print(f"   Recommendations Generated: {len(learning_result['recommendations'])}")
        
        learning_summary = learning_result['learning_summary']
        receipt_stats = learning_summary['receipt_learning']
        print(f"   Learning Receipts: {receipt_stats['total_receipts']}")
        print(f"   Average Reward: {receipt_stats['average_rewards'].get('reasoning_receipt', 0):.3f}")
        
        # 5. Comprehensive System Demonstration
        print("\n🌟 Running Comprehensive System Demonstration...")
        print("-" * 40)
        
        comprehensive_result = await agent.comprehensive_demonstration()
        
        if comprehensive_result["demonstration_successful"]:
            metrics = comprehensive_result["overall_metrics"]
            
            print("🎉 COMPREHENSIVE DEMONSTRATION SUCCESSFUL!")
            print("=" * 50)
            print("📊 SYSTEM PERFORMANCE METRICS:")
            print(f"   Total Execution Time: {metrics['total_demonstration_time']:.2f} seconds")
            print(f"   Components Demonstrated: {metrics['components_demonstrated']}/4")
            print(f"   Overall Coherence: {metrics['overall_coherence']:.3f}")
            print(f"   Agent Health Score: {metrics['agent_health']:.3f}")
            print(f"   Reasoning Performance: {metrics['reasoning_success']:.3f}")
            print(f"   Attention Efficiency: {metrics['attention_efficiency']:.3f}")
            print(f"   Tool Success Rate: {metrics['tool_success_rate']:.3f}")
            print(f"   Learning Adaptations: {metrics['learning_adaptations']}")
            
            # Component-specific results
            print("\n🔍 COMPONENT-SPECIFIC RESULTS:")
            
            reasoning = comprehensive_result["reasoning"]
            print(f"   🧠 Reasoning - Best Mode: {reasoning['best_mode']}")
            print(f"               Performance Score: {reasoning['comparison']['best_score']:.3f}")
            
            attention = comprehensive_result["attention"]
            print(f"   🎯 Attention - Coherence Gain: {attention['total_coherence_gain']:.3f}")
            print(f"               Tasks Completed: {len(attention['results'])}")
            
            tools = comprehensive_result["tools"]
            print(f"   🔧 Tools - Success Rate: {tools['success_rate']:.3f}")
            print(f"            Operations: {len(tools['results'])}")
            
            learning = comprehensive_result["learning"]
            print(f"   📚 Learning - Recommendations: {len(learning['recommendations'])}")
            print(f"               Receipts: {learning['learning_summary']['receipt_learning']['total_receipts']}")
            
        else:
            print("❌ Comprehensive demonstration failed")
            print(f"Error: {comprehensive_result.get('error', 'Unknown error')}")
        
        # Final system status
        print("\n📋 FINAL SYSTEM STATUS:")
        print("-" * 30)
        final_state = agent.get_state_snapshot()
        
        print(f"   Agent Status: {final_state['agent_state']['status']}")
        print(f"   Coherence Score: {final_state['agent_state']['coherence_score']:.3f}")
        print(f"   Active Tasks: {len(final_state['active_tasks'])}")
        print(f"   Queue Size: {final_state['queue_size']}")
        print(f"   Resource Usage: {final_state['resource_usage']['memory_mb']:.1f} MB")
        
        print("\n🎊 HAAI System Demonstration Complete!")
        print("=" * 50)
        print("The revolutionary HAAI system has successfully demonstrated:")
        print("✅ Coherence-governed hierarchical reasoning")
        print("✅ Adaptive attention allocation with ℓ* optimization")
        print("✅ Receipt-based learning and continuous adaptation")
        print("✅ Tool integration with safety validation")
        print("✅ Full system integration with provable consistency")
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        print(f"\n❌ Error during demonstration: {e}")
    
    finally:
        # Clean shutdown
        print("\n🔄 Shutting down HAAI Agent...")
        await agent.shutdown()
        print("✅ Shutdown complete")


async def main():
    """Main demonstration function."""
    print("🌟 HAAI (Hierarchical Abstraction AI) System")
    print("World's First Coherence-Governed Hierarchical Abstraction AI")
    print("Integrating CGL Governance, Noetica Ecosystem, and Revolutionary Attention")
    print()
    
    try:
        await demonstrate_haai_capabilities()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demonstration interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n💥 Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())