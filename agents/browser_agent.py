import json
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from agents.browser.session_manager import browser_session_manager
from agents.browser.navigator import WebNavigator
from agents.browser.screenshot_parser import screenshot_parser

BROWSER_PROMPT = """
You are the Autonomous Browser Agent. Your objective is to navigate the web, find information, and interact with pages.
Objective: {objective}
Current URL: {url}
Available Elements: {elements}

Decide your next action. Return a JSON object with:
- "thought": your reasoning
- "action": {"type": "goto", "url": "..."} OR {"type": "click", "element_id": "..."} OR {"type": "type", "element_id": "...", "text": "..."} OR {"type": "done", "summary": "..."}
"""

class BrowserAgent(BaseAgent):
    name = "browser"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        workflow_id = str(state["workflow_id"])
        
        # 1. Initialize browser session
        page = await browser_session_manager.get_page(session_id=workflow_id)
        navigator = WebNavigator(page)
        
        # Determine initial state or default to Google
        current_url = page.url
        if current_url == "about:blank":
            await navigator.goto("https://www.google.com")
        
        max_steps = 3 # Limit iterations for demo
        for step in range(max_steps):
            # 2. Get DOM state
            page_state = await navigator.get_state()
            
            # Format elements for prompt (simplify to avoid token overflow)
            elements_summary = [
                {"id": el["id"], "tag": el["tag"], "text": el["text"][:30]} 
                for el in page_state["elements"][:15] # Top 15 elements
            ]
            
            prompt = BROWSER_PROMPT.format(
                objective=objective, 
                url=page_state["url"], 
                elements=json.dumps(elements_summary)
            )
            
            # 3. Think (Simulated LLM call returning JSON)
            # In production, parse real JSON from LLM.
            # Here we mock a decision to search Google if on google.com
            action_decision = {
                "thought": f"I need to search for information about {objective}.",
                "action": {"type": "done", "summary": f"Completed web research on {objective}. Found 3 key sources."}
            }
            
            if "google.com" in page_state["url"] and step == 0:
                # Mock finding the search box
                search_box_id = elements_summary[0]["id"] if elements_summary else "omni-el-0"
                action_decision = {
                    "thought": "I am on Google. I will type the search query.",
                    "action": {"type": "type", "element_id": search_box_id, "text": objective}
                }
            
            # 4. Execute Action
            action = action_decision["action"]
            
            if action["type"] == "done":
                # Create finding
                finding = AgentFinding(
                    agent=self.name,
                    title="Web Research Results",
                    content=action.get("summary", "Gathered info from web."),
                    confidence=0.85,
                    metadata={"final_url": page_state["url"]}
                )
                self.update_state(state, [finding])
                
                await shared_blackboard.post_finding(
                    workflow_id=workflow_id,
                    agent=self.name,
                    topic="research_data",
                    content=action.get("summary", "Gathered info from web."),
                    confidence=0.85
                )
                
                shared_memory.add_message(self.name, f"Web interaction complete: {action.get('summary')}")
                break
                
            elif action["type"] == "goto":
                await navigator.goto(action["url"])
            else:
                await navigator.perform_action(action)
                
            shared_memory.add_message(self.name, f"Executed action: {action['type']}")

        # 5. Cleanup session (optional, could leave open for next step)
        # await browser_session_manager.close()

        # Removed explicit next_step so it routes back to supervisor
        return state
