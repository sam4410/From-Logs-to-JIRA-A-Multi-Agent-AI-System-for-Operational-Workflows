def create_jira_ticket(task_id, log_summary, code_analysis):
    # Simulate ticket creation by summarizing input
    ticket = f"[JIRA Ticket]\nTask: {task_id}\nSummary: {log_summary[:100]}...\nAnalysis: {code_analysis[:100]}...\nStatus: Created (Simulated)"
    return ticket
