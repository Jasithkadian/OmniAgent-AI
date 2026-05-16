import json
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from agents.core.agent_base import BaseAgent
from agents.core.state import WorkflowState, AgentFinding
from agents.core.memory import shared_memory
from app.core.observability import obs_manager

logger = logging.getLogger(__name__)

class VerificationResult(BaseModel):
    chain_of_thought: str = Field(description="Step-by-step reasoning for the audit")
    hallucination_score: float = Field(description="Score from 0 to 1, where 1 means high hallucination", ge=0, le=1)
    citation_accuracy: float = Field(description="Score from 0 to 1, where 1 means all citations are accurate", ge=0, le=1)
    reasoning_quality: float = Field(description="Score from 0 to 1, where 1 means high reasoning quality", ge=0, le=1)
    unsupported_claims: List[str] = Field(default_factory=list, description="Claims made in the report not found in sources")
    contradiction_flags: List[str] = Field(default_factory=list, description="Claims that contradict the sources")
    verification_summary: str = Field(description="Brief summary of the verification findings")
    is_verified: bool = Field(description="Whether the report passed verification and is safe to deliver")

CRITIC_PROMPT = """
You are the Lead Verification & Quality Critic. Your task is to rigorously verify the Technical Report against the retrieved Research Findings.

Objective: {objective}

Research Findings:
{findings}

Technical Report to Verify:
{report}

Verification Protocol:
1. PHASE 1: Fact Extraction - List all technical claims made in the report.
2. PHASE 2: Grounding - For each claim, find the specific research finding that supports it.
3. PHASE 3: Contradiction Check - Identify any report content that conflicts with research findings.
4. PHASE 4: Scoring - Assign scores based on the evidence gathered.

Verification Criteria:
1. Hallucination Detection: Are there any claims made that are not supported by the findings?
2. Citation Grounding: Are the citations used correctly and do they point to the right facts?
3. Contradiction Check: Does the report contradict any known facts from the findings?
4. Quality Assessment: Is the reasoning sound and technical structure logical?

Return your verification in structured JSON format following this schema:
{{
  "chain_of_thought": "Your step-by-step reasoning through the 4 phases...",
  "hallucination_score": 0.0,
  "citation_accuracy": 1.0,
  "reasoning_quality": 0.9,
  "unsupported_claims": [],
  "contradiction_flags": [],
  "verification_summary": "...",
  "is_verified": true
}}
"""

class CriticAgent(BaseAgent):
    name = "critic"

    async def run(self, state: WorkflowState) -> WorkflowState:
        objective = state["objective"]
        report = state["artifacts"].get("final_report", "")
        
        # Gather all research findings for grounding
        research_findings = [
            f"[{f['agent']}] {f['title']}: {f['content']}" 
            for f in state["findings"] 
            if f["agent"] == "research"
        ]
        
        if not report:
            logger.warning("No report found in artifacts for verification.")
            state["next_step"] = "report" # Try to regenerate or handle failure
            return state

        logger.info(f"Critic Agent verifying report for objective: {objective}")

        # 1. Reasoning phase: Verify report
        prompt = CRITIC_PROMPT.format(
            objective=objective,
            findings="\n\n".join(research_findings),
            report=report
        )

        chat = self.model.start_chat()
        response = await chat.send_message_async(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )

        try:
            verification_data = json.loads(response.text)

            # Record in Observability
            obs_manager.record_verification(
                str(state["workflow_id"]),
                score=verification_data.get("reasoning_quality", 0.0),
                hallucination=verification_data.get("hallucination_score", 0.0) > 0.1
            )

            # 2. Record verification finding

            finding = AgentFinding(
                agent=self.name,
                title="Verification & Quality Audit",
                content=verification_data.get("verification_summary", "Audit complete."),
                confidence=1.0 - verification_data.get("hallucination_score", 0.0),
                metadata=verification_data
            )
            self.update_state(state, [finding])
            
            # 3. Store metrics in artifacts
            state["artifacts"]["verification_metrics"] = verification_data
            
            # 4. Handle routing based on verification result
            if verification_data.get("is_verified", False):
                logger.info("Report verified successfully.")
                state["next_step"] = "supervisor" # Supervisor will end it
            else:
                logger.warning(f"Report failed verification: {verification_data.get('verification_summary')}")
                # We could route back to research or report, but for now we'll go to supervisor 
                # and let it decide (or fail if iterations exceeded)
                state["next_step"] = "supervisor"
                state["errors"].append(f"Verification failed: {verification_data.get('verification_summary')}")
            
            shared_memory.add_message(self.name, f"Verification complete. Result: {'Passed' if verification_data.get('is_verified') else 'Failed'}")
            
        except Exception as e:
            logger.error(f"Failed to parse verification response: {e}")
            state["errors"].append(f"Critic failure: {str(e)}")
            state["status"] = "failed"
            
        return state
