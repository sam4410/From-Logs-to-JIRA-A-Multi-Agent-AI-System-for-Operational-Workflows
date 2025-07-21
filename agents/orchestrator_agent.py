import re
from datetime import datetime
from typing import List, Dict, Any
from crewai import Crew, Process
from langchain_openai import ChatOpenAI

from config.config import Config
from .log_agent import LogAnalysisAgent
from .code_agent import CodeAnalysisAgent
from .database_agent import DatabaseMetricsAgent
from .incident_agent import IncidentHistoryAgent
from .jira_agent import JiraTicketAgent
from tools.analysis_utils import AnalysisUtils

class OpsAnalysisOrchestrator:
    """Main orchestrator that coordinates all analysis agents"""
    
    def __init__(self):
        """Initialize the orchestrator with all agents"""
        Config.validate_config()
        
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )
        
        # Initialize all agents
        self.log_agent = LogAnalysisAgent(self.llm)
        self.code_agent = CodeAnalysisAgent(self.llm)
        self.db_agent = DatabaseMetricsAgent(self.llm)
        self.incident_agent = IncidentHistoryAgent(self.llm)
        self.jira_agent = JiraTicketAgent(self.llm)
        
        self.analysis_results = {}
    
    def create_analysis_tasks(self, user_query: str):
        """Create enhanced tasks with better context and dependencies"""
        
        # Extract task ID and classify query type
        task_id_match = re.search(r"TID[-_]?\d+", user_query)
        task_id = task_id_match.group(0) if task_id_match else "UNKNOWN"
        
        query_lower = user_query.lower()
        is_performance_query = any(word in query_lower for word in Config.PERFORMANCE_KEYWORDS)
        is_error_query = any(word in query_lower for word in Config.ERROR_QUERY_KEYWORDS)
        
        # Create tasks for each agent
        tasks = []
        
        # Task 1: Log Analysis
        log_task = self.log_agent.create_task(user_query, task_id, is_performance_query, is_error_query)
        tasks.append(log_task)
        
        # Task 2: Code Analysis (depends on log analysis)
        code_task = self.code_agent.create_task(user_query, task_id, context=[log_task])
        tasks.append(code_task)
        
        # Task 3: Database Metrics Analysis
        db_task = self.db_agent.create_task(user_query, task_id)
        tasks.append(db_task)
        
        # Task 4: Incident History Research (depends on log and code analysis)
        incident_task = self.incident_agent.create_task(user_query, task_id, context=[log_task, code_task])
        tasks.append(incident_task)
        
        # Task 5: JIRA Ticket Creation (depends on all previous tasks)
        jira_task = self.jira_agent.create_task(user_query, task_id, context=[log_task, code_task, db_task, incident_task])
        tasks.append(jira_task)
        
        return tasks
    
    def execute_analysis(self, user_query: str) -> str:
        """Execute the complete operational analysis with enhanced reporting"""
        
        print(f"\n🤖 Multi-Agent Operational Intelligence System")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📥 Query: {user_query}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Extract task ID for tracking
        task_id_match = re.search(r"TID[-_]?\d+", user_query)
        task_id = task_id_match.group(0) if task_id_match else "UNKNOWN"
        
        print(f"🎯 Target Task: {task_id}")
        print(f"🔍 Analysis Type: Operational Intelligence")
        
        try:
            # Create enhanced tasks
            tasks = self.create_analysis_tasks(user_query)
            
            # Get all agent instances
            agents = [
                self.log_agent.get_agent(),
                self.code_agent.get_agent(),
                self.db_agent.get_agent(),
                self.incident_agent.get_agent(),
                self.jira_agent.get_agent()
            ]
            
            # Create crew with sequential process for better context flow
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True,
                memory=True,  # Enable memory for better context retention
            )
            
            print(f"\n🚀 Initiating multi-agent analysis...")
            print(f"👥 Agents: {len(agents)} specialized agents")
            print(f"📋 Tasks: {len(tasks)} sequential analysis tasks")
            
            # Execute the crew
            result = crew.kickoff()
            
            # Generate final summary
            summary = self._generate_executive_summary(result, task_id)
            
            print(f"\n✅ Analysis Complete!")
            print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"\n{summary}")
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Analysis failed: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _generate_executive_summary(self, result: str, task_id: str) -> str:
        """Generate an executive summary of the analysis"""
        
        summary_lines = [
            f"🎯 EXECUTIVE SUMMARY - Task {task_id}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        
        # Extract key findings (simplified pattern matching)
        result_lower = result.lower()
        
        if "failed" in result_lower or "error" in result_lower:
            summary_lines.append("🚨 STATUS: Critical issue identified requiring immediate attention")
        elif "warning" in result_lower:
            summary_lines.append("⚠️  STATUS: Warning conditions detected, monitoring recommended")
        else:
            summary_lines.append("✅ STATUS: Analysis complete, no critical issues found")
        
        # Key findings
        if "nullpointer" in result_lower:
            summary_lines.append("🔍 KEY FINDING: Null pointer exception detected in code")
        if "timeout" in result_lower:
            summary_lines.append("🔍 KEY FINDING: Connection timeout issues identified")
        if "memory" in result_lower:
            summary_lines.append("🔍 KEY FINDING: Memory-related issues detected")
        
        # Add recommendations
        recommendations = AnalysisUtils.generate_recommendations({"result": result})
        if recommendations:
            summary_lines.append("\n💡 TOP RECOMMENDATIONS:")
            for rec in recommendations[:3]:  # Top 3 recommendations
                summary_lines.append(f"   {rec}")
        
        summary_lines.extend([
            f"\n📊 ANALYSIS SCOPE:",
            f"   • Log files analyzed for error patterns",
            f"   • Code base reviewed for potential bugs", 
            f"   • Performance metrics evaluated",
            f"   • Historical incidents researched",
            f"   • JIRA ticket prepared for tracking",
            f"\n🎫 NEXT STEPS: Review generated JIRA ticket for detailed action items"
        ])
        
        return "\n".join(summary_lines)
