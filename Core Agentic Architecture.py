# multi_agent_ops_ai/main.py

from agents.orchestrator_agent import OrchestratorAgent

def run_query(user_query):
    print("\n[System] Received query:", user_query)
    orchestrator = OrchestratorAgent()
    result = orchestrator.handle_query(user_query)
    print("\n[System] Final response:")
    print(result)

if __name__ == "__main__":
    sample_query = "Why is task TID-12345 failing?"
    run_query(sample_query)


# multi_agent_ops_ai/agents/orchestrator_agent.py
from agents.log_agent import LogAgent
from agents.code_agent import CodeAgent
from agents.database_agent import DatabaseAgent
from agents.incident_agent import IncidentAgent
from agents.jira_agent import JiraAgent

class OrchestratorAgent:
    def __init__(self):
        self.log_agent = LogAgent()
        self.code_agent = CodeAgent()
        self.db_agent = DatabaseAgent()
        self.incident_agent = IncidentAgent()
        self.jira_agent = JiraAgent()

    def handle_query(self, query: str) -> str:
        context = {"query": query, "task_id": self.extract_task_id(query)}
        agent_plan = self.classify_agents_needed(query)

        print("[Orchestrator] Plan:", agent_plan)

        if "log" in agent_plan:
            context["log_summary"] = self.log_agent.analyze_logs(context)

        if "code" in agent_plan and "log_summary" in context:
            context["code_analysis"] = self.code_agent.analyze_code(context)

        if "database" in agent_plan:
            context["db_metrics"] = self.db_agent.query_metrics(context)

        if "incident" in agent_plan:
            context["incident_history"] = self.incident_agent.search_history(context)

        if "jira" in agent_plan:
            context["jira_ticket"] = self.jira_agent.create_ticket(context)

        return self.summarize_response(context)

    def extract_task_id(self, query):
        import re
        match = re.search(r"TID[-_]?\d+", query)
        return match.group(0) if match else "UNKNOWN"

    def classify_agents_needed(self, query):
        query = query.lower()
        plan = []
        if "fail" in query or "error" in query:
            plan.extend(["log", "code"])
        if "latency" in query or "time" in query:
            plan.append("database")
        if "incident" in query:
            plan.append("incident")
        if "jira" in query or "ticket" in query or "escalate" in query:
            plan.append("jira")
        return plan

    def summarize_response(self, context):
        parts = []
        if "log_summary" in context:
            parts.append(f"Log Summary: {context['log_summary']}")
        if "code_analysis" in context:
            parts.append(f"Code Analysis: {context['code_analysis']}")
        if "db_metrics" in context:
            parts.append(f"DB Metrics: {context['db_metrics']}")
        if "incident_history" in context:
            parts.append(f"Incident History: {context['incident_history']}")
        if "jira_ticket" in context:
            parts.append(f"JIRA Ticket Created: {context['jira_ticket']}")
        return "\n".join(parts)


# multi_agent_ops_ai/agents/log_agent.py
import os
from tools.log_tools import classify_log_error

class LogAgent:
    def analyze_logs(self, context):
        task_id = context.get("task_id")
        log_dir = "data/logs"
        matching_lines = []

        for filename in os.listdir(log_dir):
            if filename.endswith(".log"):
                with open(os.path.join(log_dir, filename), "r") as file:
                    for line in file:
                        if task_id in line:
                            matching_lines.append(line.strip())

        if not matching_lines:
            return f"No log entries found for task {task_id}."

        summary = classify_log_error(matching_lines)
        return summary

# multi_agent_ops_ai/tools/log_tools.py
def classify_log_error(log_lines):
    error_keywords = ["exception", "traceback", "fail", "error"]
    issues = []

    for line in log_lines:
        for keyword in error_keywords:
            if keyword in line.lower():
                issues.append(f"Detected {keyword}: {line}")

    if not issues:
        return "Log analysis did not reveal any errors or failures."

    return "\n".join(issues)

# multi_agent_ops_ai/agents/code_agent.py
from tools.code_tools import analyze_code_snippets

