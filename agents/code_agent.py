
from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.code_tools import CodeAnalysisTool
from typing import List

class CodeAnalysisAgent:
    """Agent specialized in analyzing code for bugs and issues"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the code analysis agent"""
        self.llm = llm
        self.tool = CodeAnalysisTool()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the code analysis agent with proper configuration"""
        return Agent(
            role="Senior Code Analysis Expert",
            goal="Analyze code for bugs, security issues, and performance problems that could cause task failures",
            backstory="""You are a principal software engineer with expertise in multiple 
            programming languages and 20+ years of experience in debugging and code analysis. 
            You excel at static code analysis, identifying anti-patterns, security vulnerabilities, 
            performance bottlenecks, and suggesting architectural improvements. You have a keen 
            eye for subtle bugs like null pointer exceptions, resource leaks, and concurrency issues.""",
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def create_task(self, user_query: str, task_id: str, context: List[Task] = None) -> Task:
        """Create a code analysis task based on the user query"""
        
        context_note = ""
        if context:
            context_note = "Use the log analysis results to focus your code review on specific areas mentioned in error messages."
        
        return Task(
            description=f"""
            Analyze codebase for issues related to task {task_id} and log findings:
            
            PRIMARY OBJECTIVES:
            1. Locate code files relevant to {task_id} or error patterns from logs
            2. Perform static code analysis for common bug patterns
            3. Identify potential null pointer exceptions, resource leaks, timeout issues
            4. Review error handling and exception management patterns
            5. Analyze threading and concurrency issues
            6. Suggest specific code improvements and fixes
            
            ANALYSIS FOCUS:
            - Null safety and defensive programming practices
            - Resource management (connections, memory, files, threads)
            - Error handling patterns and exception propagation
            - Performance bottlenecks and inefficient algorithms
            - Security vulnerabilities and input validation
            - Memory leaks and resource cleanup
            - Threading and synchronization issues
            
            CODE REVIEW CHECKLIST:
            - Check for null pointer dereferences
            - Validate resource cleanup in finally blocks
            - Review exception handling completeness
            - Identify performance anti-patterns
            - Look for SQL injection vulnerabilities
            - Check for race conditions and deadlocks
            
            {context_note}
            
            DELIVERABLES:
            - Code issue summary with severity ratings (Critical, High, Medium, Low)
            - Specific file names, line numbers, and problematic code sections
            - Detailed explanation of each identified issue
            - Recommended fixes with code examples where applicable
            - Prevention strategies for similar issues in the future
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agent,
            expected_output="Detailed code analysis report with identified bugs, security issues, performance problems, and specific recommended fixes",
            context=context or []
        )
    
    def get_agent(self) -> Agent:
        """Get the agent instance"""
        return self.agent
