
from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.log_tools import LogAnalysisTool

class LogAnalysisAgent:
    """Agent specialized in analyzing system logs for errors and patterns"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the log analysis agent"""
        self.llm = llm
        self.tool = LogAnalysisTool()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the log analysis agent with proper configuration"""
        return Agent(
            role="Senior Log Analysis Specialist",
            goal="Perform deep analysis of system logs to identify root causes and error patterns",
            backstory="""You are a veteran system administrator with 15+ years of experience 
            in log analysis. You can quickly identify critical errors, trace error propagation, 
            and understand system behavior patterns from log data. You excel at correlating 
            timestamps, identifying cascading failures, and extracting meaningful insights 
            from large volumes of log data.""",
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def create_task(self, user_query: str, task_id: str, is_performance_query: bool = False, is_error_query: bool = False) -> Task:
        """Create a log analysis task based on the user query"""
        
        analysis_focus = []
        if is_performance_query:
            analysis_focus.append("performance issues and bottlenecks")
        if is_error_query:
            analysis_focus.append("error patterns and exception traces")
        
        focus_text = ", ".join(analysis_focus) if analysis_focus else "general error patterns"
        
        return Task(
            description=f"""
            Perform comprehensive log analysis for task {task_id}:
            
            PRIMARY OBJECTIVES:
            1. Search all log files for entries related to {task_id}
            2. Identify and classify all errors, warnings, and exceptions
            3. Create a timeline of events leading to the issue
            4. Extract stack traces and error messages
            5. Determine error severity and impact
            
            ANALYSIS FOCUS:
            - Primary focus: {focus_text}
            - Look for: exceptions, timeouts, connection failures, null pointer errors
            - Timeline reconstruction from log timestamps
            - Error pattern correlation across multiple log files
            
            DELIVERABLES:
            - Complete error timeline with timestamps
            - Error classification and severity assessment
            - Key error messages and stack traces
            - Potential root cause hypotheses based on log patterns
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agent,
            expected_output="Comprehensive log analysis report with error timeline, classification, and root cause hypotheses"
        )
    
    def get_agent(self) -> Agent:
        """Get the agent instance"""
        return self.agent