class CodeAgent:
    def analyze_code(self, context):
        task_id = context.get("task_id")
        error_summary = context.get("log_summary", "")

        # Simulate finding relevant code from error summary
        code_context = self.retrieve_relevant_code(task_id, error_summary)
        analysis = analyze_code_snippets(code_context, error_summary)
        return analysis

    def retrieve_relevant_code(self, task_id, error_summary):
        # Placeholder for filtering files from data/codebase/
        import os
        codebase_dir = "data/codebase"
        code_snippets = []

        for filename in os.listdir(codebase_dir):
            if filename.endswith(".java") or filename.endswith(".py"):
                with open(os.path.join(codebase_dir, filename), "r") as f:
                    snippet = f.read()
                    if task_id in snippet or any(term in snippet for term in error_summary.split()):
                        code_snippets.append(snippet[:500])  # Take first 500 chars

        return code_snippets

# multi_agent_ops_ai/tools/code_tools.py
def analyze_code_snippets(snippets, error_summary):
    if not snippets:
        return "No related code snippets found."

    results = [f"Found {len(snippets)} relevant code snippet(s)."]
    for i, snippet in enumerate(snippets):
        results.append(f"Snippet {i+1} (preview):\n{snippet}\n")

    results.append("Potential cause based on log summary: " + error_summary[:150] + "...")
    return "\n".join(results)


# multi_agent_ops_ai/agents/database_agent.py
from tools.db_tools import fetch_task_metrics

class DatabaseAgent:
    def query_metrics(self, context):
        task_id = context.get("task_id")
        metrics = fetch_task_metrics(task_id)
        if not metrics:
            return f"No database metrics found for task {task_id}."

        return f"Start Time: {metrics['start_time']}, End Time: {metrics['end_time']}, Duration: {metrics['duration']} seconds"


# multi_agent_ops_ai/tools/db_tools.py
import sqlite3

def fetch_task_metrics(task_id):
    conn = sqlite3.connect("data/metrics.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT start_time, end_time, duration
            FROM task_metrics
            WHERE task_id = ?
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "start_time": row[0],
                "end_time": row[1],
                "duration": row[2]
            }
        else:
            return None

    except Exception as e:
        conn.close()
        return None


# multi_agent_ops_ai/agents/incident_agent.py
from tools.incident_tools import search_similar_incidents

class IncidentAgent:
    def search_history(self, context):
        task_id = context.get("task_id")
        summary = context.get("log_summary", "")
        results = search_similar_incidents(task_id, summary)
        return results


# multi_agent_ops_ai/tools/incident_tools.py
import pandas as pd

def search_similar_incidents(task_id, error_summary):
    try:
        df = pd.read_csv("data/incidents.csv")
        matched = df[df['description'].str.contains(task_id, case=False, na=False)]

        if matched.empty:
            matched = df[df['description'].str.contains(error_summary[:50], case=False, na=False)]

        if matched.empty:
            return f"No similar incidents found for task {task_id}."

        incidents = []
        for _, row in matched.iterrows():
            incidents.append(f"Date: {row['date']}, Summary: {row['description']}")

        return "\n".join(incidents)

    except Exception as e:
        return f"Incident lookup failed: {str(e)}"


# multi_agent_ops_ai/agents/jira_agent.py
from tools.jira_tools import create_jira_ticket

class JiraAgent:
    def create_ticket(self, context):
        task_id = context.get("task_id")
        error_summary = context.get("log_summary", "")
        code_analysis = context.get("code_analysis", "")
        return create_jira_ticket(task_id, error_summary, code_analysis)


# multi_agent_ops_ai/tools/jira_tools.py
def create_jira_ticket(task_id, log_summary, code_analysis):
    # Simulate ticket creation by summarizing input
    ticket = f"[JIRA Ticket]\nTask: {task_id}\nSummary: {log_summary[:100]}...\nAnalysis: {code_analysis[:100]}...\nStatus: Created (Simulated)"
    return ticket
