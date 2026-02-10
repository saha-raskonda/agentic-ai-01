import uuid
from typing import Dict, Any, List

from agent_core import AgentState, Planner, PolicyEngine, Verifier, Memory
from tools import QueryMetrics, CorrelateLogs, AnalyzeConfig, Tool

class SREAgent:
    def __init__(self):
        self.tools: Dict[str, Tool] = {
            "query_metrics": QueryMetrics(),
            "correlate_logs": CorrelateLogs(),
            "analyze_config": AnalyzeConfig()
            # Add other tools as they are developed
        }
        self.planner = Planner(self.tools)
        self.policy_engine = PolicyEngine()
        self.verifier = Verifier()
        self.memory = Memory()

    def process_alert(self, incident_description: str) -> AgentState:
        incident_id = str(uuid.uuid4())
        state = AgentState(incident_id=incident_id, symptoms=[incident_description])
        state.confidence = 0.5  # Baseline confidence to allow initial sensing tools
        self.memory.update_context(state, "incident_description", incident_description)

        print(f"Agent initiated for incident: {incident_id} - '{incident_description}'")

        # Phase 1: Sense and Plan initial actions
        print("\nPhase 1: Sensing and Planning...")
        triage_steps = self.planner.plan_triage_steps(incident_description, state)
        print(f"Planned steps: {len(triage_steps)} actions.")

        # Phase 2: Act (execute tools) and Observe
        print("\nPhase 2: Acting and Observing...")
        for step in triage_steps:
            tool: Tool = step["tool"]
            args = step["args"]
            tool_name = tool.name

            if self.policy_engine.check_action_allowed(tool_name, args, state):
                print(f"  Executing tool: {tool_name} with args: {args}")
                result = tool.run(**args)
                state.actions_taken.append({"tool": tool_name, "args": args, "result": result})
                self.memory.update_context(state, f"tool_output_{tool_name}_{len(state.actions_taken)}", result)
                
                # Update symptoms based on tool output
                if "metric" in result:
                    if result["data"] and any(d.get("value", 0) > 0.1 for d in result["data"]): # Example threshold
                        state.symptoms.append(f"High {result['metric']}: {result['data']}")
                if "logs" in result and result["count"] > 0:
                    state.symptoms.append(f"Critical logs found: {result['logs']}")
                if "config" in result and result.get("recent_changes"):
                    state.symptoms.append(f"Recent config changes for {result['service']}: {result['recent_changes']}")
            else:
                print(f"  Policy engine blocked action: {tool_name} with args: {args}")
                # Policy engine already sets requires_human and adds hypothesis if blocked
                break # Stop further automated actions if policy blocks

        # Phase 3: Reason and Formulate Hypotheses/Suggestions
        print("\nPhase 3: Reasoning and Hypothesizing...")
        self._formulate_hypotheses(state)
        self._suggest_remediation(state)

        print("\nPhase 4: Verification (simulated)")
        # For insights-only, verification is about confidence in insights and whether human is needed
        # Incorporate mock verification results into confidence
        if self.verifier.verify_metrics_improvement({}, {}): # Mock call for now
            state.confidence += 0.05
        if self.verifier.verify_issue_resolved(state):
            state.confidence += 0.1
        
        # Ensure confidence doesn't exceed 1.0
        state.confidence = min(state.confidence, 1.0)

        # If confidence is low after all steps, or if any policy required human intervention, set requires_human
        state.requires_human = state.requires_human or (state.confidence < 0.6)

        print(f"\nAgent processing complete for incident {incident_id}.")
        return state

    def _formulate_hypotheses(self, state: AgentState):
        """Generates hypotheses based on collected symptoms and tool outputs."""
        if any("High error_rate" in s for s in state.symptoms):
            state.hypotheses.append("Potential service degradation due to elevated error rates.")
            known_issues = self.memory.retrieve_knowledge("error rate spikes")
            if known_issues:
                state.hypotheses.extend(known_issues)
        if any("Critical logs found" in s for s in state.symptoms):
            state.hypotheses.append("Error messages in logs indicate a specific fault.")
        if any("Recent config changes" in s for s in state.symptoms):
            state.hypotheses.append("Recent configuration changes might be the root cause.")
        if not state.hypotheses:
            state.hypotheses.append("No clear hypotheses formed yet. More data might be needed or issue is transient.")

    def _suggest_remediation(self, state: AgentState):
        """Suggests remediation steps based on hypotheses. (Insights only)"""
        if "Potential service degradation due to elevated error rates." in state.hypotheses:
            state.hypotheses.append("Suggested remediation: Investigate recent deployments or upstream dependencies. Consider checking dashboard for 'error_rate' and 'latency'.")
        if "Error messages in logs indicate a specific fault." in state.hypotheses:
            state.hypotheses.append("Suggested remediation: Examine full logs around the time of the incident for specific error codes or stack traces.")
        if "Recent configuration changes might be the root cause." in state.hypotheses:
            state.hypotheses.append("Suggested remediation: Review changes made to the affected service configuration. Consider rolling back if recent changes are suspected.")
        
        # Example of using memory for suggestions
        if "high latency" in " ".join(state.symptoms).lower():
            runbook = self.memory.long_term_knowledge["runbook_links"].get("db_overload")
            if runbook:
                state.hypotheses.append(f"Suggested remediation: Check database load and connection pools. Refer to runbook: {runbook}")

    def _assess_confidence(self, state: AgentState) -> float:
        """Assesses the agent's confidence in its findings based on accumulated data."""
        confidence = 0.5 # Start with baseline confidence from process_alert
        
        if state.hypotheses and len(state.hypotheses) > 1: # More specific hypotheses
            confidence += 0.1
        if state.symptoms and len(state.symptoms) > 1: # More data gathered
            confidence += 0.2
        if any("critical" in s.lower() for s in state.symptoms) and any("error_rate" in str(action) for action in state.actions_taken):
            confidence += 0.1 # Specific data correlates with critical issue

        return min(confidence, 1.0)


# Example Usage (for testing the agent)
if __name__ == "__main__":
    agent = SREAgent()

    print("--- Incident 1: High Latency in Web Service ---")
    final_state_1 = agent.process_alert("High latency detected in web service 'frontend'.")
    print("\nFinal Agent State 1:")
    print(f"  Incident ID: {final_state_1.incident_id}")
    print(f"  Symptoms: {final_state_1.symptoms}")
    print(f"  Hypotheses: {final_state_1.hypotheses}")
    print(f"  Actions Taken (Tool Calls): {len(final_state_1.actions_taken)}")
    print(f"  Confidence: {final_state_1.confidence:.2f}")
    print(f"  Requires Human: {final_state_1.requires_human}")
    # print(f"  Context: {final_state_1.context}")

    print("\n" + "="*80 + "\n")

    print("--- Incident 2: Authentication Service Errors ---")
    final_state_2 = agent.process_alert("Authentication service returning 5xx errors after recent deployment.")
    print("\nFinal Agent State 2:")
    print(f"  Incident ID: {final_state_2.incident_id}")
    print(f"  Symptoms: {final_state_2.symptoms}")
    print(f"  Hypotheses: {final_state_2.hypotheses}")
    print(f"  Actions Taken (Tool Calls): {len(final_state_2.actions_taken)}")
    print(f"  Confidence: {final_state_2.confidence:.2f}")
    print(f"  Requires Human: {final_state_2.requires_human}")
    # print(f"  Context: {final_state_2.context}")