from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import logging
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
import time

from agents.core.state import AgentName, WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from app.core.config import settings
from app.core.observability import obs_manager

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Production-grade base agent class.
    Handles LLM reasoning, tool execution, and state management.
    """
    name: AgentName

    def __init__(self, model_name: str = "models/gemini-2.0-flash", tools: Optional[List[Any]] = None):
        self.model_name = model_name
        self.tools = tools or []
        
        # Configure Gemini
        if not settings.gemini_api_key:
            logger.error("GEMINI_API_KEY not found in settings. Agent reasoning will fail.")
        genai.configure(api_key=settings.gemini_api_key)
        
        # Prepare tools for Gemini
        gemini_tools = []
        for tool in self.tools:
            if hasattr(tool, "as_gemini_tool"):
                gemini_tools.append(tool.as_gemini_tool())
            else:
                # Fallback for simple tools
                gemini_tools.append(tool)
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=gemini_tools if gemini_tools else None
        )

    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """
        The entry point for LangGraph nodes.
        """
        logger.info(f"Agent {self.name} invoked (Iteration: {state['iteration_count']})")
        start_time = time.time()
        try:
            # 1. Update active agent and iteration count
            state["active_agent"] = self.name
            state["iteration_count"] += 1
            
            # 2. Run the agent logic
            updated_state = await self.run(state)
            
            # 3. Record metrics
            duration = time.time() - start_time
            obs_manager.record_agent_time(str(state["workflow_id"]), self.name, duration)
            
            # 4. Finalize state
            return updated_state
        except Exception as e:
            logger.exception(f"Fatal error in agent {self.name}: {str(e)}")
            state["errors"].append(f"[{self.name}] {str(e)}")
            state["status"] = "failed"
            return state

    @abstractmethod
    async def run(self, state: WorkflowState) -> WorkflowState:
        """Main execution logic for the agent."""
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def think(self, prompt: str, state: WorkflowState, tools: Optional[List[str]] = None) -> Any:
        """
        Executes a reasoning loop using the LLM.
        Supports tool calling and structured output.
        """
        logger.info(f"Agent {self.name} is reasoning...")
        
        # In a production system, we'd use a chat session to handle multi-turn tool calling
        chat = self.model.start_chat(enable_automatic_function_calling=True)
        
        try:
            response = await chat.send_message_async(prompt)
            # Log token usage if available in the future or via custom metrics
            return response.text
        except Exception as e:
            logger.error(f"LLM Reasoning failed for {self.name}: {e}")
            raise

    async def use_tools(self, tool_name: str, **kwargs) -> Any:
        """Execute a specific tool."""
        logger.info(f"{self.name} using tool: {tool_name}")
        for tool in self.tools:
            if hasattr(tool, "name") and tool.name == tool_name:
                return await tool.ainvoke(kwargs)
        return f"Tool {tool_name} not found."

    def update_state(self, state: WorkflowState, findings: List[AgentFinding]) -> WorkflowState:
        """Update state with new findings."""
        for finding in findings:
            state["findings"].append(finding.model_dump())
            shared_memory.add_finding(finding)
        return state
