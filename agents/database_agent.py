
from crewai import Agent, Task
from langchain_openai import ChatOpenAI
from tools.db_tools import DatabaseMetricsTool

class DatabaseMetricsAgent:
    """Agent specialized in analyzing database metrics and performance data"""
    
    def __init__(self, llm: ChatOpenAI):
        """Initialize the database metrics agent"""
        self.llm = llm
        self.tool = DatabaseMetricsTool()
        self.agent = self._create_agent()
    
    def _create_agent(self) -> Agent:
        """Create the database metrics agent with proper configuration"""
        return Agent(
            role="Database Performance Specialist",
            goal="Analyze database metrics, identify performance bottlenecks, and correlate metrics with system issues",
            backstory="""You are a database expert and performance analyst with 12+ years of experience 
            in database optimization, query tuning, and system performance monitoring. You understand 
            how to interpret system metrics, identify performance bottlenecks, correlate metrics 
            with application issues, and recommend database-level optimizations. You excel at 
            identifying patterns in performance data that indicate systemic problems.""",
            tools=[self.tool],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def create_task(self, user_query: str, task_id: str) -> Task:
        """Create a database metrics analysis task"""
        
        return Task(
            description=f"""
            Retrieve and analyze performance metrics for task {task_id}:
            
            PRIMARY OBJECTIVES:
            1. Query database for all metrics related to {task_id}
            2. Analyze execution timing, duration, and resource utilization patterns
            3. Identify performance anomalies and bottlenecks
            4. Compare current metrics with baseline performance data
            5. Correlate metrics with potential error patterns
            6. Assess resource saturation and capacity issues
            
            ANALYSIS FOCUS:
            - Task execution duration and timing analysis
            - CPU and memory utilization patterns and trends
            - Error count trends, spikes, and correlations
            - Performance degradation indicators over time
            - Resource saturation points and capacity limits
            - Database connection and query performance
            
            CORRELATION ANALYSIS:
            - Cross-reference timing data with log error timestamps
            - Identify performance impact of errors and failures
            - Establish baseline vs actual performance comparisons
            - Detect performance degradation trends
            - Correlate resource usage spikes with system events
            
            PERFORMANCE BENCHMARKING:
            - Compare against historical performance baselines
            - Identify performance regression patterns
            - Calculate performance percentiles and outliers
            - Assess system scalability and capacity issues
            
            DELIVERABLES:
            - Comprehensive performance metrics summary
            - Anomaly detection results with severity assessment
            - Resource utilization analysis with trend identification
            - Performance impact assessment of identified issues
            - Capacity planning recommendations
            - Database optimization suggestions
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agent,
            expected_output="Performance metrics analysis with anomaly detection, correlation findings, and optimization recommendations"
        )
    
    def get_agent(self) -> Agent:
        """Get the agent instance"""
        return self.agent
