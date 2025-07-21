
from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.incident_tools import IncidentHistoryTool
from typing import List

class IncidentHistoryAgent:
    """Agent specialized in researching historical incidents and resolutions"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the incident history agent"""
        self.llm = llm
        self.tool = IncidentHistoryTool()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the incident history agent with proper configuration"""
        return Agent(
            role="Senior Incident Management Specialist",
            goal="Research historical incidents, identify patterns, and provide proven resolution strategies",
            backstory="""You are a senior Site Reliability Engineer (SRE) with extensive experience 
            in incident response, post-mortem analysis, and knowledge management. You have 10+ years 
            of experience managing complex system incidents and excel at finding patterns in historical 
            data, identifying root causes, and predicting potential issues. You have a deep understanding 
            of incident lifecycle management and are skilled at extracting actionable insights from past 
            incidents to prevent future occurrences.""",
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def create_task(self, user_query: str, task_id: str, context: List[Task] = None) -> Task:
        """Create an incident history research task"""
        
        context_note = ""
        if context:
            context_note = """
            CONTEXT INTEGRATION:
            Use insights from log analysis and code review to refine search terms and improve 
            relevance of historical incident matches. Focus on incidents with similar error 
            patterns, code issues, or system behaviors.
            """
        
        return Task(
            description=f"""
            Research historical incidents similar to current {task_id} issue:
            
            PRIMARY OBJECTIVES:
            1. Search incident database for similar error patterns and symptoms
            2. Find incidents with matching task types, error signatures, or failure modes
            3. Extract successful resolution strategies and documented fixes
            4. Identify recurring patterns and systemic issues across incidents
            5. Compile lessons learned and preventive measures from past incidents
            6. Analyze incident escalation patterns and response effectiveness
            
            SEARCH STRATEGY:
            - Exact task ID matches for direct historical relevance
            - Similar error message patterns and exception types
            - Matching system components and service dependencies
            - Time-based correlation analysis (seasonal patterns, deployment windows)
            - Severity and impact classification alignment
            - Resolution strategy categorization and effectiveness analysis
            
            PATTERN ANALYSIS:
            - Frequency of similar incident types and occurrence patterns
            - Mean time to detection (MTTD) and mean time to resolution (MTTR) trends
            - Common root causes and contributing factors across similar incidents
            - Escalation patterns and team involvement requirements
            - Success rates of different resolution approaches
            - Customer impact patterns and business cost analysis
            
            KNOWLEDGE EXTRACTION:
            - Document proven fix procedures and step-by-step resolutions
            - Extract troubleshooting playbooks and diagnostic procedures
            - Identify effective monitoring and alerting configurations
            - Compile prevention strategies that worked in similar cases
            - Note configuration changes or code fixes that resolved issues
            - Document team coordination and communication patterns that worked
            
            RISK ASSESSMENT:
            - Evaluate likelihood of incident recurrence based on historical data
            - Assess potential for escalation based on similar incident patterns
            - Identify early warning signs from historical incident timelines
            - Analyze blast radius and impact scope predictions
            - Review dependencies and cascade failure potential
            
            {context_note}
            
            DELIVERABLES:
            - Historical incident summary with relevance scoring
            - Pattern analysis report with frequency and trend data
            - Proven resolution strategies ranked by success rate and applicability
            - Risk assessment with recurrence likelihood and impact predictions
            - Preventive measure recommendations based on lessons learned
            - Escalation pathway suggestions based on similar incident handling
            - Knowledge base updates and documentation improvement suggestions
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agent,
            expected_output="Comprehensive incident history analysis with pattern identification, proven resolution strategies, and preventive recommendations",
            context=context or []
        )
    
    def get_agent(self) -> Agent:
        """Get the agent instance"""
        return self.agent
