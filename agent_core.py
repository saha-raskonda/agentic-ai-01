from dataclasses import dataclass, field
from typing import List, Dict, Type, Any
from tools import Tool, QueryMetrics, CorrelateLogs, AnalyzeConfig

@dataclass
class AgentState:
    incident_id: str
    symptoms: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    requires_human: bool = False
    context: Dict[str, Any] = field(default_factory=dict) # Short-term memory

class Planner:
    """
    A simple rule-based planner for the SRE agent.
    In a real system, this would involve more sophisticated logic, possibly an LLM.
    """
    def __init__(self, available_tools: Dict[str, Tool]):
        self.available_tools = available_tools

    def plan_triage_steps(self, incident_description: str, current_state: AgentState) -> List[Dict[str, Any]]:
        """
        Generates a sequence of steps for incident triage based on description and current state.
        Each step is a dict indicating which tool to use and with what arguments.
        """
        steps = []
        # Initial steps for any incident
        steps.append({"tool": self.available_tools["query_metrics"], "args": {"metric_name": "error_rate"}})
        steps.append({"tool": self.available_tools["query_metrics"], "args": {"metric_name": "latency"}})
        steps.append({"tool": self.available_tools["correlate_logs"], "args": {"keywords": ["error", "timeout"], "incident_id": current_state.incident_id}})
        
        if "authentication" in incident_description.lower() or "auth" in incident_description.lower():
            steps.append({"tool": self.available_tools["analyze_config"], "args": {"service_name": "auth-service"}})
        elif "database" in incident_description.lower() or "db" in incident_description.lower():
            steps.append({"tool": self.available_tools["analyze_config"], "args": {"service_name": "db-service"}})

        # More sophisticated planning would go here based on current_state.symptoms and previous tool outputs
        return steps

class PolicyEngine:
    """
    Enforces policies and guardrails.
    For this prototype, it's a simple function, but in production, this would be a robust system.
    """
    def check_action_allowed(self, tool_name: str, args: Dict[str, Any], current_state: AgentState) -> bool:
        """
        Checks if a given action (tool usage) is allowed by policy.
        """
        # Define what constitutes a "write" action for future policies
        WRITE_ACTIONS = ["scale_deployment", "restart_workload", "rollback_deployment"] # Placeholder names

        # Policy 1: Read-only first principle - block write actions for now
        if tool_name in WRITE_ACTIONS:
            print(f"Policy Violation: Attempted write action '{tool_name}'. 'Read-only first' policy enforced. Requires explicit human approval.")
            current_state.requires_human = True
            current_state.hypotheses.append(f"Write action '{tool_name}' blocked by policy; human approval required.")
            return False

        # Policy 2: Allow initial sensing tools to run regardless of initial confidence
        # This check should be after write action check, as even initial writes should be blocked
        if not current_state.actions_taken:
            return True

        # Policy 3: General confidence threshold for any further actions
        if current_state.confidence < 0.6 and not current_state.requires_human: # Increased threshold for subsequent actions
            print(f"Policy Violation: Low confidence ({current_state.confidence}), requiring human intervention for subsequent actions.")
            current_state.requires_human = True
            current_state.hypotheses.append("Low confidence detected; human review required before further actions.")
            return False
        
        # Policy 4: Specific tool restrictions (placeholder)
        if tool_name == "scale_deployment": # This tool is not yet implemented but is in the requirements
            if "prod" in args.get("namespace", "") and "business_hours" in current_state.context: # Assuming context holds business_hours status
                print("Policy Violation: Cannot scale prod during business hours without explicit override.")
                current_state.requires_human = True
                current_state.hypotheses.append("Scaling production during business hours detected; human override required.")
                return False
        
        return True

class Verifier:
    """
    Verifies the outcome of actions or confirms system state.
    """
    def verify_metrics_improvement(self, initial_metrics: Dict[str, Any], current_metrics: Dict[str, Any]) -> bool:
        """
        Simulates verifying if metrics have improved.
        """
        print("DEBUG: Verifying metrics improvement.")
        # Placeholder logic
        return True

    def verify_issue_resolved(self, current_state: AgentState) -> bool:
        """
        Simulates verifying if the incident has been resolved based on current state.
        """
        print("DEBUG: Verifying if issue is resolved.")
        # Placeholder: If no critical symptoms, assume resolved for now
        return not any("critical" in s.lower() for s in current_state.symptoms)

class Memory:
    """
    Manages short-term and long-term memory for the agent.
    For this prototype, short-term memory is part of AgentState.context.
    Long-term memory is a placeholder.
    """
    def __init__(self):
        self.long_term_knowledge = {
            "known_issues": ["high latency often indicates database load", "error rate spikes after new deployments"],
            "runbook_links": {"db_overload": "http://runbooks.example.com/db_overload"}
        }

    def retrieve_knowledge(self, query: str) -> List[str]:
        """
        Retrieves relevant knowledge from long-term memory.
        """
        results = []
        for issue in self.long_term_knowledge["known_issues"]:
            if query.lower() in issue.lower():
                results.append(issue)
        return results

    def update_context(self, state: AgentState, key: str, value: Any):
        """
        Updates the short-term context in the agent state.
        """
        state.context[key] = value