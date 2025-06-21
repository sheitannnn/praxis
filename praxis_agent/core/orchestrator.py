"""
Orchestrator Core - Main decision-making engine
Implements the Generalized Minimax Strategy for optimal task execution
"""

import json
import uuid
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from gateway.llm_gateway import llm_gateway, LLMResponse
from cognitive.memory_core import memory_core, TaskEpisode
from toolkit.actions import action_toolkit, ActionResult
from config.settings import config_manager


class TaskStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Task:
    """Represents a user task to be executed"""
    id: str
    goal: str
    status: TaskStatus
    plan: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    context: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class DecisionPoint:
    """Represents a decision point in the Generalized Minimax Strategy"""
    options: List[Dict[str, Any]]
    risk_assessment: Dict[str, float]
    expected_value: Dict[str, float]
    selected_option: Optional[str] = None
    reasoning: Optional[str] = None


class GeneralizedMinimaxStrategy:
    """Implements the core decision-making strategy"""
    
    def __init__(self):
        self.config = config_manager.load_config()
    
    async def evaluate_options(self, goal: str, available_actions: List[str], 
                             context: Dict[str, Any]) -> DecisionPoint:
        """Evaluate options using Generalized Minimax Strategy"""
        
        # Get relevant historical context
        historical_context = memory_core.get_relevant_context(goal)
        
        # Prepare evaluation prompt
        evaluation_prompt = self._create_evaluation_prompt(
            goal, available_actions, context, historical_context
        )
        
        # Get LLM evaluation
        response = await llm_gateway.generate(
            evaluation_prompt,
            system_prompt="You are an expert decision-making system. Use the Generalized Minimax Strategy to evaluate options: maximize probability of success while minimizing risk of failure.",
            max_tokens=2048
        )
        
        if not response.success:
            # Fallback to simple heuristic
            return self._fallback_evaluation(available_actions)
        
        try:
            # Parse LLM response
            evaluation_data = json.loads(response.content)
            
            return DecisionPoint(
                options=evaluation_data.get("options", []),
                risk_assessment=evaluation_data.get("risk_assessment", {}),
                expected_value=evaluation_data.get("expected_value", {}),
                selected_option=evaluation_data.get("selected_option"),
                reasoning=evaluation_data.get("reasoning")
            )
        except:
            return self._fallback_evaluation(available_actions)
    
    def _create_evaluation_prompt(self, goal: str, actions: List[str], 
                                context: Dict[str, Any], 
                                historical_context: List[Dict[str, Any]]) -> str:
        """Create prompt for option evaluation"""
        
        prompt = f"""
**TASK GOAL:** {goal}

**AVAILABLE ACTIONS:** {', '.join(actions)}

**CURRENT CONTEXT:**
{json.dumps(context, indent=2)}

**HISTORICAL CONTEXT:**
"""
        
        for ctx in historical_context[:3]:  # Limit to top 3 most relevant
            prompt += f"- {ctx['type']}: {ctx['content'][:200]}...\n"
        
        prompt += """

**EVALUATION REQUIREMENTS:**
Using the Generalized Minimax Strategy, evaluate each available action:

1. **MAXIMIZE (Success Probability):** Rate each action's likelihood of advancing toward the goal (0.0-1.0)
2. **MINIMIZE (Risk/Failure):** Rate each action's risk of failure, errors, or inefficiency (0.0-1.0)

**OUTPUT FORMAT (JSON):**
```json
{
    "options": [
        {
            "action": "action_name",
            "success_probability": 0.85,
            "risk_score": 0.2,
            "expected_value": 0.65,
            "reasoning": "Why this action is/isn't optimal"
        }
    ],
    "risk_assessment": {
        "action_name": 0.2
    },
    "expected_value": {
        "action_name": 0.65
    },
    "selected_option": "best_action_name",
    "reasoning": "Overall reasoning for selection"
}
```

**CALCULATE EXPECTED VALUE:** success_probability * (1 - risk_score)
**SELECT:** Action with highest expected value
"""
        
        return prompt
    
    def _fallback_evaluation(self, actions: List[str]) -> DecisionPoint:
        """Simple fallback evaluation when LLM fails"""
        options = []
        risk_assessment = {}
        expected_value = {}
        
        # Simple heuristic: prefer safer actions
        action_priorities = {
            "search_web": 0.8,
            "read_file": 0.9,
            "write_file": 0.7,
            "list_directory": 0.95,
            "fetch_url": 0.75,
            "execute_python": 0.6,
            "execute_command": 0.4
        }
        
        for action in actions:
            priority = action_priorities.get(action, 0.5)
            risk = 1.0 - priority
            
            options.append({
                "action": action,
                "success_probability": priority,
                "risk_score": risk,
                "expected_value": priority * (1 - risk),
                "reasoning": f"Heuristic evaluation for {action}"
            })
            
            risk_assessment[action] = risk
            expected_value[action] = priority * (1 - risk)
        
        # Select best option
        best_action = max(expected_value.keys(), key=lambda k: expected_value[k])
        
        return DecisionPoint(
            options=options,
            risk_assessment=risk_assessment,
            expected_value=expected_value,
            selected_option=best_action,
            reasoning="Fallback heuristic evaluation"
        )


