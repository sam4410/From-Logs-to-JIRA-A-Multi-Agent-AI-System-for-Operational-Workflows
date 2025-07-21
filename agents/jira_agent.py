
from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.jira_tools import JiraTicketTool
from typing import List

class JiraTicketAgent:
    """Agent specialized in creating comprehensive JIRA tickets for operational issues"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the JIRA ticket agent"""
        self.llm = llm
        self.tool = JiraTicketTool()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the JIRA ticket agent with proper configuration"""
        return Agent(
            role="Senior Technical Project Manager & Documentation Specialist",
            goal="Create comprehensive, actionable JIRA tickets that consolidate all analysis findings and provide clear resolution pathways",
            backstory="""You are a senior technical project manager with 12+ years of experience 
            in incident management, technical documentation, and cross-functional team coordination. 
            You excel at synthesizing complex technical information into clear, actionable work items 
            that development, operations, and support teams can execute effectively. You understand 
            JIRA best practices, ticket lifecycle management, and have expertise in creating detailed 
            user stories, acceptance criteria, and technical specifications. You are skilled at 
            prioritizing work, estimating effort, and ensuring proper tracking and accountability.""",
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def create_task(self, user_query: str, task_id: str, context: List[Task] = None) -> Task:
        """Create a JIRA ticket creation task based on all previous analysis"""
        
        context_note = ""
        if context:
            context_note = """
            CONTEXT INTEGRATION:
            Synthesize findings from all previous analysis tasks:
            - Log analysis results (error patterns, timelines, severity)
            - Code review findings (bugs, security issues, technical debt)
            - Performance metrics analysis (bottlenecks, resource utilization)
            - Historical incident research (patterns, proven solutions, preventive measures)
            
            Use these inputs to create a comprehensive, well-structured JIRA ticket that serves 
            as the single source of truth for resolving this operational issue.
            """
        
        return Task(
            description=f"""
            Create comprehensive JIRA ticket(s) for resolving {task_id} operational issue:
            
            PRIMARY OBJECTIVES:
            1. Synthesize all analysis findings into coherent problem statement
            2. Create detailed JIRA ticket with proper categorization and priority
            3. Define clear acceptance criteria and success metrics
            4. Establish actionable work breakdown and task dependencies
            5. Document all relevant technical details and context
            6. Assign appropriate labels, components, and team assignments
            
            TICKET STRUCTURE REQUIREMENTS:
            
            SUMMARY:
            - Clear, concise title that captures the core issue
            - Include task ID and severity level in title
            - Use standardized naming conventions for operational issues
            
            DESCRIPTION:
            - Executive summary of the problem and business impact
            - Detailed problem statement with symptoms and scope
            - Timeline of events and discovery process
            - Environment and system context information
            
            ANALYSIS FINDINGS:
            - Log analysis summary with key error patterns
            - Code review findings with specific file/line references
            - Performance metrics analysis with baseline comparisons
            - Historical incident patterns and recurrence risk
            - Root cause analysis with confidence levels
            
            TECHNICAL DETAILS:
            - System components affected and dependency mapping
            - Error messages, stack traces, and diagnostic data
            - Configuration details and environment specifications
            - Resource utilization patterns and capacity considerations
            
            RESOLUTION STRATEGY:
            - Recommended fix approaches ranked by priority and risk
            - Step-by-step implementation plan with dependencies
            - Testing and validation requirements
            - Rollback procedures and risk mitigation strategies
            - Resource requirements and time estimates
            
            ACCEPTANCE CRITERIA:
            - Specific, measurable success criteria
            - Performance benchmarks and SLA requirements
            - Monitoring and alerting validation steps
            - User acceptance and business validation criteria
            
            WORK BREAKDOWN:
            - Subtasks with clear owners and dependencies
            - Development tasks with technical specifications
            - Testing tasks with specific test scenarios
            - Deployment tasks with rollout strategies
            - Documentation and knowledge transfer tasks
            
            PRIORITY AND CLASSIFICATION:
            - Business impact assessment (Critical/High/Medium/Low)
            - Technical complexity evaluation
            - Customer impact scope and urgency
            - Regulatory or compliance implications
            - Resource availability and capacity planning
            
            METADATA AND TRACKING:
            - Appropriate JIRA project and issue type selection
            - Component assignments and team ownership
            - Labels for categorization and search optimization
            - Epic/Initiative linking for strategic alignment
            - Sprint planning and release targeting recommendations
            
            COMMUNICATION PLAN:
            - Stakeholder notification requirements
            - Status update frequency and communication channels
            - Escalation procedures and decision points
            - Post-resolution communication and lessons learned sharing
            
            PREVENTION AND MONITORING:
            - Long-term prevention strategies and system improvements
            - Enhanced monitoring and alerting recommendations
            - Process improvements and automation opportunities
            - Knowledge base updates and documentation requirements
            
            {context_note}
            
            DELIVERABLES:
            - Primary JIRA ticket with comprehensive problem documentation
            - Subtask breakdown with clear ownership and timelines
            - Risk assessment with mitigation strategies
            - Implementation roadmap with milestones and checkpoints
            - Communication plan with stakeholder matrix
            - Post-resolution follow-up tasks and improvement initiatives
            - Documentation and knowledge transfer requirements
            
            QUALITY STANDARDS:
            - All technical details must be accurate and verifiable
            - Acceptance criteria must be specific and testable
            - Resource estimates should be realistic and well-justified
            - All findings from previous analysis must be properly integrated
            - Ticket must follow organizational JIRA standards and templates
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agent,
            expected_output="Complete JIRA ticket creation with comprehensive problem documentation, detailed resolution strategy, clear acceptance criteria, and actionable work breakdown structure",
            context=context or []
        )
    
    def get_agent(self) -> Agent:
        """Get the agent instance"""
        return self.agent
