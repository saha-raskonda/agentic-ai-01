
from abc import ABC, abstractmethod
from typing import Dict, Any, Type, List

class Tool(ABC):
    """
    Base class for all SRE Agentic tools.
    Defines the contract for tools that the agent can use to interact with SRE systems.
    """
    name: str
    description: str

    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Executes the tool's action.
        Args:
            **kwargs: Arguments specific to the tool's execution.
        Returns:
            A dictionary containing the result of the tool's execution.
        """
        pass

class QueryMetrics(Tool):
    name = "query_metrics"
    description = "Queries a simulated metrics system for given metrics and time range."

    def run(self, metric_name: str, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Simulates querying metrics.
        """
        print(f"DEBUG: QueryMetrics called for metric '{metric_name}' for {duration_minutes} minutes.")
        if "error_rate" in metric_name.lower():
            return {"metric": metric_name, "data": [{"timestamp": "...", "value": 0.15}, {"timestamp": "...", "value": 0.2}]}
        elif "latency" in metric_name.lower():
            return {"metric": metric_name, "data": [{"timestamp": "...", "value": 250}, {"timestamp": "...", "value": 300}]}
        return {"metric": metric_name, "data": [{"timestamp": "...", "value": 100}]}

class CorrelateLogs(Tool):
    name = "correlate_logs"
    description = "Correlates logs based on keywords or incident ID for a given time range."

    def run(self, keywords: List[str], incident_id: str = None, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Simulates correlating logs.
        """
        print(f"DEBUG: CorrelateLogs called for keywords {keywords} and incident_id {incident_id}.")
        if "error" in [k.lower() for k in keywords]:
            return {"logs": ["[ERROR] Service Unavailable", "[ERROR] Connection Refused"], "count": 2}
        elif "timeout" in [k.lower() for k in keywords]:
             return {"logs": ["Service A timeout connecting to Service B"], "count": 1}
        return {"logs": ["No critical logs found"], "count": 0}

class AnalyzeConfig(Tool):
    name = "analyze_config"
    description = "Analyzes configuration for a given service or deployment."

    def run(self, service_name: str) -> Dict[str, Any]:
        """
        Simulates analyzing configuration.
        """
        print(f"DEBUG: AnalyzeConfig called for service '{service_name}'.")
        if "auth-service" in service_name.lower():
            return {"service": service_name, "config": {"version": "1.2.3", "replicas": 3, "database_url": "jdbc:postgres://..."}, "recent_changes": ["Added new feature flag 'auth_v2'"]}
        return {"service": service_name, "config": {"version": "unknown"}, "recent_changes": []}