class Orchestrator:
    """Main orchestrator that coordinates all agent components"""
    
    def __init__(self):
        self.config = config_manager.load_config()
        self.strategy = GeneralizedMinimaxStrategy()
        self.active_tasks: Dict[str, Task] = {}
        self.task_queue: List[str] = []
        self.is_running = False
        
    async def start(self):
        """Start the orchestrator"""
        self.is_running = True
        print("🚀 Praxis Agent Orchestrator started")
        
        # Start main execution loop
        await self._main_loop()
    
    async def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        print("🛑 Praxis Agent Orchestrator stopped")
    
    async def execute_goal(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Task:
        """Execute a user goal"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            goal=goal,
            status=TaskStatus.PENDING,
            plan=[],
            actions=[],
            context=context or {},
            start_time=datetime.now()
        )
        
        self.active_tasks[task_id] = task
        self.task_queue.append(task_id)
        
        print(f"📋 New task queued: {goal[:50]}...")
        
        return task
    
    async def _main_loop(self):
        """Main execution loop"""
        while self.is_running:
            try:
                if self.task_queue:
                    task_id = self.task_queue.pop(0)
                    if task_id in self.active_tasks:
                        await self._execute_task(task_id)
                
                # Brief pause to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task_id: str):
        """Execute a specific task"""
        task = self.active_tasks[task_id]
        
        try:
            print(f"🎯 Executing task: {task.goal[:50]}...")
            
            # Planning phase
            task.status = TaskStatus.PLANNING
            memory_core.update_current_context("current_task", task.goal)
            
            plan = await self._create_plan(task)
            task.plan = plan
            
            # Execution phase
            task.status = TaskStatus.EXECUTING
            
            for step_idx, step in enumerate(plan):
                print(f"  🔄 Step {step_idx + 1}: {step['action']}")
                
                result = await self._execute_step(task, step)
                
                task.actions.append({
                    "step": step_idx + 1,
                    "action": step,
                    "result": asdict(result),
                    "timestamp": datetime.now().isoformat()
                })
                
                if not result.success:
                    # Handle failure with adaptive strategy
                    recovery_success = await self._handle_failure(task, step, result)
                    if not recovery_success:
                        task.status = TaskStatus.FAILED
                        task.error = f"Failed at step {step_idx + 1}: {result.error}"
                        break
                
                # Update context with results
                if result.success and result.result:
                    memory_core.update_current_context(f"step_{step_idx}", result.result)
            
            if task.status == TaskStatus.EXECUTING:
                # Task completed successfully
                task.status = TaskStatus.COMPLETED
                task.result = "Task completed successfully"
                print(f"✅ Task completed: {task.goal[:50]}...")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            print(f"❌ Task failed: {e}")
        
        finally:
            task.end_time = datetime.now()
            await self._finalize_task(task)
    
    async def _create_plan(self, task: Task) -> List[Dict[str, Any]]:
        """Create execution plan for task"""
        
        # Get relevant context from memory
        relevant_context = memory_core.get_relevant_context(task.goal)
        
        # Get available actions
        available_actions = action_toolkit.get_available_actions()
        
        # Create planning prompt
        planning_prompt = f"""
**GOAL:** {task.goal}

**AVAILABLE ACTIONS:**
{json.dumps(available_actions, indent=2)}

**RELEVANT CONTEXT:**
{json.dumps([ctx['content'][:100] for ctx in relevant_context[:3]], indent=2)}

**CURRENT CONTEXT:**
{json.dumps(task.context, indent=2)}

Create a step-by-step plan to achieve the goal. Each step should specify:
1. The action to take
2. The parameters needed
3. The expected outcome

**OUTPUT FORMAT (JSON):**
```json
[
    {
        "action": "action_name",
        "parameters": {"param1": "value1"},
        "expected_outcome": "What this step should accomplish",
        "rationale": "Why this step is necessary"
    }
]
```

Plan should be minimal but complete - avoid unnecessary steps.
"""
        
        response = await llm_gateway.generate(
            planning_prompt,
            system_prompt="You are an expert task planner. Create efficient, step-by-step plans that minimize risk while maximizing success probability."
        )
        
        if response.success:
            try:
                plan = json.loads(response.content)
                return plan if isinstance(plan, list) else []
            except:
                pass
        
        # Fallback to simple plan
        return self._create_fallback_plan(task.goal)
    
    def _create_fallback_plan(self, goal: str) -> List[Dict[str, Any]]:
        """Create a simple fallback plan"""
        # Basic heuristic based on goal keywords
        plan = []
        
        if "search" in goal.lower() or "find" in goal.lower():
            plan.append({
                "action": "search_web",
                "parameters": {"query": goal, "num_results": 5},
                "expected_outcome": "Find relevant information",
                "rationale": "Search for information related to the goal"
            })
        
        if "file" in goal.lower() or "read" in goal.lower():
            plan.append({
                "action": "list_directory",
                "parameters": {"path": ".", "recursive": False},
                "expected_outcome": "List current directory contents",
                "rationale": "Explore available files"
            })
        
        if not plan:
            plan.append({
                "action": "get_system_info",
                "parameters": {},
                "expected_outcome": "Get system information",
                "rationale": "Gather basic system information to understand environment"
            })
        
        return plan
    
    async def _execute_step(self, task: Task, step: Dict[str, Any]) -> ActionResult:
        """Execute a single step with Minimax decision making"""
        
        action_name = step["action"]
        parameters = step.get("parameters", {})
        
        # Use strategy to evaluate and potentially modify the step
        decision_point = await self.strategy.evaluate_options(
            task.goal, 
            [action_name],  # Single action for this step
            {**task.context, "current_step": step}
        )
        
        # Execute the action
        result = action_toolkit.execute_action(action_name, **parameters)
        
        # Store decision and result for learning
        memory_core.add_short_term_memory(
            f"Step: {action_name} -> {'Success' if result.success else 'Failed'}",
            metadata={
                "task_id": task.id,
                "action": action_name,
                "decision_reasoning": decision_point.reasoning,
                "success": result.success
            }
        )
        
        return result
    
    async def _handle_failure(self, task: Task, failed_step: Dict[str, Any], 
                            result: ActionResult) -> bool:
        """Handle step failure with adaptive recovery"""
        
        print(f"  ⚠️ Step failed: {failed_step['action']} - {result.error}")
        
        # Try to get alternative approach from LLM
        recovery_prompt = f"""
The following step failed during task execution:

**TASK GOAL:** {task.goal}
**FAILED STEP:** {failed_step['action']}
**PARAMETERS:** {failed_step.get('parameters', {})}
**ERROR:** {result.error}

**AVAILABLE ACTIONS:** {[action['name'] for action in action_toolkit.get_available_actions()]}

Suggest an alternative approach to accomplish the same outcome. 
Consider:
1. Different action that could achieve the same result
2. Modified parameters for the same action
3. Workaround strategy

**OUTPUT FORMAT (JSON):**
```json
{
    "alternative_action": "action_name",
    "parameters": {"param1": "value1"},
    "reasoning": "Why this alternative should work"
}
```
"""
        
        response = await llm_gateway.generate(recovery_prompt)
        
        if response.success:
            try:
                alternative = json.loads(response.content)
                
                print(f"  🔄 Trying alternative: {alternative['alternative_action']}")
                
                # Execute alternative
                alt_result = action_toolkit.execute_action(
                    alternative["alternative_action"],
                    **alternative.get("parameters", {})
                )
                
                if alt_result.success:
                    print(f"  ✅ Alternative succeeded")
                    # Record the successful alternative
                    task.actions.append({
                        "type": "recovery",
                        "original_step": failed_step,
                        "alternative": alternative,
                        "result": asdict(alt_result),
                        "timestamp": datetime.now().isoformat()
                    })
                    return True
                
            except Exception as e:
                print(f"  ❌ Alternative parsing failed: {e}")
        
        # Recovery failed
        return False
    
    async def _finalize_task(self, task: Task):
        """Finalize task and store episode in memory"""
        
        # Calculate duration
        duration = (task.end_time - task.start_time).total_seconds()
        
        # Create task episode for learning
        episode = TaskEpisode(
            id=task.id,
            goal=task.goal,
            plan=task.plan,
            actions=task.actions,
            result=task.result or task.error or "No result",
            success=task.status == TaskStatus.COMPLETED,
            duration_seconds=int(duration),
            timestamp=task.start_time,
            metadata={
                "end_status": task.status.value,
                "action_count": len(task.actions),
                "context": task.context
            }
        )
        
        # Store episode in long-term memory
        memory_core.store_task_episode(episode)
        
        # If successful, extract learnings for long-term memory
        if task.status == TaskStatus.COMPLETED:
            learning_text = f"Successfully completed: {task.goal}. Strategy: {[step['action'] for step in task.plan]}"
            memory_core.add_long_term_memory(
                learning_text,
                importance_score=0.8,
                metadata={
                    "type": "successful_strategy",
                    "task_type": self._classify_task_type(task.goal),
                    "duration": duration
                }
            )
        
        # Clean up current context
        memory_core.clear_current_context()
        
        # Remove from active tasks
        if task.id in self.active_tasks:
            del self.active_tasks[task.id]
        
        print(f"📊 Task finalized - Duration: {duration:.1f}s, Status: {task.status.value}")
    
    def _classify_task_type(self, goal: str) -> str:
        """Classify task type for better learning"""
        goal_lower = goal.lower()
        
        if any(word in goal_lower for word in ["search", "find", "look"]):
            return "information_gathering"
        elif any(word in goal_lower for word in ["write", "create", "generate"]):
            return "content_creation"
        elif any(word in goal_lower for word in ["analyze", "summarize", "process"]):
            return "data_processing"
        elif any(word in goal_lower for word in ["install", "setup", "configure"]):
            return "system_management"
        else:
            return "general"
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": len(self.task_queue),
            "memory_stats": memory_core.get_memory_stats(),
            "llm_usage": llm_gateway.get_usage_stats()
        }


# Global orchestrator instance
orchestrator = Orchestrator()
