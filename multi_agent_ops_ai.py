# ==============================================================================
# main.py - Entry point for the multi-agent system
# ==============================================================================

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from langchain_openai import ChatOpenAI
import sqlite3
import pandas as pd
import re
from typing import Dict, List, Any
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# ==============================================================================
# CUSTOM TOOLS
# ==============================================================================

class LogAnalysisTool(BaseTool):
    name: str = "log_analysis_tool"
    description: str = "Analyzes log files for errors and issues related to a specific task ID"
    
    def _run(self, task_id: str) -> str:
        """Analyze logs for specific task ID"""
        log_dir = "data/logs"
        matching_lines = []
        
        if not os.path.exists(log_dir):
            return f"Log directory not found: {log_dir}"
        
        for filename in os.listdir(log_dir):
            if filename.endswith(".log"):
                try:
                    with open(os.path.join(log_dir, filename), "r") as file:
                        for line_num, line in enumerate(file, 1):
                            if task_id in line:
                                matching_lines.append(f"{filename}:{line_num}: {line.strip()}")
                except Exception as e:
                    continue
        
        if not matching_lines:
            return f"No log entries found for task {task_id}"
        
        # Classify errors
        error_keywords = ["exception", "traceback", "fail", "error", "timeout", "null"]
        critical_issues = []
        
        for line in matching_lines:
            line_lower = line.lower()
            for keyword in error_keywords:
                if keyword in line_lower:
                    critical_issues.append(f"🔴 CRITICAL: {line}")
                    break
            else:
                critical_issues.append(f"ℹ️  INFO: {line}")
        
        return "\n".join(critical_issues)

class CodeAnalysisTool(BaseTool):
    name: str = "code_analysis_tool"
    description: str = "Analyzes code snippets related to errors and task failures"
    
    def _run(self, task_id: str, error_context: str = "") -> str:
        """Analyze code for potential issues"""
        codebase_dir = "data/codebase"
        if not os.path.exists(codebase_dir):
            return f"Codebase directory not found: {codebase_dir}"
        
        relevant_files = []
        error_terms = error_context.lower().split() if error_context else []
        
        for filename in os.listdir(codebase_dir):
            if filename.endswith((".py", ".java", ".js", ".go")):
                try:
                    with open(os.path.join(codebase_dir, filename), "r") as f:
                        content = f.read()
                        if task_id in content or any(term in content.lower() for term in error_terms):
                            relevant_files.append({
                                "filename": filename,
                                "content": content[:800],  # First 800 chars
                                "lines": len(content.split('\n'))
                            })
                except Exception:
                    continue
        
        if not relevant_files:
            return "No relevant code files found"
        
        analysis = [f"Found {len(relevant_files)} relevant code files:"]
        for file_info in relevant_files:
            analysis.append(f"\n📁 {file_info['filename']} ({file_info['lines']} lines)")
            analysis.append(f"Preview:\n```\n{file_info['content']}\n```")
        
        return "\n".join(analysis)

class DatabaseMetricsTool(BaseTool):
    name: str = "database_metrics_tool"
    description: str = "Queries database for task performance metrics and timing data"
    
    def _run(self, task_id: str) -> str:
        """Fetch task metrics from database"""
        db_path = "data/metrics.db"
        if not os.path.exists(db_path):
            return f"Database not found: {db_path}"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT task_id, start_time, end_time, duration_seconds, 
                       status, cpu_usage, memory_usage, error_count
                FROM task_metrics 
                WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return f"No metrics found for task {task_id}"
            
            return f"""
📊 Task Metrics for {row[0]}:
⏱️  Duration: {row[3]} seconds
📅 Start: {row[1]}
📅 End: {row[2]}
🚦 Status: {row[4]}
💻 CPU Usage: {row[5]}%
🧠 Memory Usage: {row[6]}MB
❌ Error Count: {row[7]}
"""
        except Exception as e:
            return f"Database query failed: {str(e)}"

class IncidentHistoryTool(BaseTool):
    name: str = "incident_history_tool"
    description: str = "Searches historical incidents for similar issues"
    
    def _run(self, task_id: str, error_summary: str = "") -> str:
        """Search incident history"""
        incidents_path = "data/incidents.csv"
        if not os.path.exists(incidents_path):
            return f"Incidents file not found: {incidents_path}"
        
        try:
            df = pd.read_csv(incidents_path)
            
            # First try exact task ID match
            exact_match = df[df['description'].str.contains(task_id, case=False, na=False)]
            
            # Then try error context match
            context_match = pd.DataFrame()
            if error_summary and len(error_summary) > 10:
                keywords = error_summary.lower().split()[:5]  # Top 5 keywords
                for keyword in keywords:
                    if len(keyword) > 3:  # Skip short words
                        matches = df[df['description'].str.contains(keyword, case=False, na=False)]
                        context_match = pd.concat([context_match, matches]).drop_duplicates()
            
            all_matches = pd.concat([exact_match, context_match]).drop_duplicates()
            
            if all_matches.empty:
                return f"No similar incidents found for task {task_id}"
            
            results = [f"Found {len(all_matches)} similar incidents:"]
            for _, row in all_matches.head(5).iterrows():  # Limit to top 5
                results.append(f"\n📅 {row['date']} | Severity: {row['severity']}")
                results.append(f"📋 {row['description'][:150]}...")
                if pd.notna(row['resolution']):
                    results.append(f"✅ Resolution: {row['resolution'][:100]}...")
            
            return "\n".join(results)
        except Exception as e:
            return f"Incident search failed: {str(e)}"

class JiraTicketTool(BaseTool):
    name: str = "jira_ticket_tool"
    description: str = "Creates a JIRA ticket with all gathered information"
    
    def _run(self, task_id: str, summary: str, details: str) -> str:
        """Create JIRA ticket"""
        ticket_id = f"OPS-{datetime.now().strftime('%Y%m%d')}-{task_id.replace('TID-', '')}"
        
        ticket = f"""
🎫 JIRA TICKET CREATED
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ticket ID: {ticket_id}
Task: {task_id}
Priority: HIGH
Assignee: DevOps Team
Labels: ops-ai, auto-generated, {task_id.lower()}

📋 SUMMARY:
{summary[:200]}...

📝 DETAILED ANALYSIS:
{details[:1000]}...

🚀 NEXT STEPS:
1. Review log analysis findings
2. Examine identified code issues  
3. Check performance metrics
4. Reference similar incident resolutions
5. Implement fix and monitor

Status: OPEN
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return ticket

# ==============================================================================
# AGENTS DEFINITION
# ==============================================================================

# Log Analysis Agent
log_agent = Agent(
    role="Log Analysis Specialist",
    goal="Extract and analyze error patterns from system logs to identify root causes of task failures",
    backstory="""You are an expert in log analysis with years of experience in 
    identifying patterns in system logs. You can quickly spot errors, exceptions, 
    and anomalies that indicate system issues.""",
    tools=[LogAnalysisTool()],
    llm=llm,
    verbose=True
)

# Code Analysis Agent  
code_agent = Agent(
    role="Code Analysis Expert",
    goal="Analyze code snippets and identify potential issues that could cause task failures",
    backstory="""You are a senior software engineer with expertise in debugging 
    and code analysis. You can identify problematic code patterns, potential 
    bugs, and suggest improvements.""",
    tools=[CodeAnalysisTool()],
    llm=llm,
    verbose=True
)

# Database Metrics Agent
db_agent = Agent(
    role="Performance Metrics Analyst",
    goal="Retrieve and analyze task performance metrics from databases",
    backstory="""You are a database expert and performance analyst. You understand 
    how to interpret system metrics, identify performance bottlenecks, and correlate 
    metrics with system issues.""",
    tools=[DatabaseMetricsTool()],
    llm=llm,
    verbose=True
)

# Incident History Agent
incident_agent = Agent(
    role="Incident Management Specialist", 
    goal="Search historical incidents to find similar issues and their resolutions",
    backstory="""You are an incident management expert with deep knowledge of 
    historical system issues. You can identify patterns and suggest solutions 
    based on past incidents.""",
    tools=[IncidentHistoryTool()],
    llm=llm,
    verbose=True
)

# JIRA Agent
jira_agent = Agent(
    role="Ticket Management Coordinator",
    goal="Create comprehensive JIRA tickets with all analysis findings",
    backstory="""You are a project management expert skilled in creating detailed, 
    actionable tickets that help development teams resolve issues efficiently.""",
    tools=[JiraTicketTool()],
    llm=llm,
    verbose=True
)

# ==============================================================================
# TASKS DEFINITION
# ==============================================================================

def create_tasks(user_query: str):
    """Create tasks based on user query"""
    
    # Extract task ID from query
    task_id_match = re.search(r"TID[-_]?\d+", user_query)
    task_id = task_id_match.group(0) if task_id_match else "UNKNOWN"
    
    log_task = Task(
        description=f"""
        Analyze system logs for task {task_id} to identify errors, exceptions, 
        and failure patterns. Focus on:
        1. Finding all log entries related to {task_id}
        2. Classifying error types and severity
        3. Extracting key error messages and stack traces
        4. Summarizing the timeline of events
        
        Query: {user_query}
        Task ID: {task_id}
        """,
        agent=log_agent,
        expected_output="Detailed log analysis with error classification and timeline"
    )
    
    code_task = Task(
        description=f"""
        Analyze code related to task {task_id} and any errors found in logs.
        Focus on:
        1. Finding code files related to the task
        2. Identifying potential bugs or issues
        3. Suggesting possible root causes
        4. Recommending code improvements
        
        Use the log analysis results to guide your code investigation.
        """,
        agent=code_agent,
        expected_output="Code analysis with identified issues and recommendations",
        context=[log_task]
    )
    
    db_task = Task(
        description=f"""
        Retrieve performance metrics for task {task_id} from the database.
        Focus on:
        1. Task execution timing and duration
        2. Resource utilization (CPU, memory)  
        3. Error counts and status
        4. Performance trends and anomalies
        """,
        agent=db_agent,
        expected_output="Performance metrics analysis with key findings"
    )
    
    incident_task = Task(
        description=f"""
        Search historical incidents for similar issues to task {task_id}.
        Focus on:
        1. Finding incidents with similar error patterns
        2. Identifying previous resolutions
        3. Extracting lessons learned
        4. Suggesting preventive measures
        
        Use insights from log and code analysis to improve search relevance.
        """,
        agent=incident_agent,
        expected_output="Historical incident analysis with resolution suggestions",
        context=[log_task, code_task]
    )
    
    jira_task = Task(
        description=f"""
        Create a comprehensive JIRA ticket for task {task_id} issue.
        Include:
        1. Clear problem summary
        2. All analysis findings (logs, code, metrics, incidents)
        3. Recommended next steps
        4. Priority and severity assessment
        
        Synthesize all previous analysis into an actionable ticket.
        """,
        agent=jira_agent,
        expected_output="Complete JIRA ticket with all analysis findings",
        context=[log_task, code_task, db_task, incident_task]
    )
    
    return [log_task, code_task, db_task, incident_task, jira_task]

# ==============================================================================
# MAIN EXECUTION FUNCTION
# ==============================================================================

def run_ops_analysis(user_query: str):
    """Run the complete operational analysis"""
    print(f"\n🤖 Multi-Agent Ops AI System")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📥 Query: {user_query}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create tasks
    tasks = create_tasks(user_query)
    
    # Create crew
    crew = Crew(
        agents=[log_agent, code_agent, db_agent, incident_agent, jira_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    # Execute analysis
    print(f"\n🚀 Starting analysis...")
    result = crew.kickoff()
    
    print(f"\n✅ Analysis Complete!")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(result)
    
    return result

# ==============================================================================
# SAMPLE DATA CREATION FUNCTIONS
# ==============================================================================

def setup_sample_data():
    """Create sample data files for testing"""
    
    # Create directories
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/codebase", exist_ok=True)
    
    # Create sample log files
    create_sample_logs()
    create_sample_code()
    create_sample_database()
    create_sample_incidents()
    
    print("✅ Sample data created successfully!")

def create_sample_logs():
    """Create sample log files"""
    log1_content = """2024-07-20 10:15:23 INFO [TaskProcessor] Starting task TID-12345
2024-07-20 10:15:24 INFO [TaskProcessor] Initializing data sources for TID-12345
2024-07-20 10:15:25 ERROR [DatabaseConnector] Connection timeout to primary database
2024-07-20 10:15:26 WARN [TaskProcessor] Retrying database connection for TID-12345
2024-07-20 10:15:28 ERROR [TaskProcessor] NullPointerException in data processing for TID-12345
2024-07-20 10:15:28 ERROR [TaskProcessor] java.lang.NullPointerException: Cannot read property of null
2024-07-20 10:15:29 ERROR [TaskProcessor] Task TID-12345 failed with exception
2024-07-20 10:15:30 INFO [TaskProcessor] Starting task TID-12346
2024-07-20 10:16:45 INFO [TaskProcessor] Task TID-12346 completed successfully
"""
    
    with open("data/logs/application.log", "w") as f:
        f.write(log1_content)
    
    log2_content = """2024-07-20 09:30:15 INFO [SystemMonitor] System health check passed
2024-07-20 10:15:20 WARN [MemoryManager] High memory usage detected: 85%
2024-07-20 10:15:23 INFO [TaskQueue] Task TID-12345 added to processing queue
2024-07-20 10:15:28 ERROR [ExceptionHandler] Uncaught exception in task TID-12345
2024-07-20 10:15:29 ERROR [TaskManager] Task execution failed: TID-12345
2024-07-20 10:30:00 INFO [SystemMonitor] Memory usage normalized: 45%
"""
    
    with open("data/logs/system.log", "w") as f:
        f.write(log2_content)

def create_sample_code():
    """Create sample code files"""
    
    python_code = """# data_processor.py
import json
from typing import Optional, Dict, Any

class DataProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
    
    def process_task(self, task_id: str) -> Optional[Dict]:
        '''Process task TID-12345 and similar tasks'''
        try:
            # BUG: Not checking if connection is None
            data = self.connection.fetch_data(task_id)  # NullPointerException source
            
            if not data:
                raise ValueError(f"No data found for task {task_id}")
            
            # Process the data
            result = self._transform_data(data)
            return result
            
        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            raise
    
    def _transform_data(self, data: Dict) -> Dict:
        # TODO: Add null checks here
        return {
            "processed_at": data["timestamp"],
            "result": data["payload"]["result"]  # Potential null reference
        }
    
    def connect_database(self):
        # Simulate database connection with timeout issues
        import time
        time.sleep(5)  # Causes timeout
        self.connection = DatabaseConnection()

class DatabaseConnection:
    def fetch_data(self, task_id: str):
        # Simulate returning None sometimes
        if "12345" in task_id:
            return None  # This causes NullPointerException
        return {"timestamp": "2024-07-20", "payload": {"result": "success"}}
"""
    
    with open("data/codebase/data_processor.py", "w") as f:
        f.write(python_code)
    
    java_code = """// TaskManager.java
public class TaskManager {
    private DatabaseService dbService;
    
    public TaskManager() {
        this.dbService = new DatabaseService();
    }
    
    public TaskResult executeTask(String taskId) {
        // Bug: No null checking for TID-12345 scenarios
        TaskData data = dbService.fetchTaskData(taskId);
        
        if (data == null) {
            // This should throw a proper exception but doesn't
            return processNullData(data);  // NullPointerException here
        }
        
        return processValidData(data);
    }
    
    private TaskResult processNullData(TaskData data) {
        // BUG: Accessing methods on null object
        return new TaskResult(data.getId(), "failed");  // NPE source
    }
    
    private TaskResult processValidData(TaskData data) {
        return new TaskResult(data.getId(), "success");
    }
}
"""
    
    with open("data/codebase/TaskManager.java", "w") as f:
        f.write(java_code)

def create_sample_database():
    """Create sample SQLite database with metrics"""
    
    conn = sqlite3.connect("data/metrics.db")
    cursor = conn.cursor()
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_metrics (
            task_id TEXT PRIMARY KEY,
            start_time TEXT,
            end_time TEXT,
            duration_seconds INTEGER,
            status TEXT,
            cpu_usage REAL,
            memory_usage INTEGER,
            error_count INTEGER
        )
    """)
    
    # Insert sample data
    sample_data = [
        ("TID-12345", "2024-07-20 10:15:23", "2024-07-20 10:15:29", 6, "FAILED", 75.5, 850, 3),
        ("TID-12346", "2024-07-20 10:15:30", "2024-07-20 10:16:45", 75, "SUCCESS", 45.2, 420, 0),
        ("TID-12344", "2024-07-20 09:30:15", "2024-07-20 09:32:20", 125, "SUCCESS", 38.1, 380, 0),
        ("TID-12347", "2024-07-20 11:00:00", "2024-07-20 11:00:05", 5, "FAILED", 82.3, 920, 2)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO task_metrics 
        (task_id, start_time, end_time, duration_seconds, status, cpu_usage, memory_usage, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_data)
    
    conn.commit()
    conn.close()

def create_sample_incidents():
    """Create sample incidents CSV"""
    
    incidents_data = [
        {
            "date": "2024-07-15",
            "incident_id": "INC-001",
            "severity": "HIGH", 
            "description": "Task TID-12300 failed with NullPointerException in data processing module",
            "resolution": "Added null checks in DataProcessor.process_task() method and improved error handling",
            "resolved_by": "DevOps Team"
        },
        {
            "date": "2024-07-10",
            "incident_id": "INC-002",
            "severity": "MEDIUM",
            "description": "Database connection timeouts causing multiple task failures including TID-12301",
            "resolution": "Increased connection timeout from 3s to 10s and added retry logic",
            "resolved_by": "Database Team"
        },
        {
            "date": "2024-07-08", 
            "incident_id": "INC-003",
            "severity": "HIGH",
            "description": "Memory leak in task processing causing system instability and task failures",
            "resolution": "Fixed memory leak in data transformation logic, added memory monitoring",
            "resolved_by": "Backend Team"
        },
        {
            "date": "2024-07-05",
            "incident_id": "INC-004", 
            "severity": "LOW",
            "description": "Intermittent NullPointerException in TaskManager for certain task types",
            "resolution": "Added comprehensive null validation and defensive programming practices",
            "resolved_by": "Development Team"
        }
    ]
    
    df = pd.DataFrame(incidents_data)
    df.to_csv("data/incidents.csv", index=False)

# ==============================================================================
# ADDITIONAL CONFIGURATION FILES
# ==============================================================================

# config/config.py
import os

class Config:
    # LLM Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = "gpt-3.5-turbo"
    LLM_TEMPERATURE = 0.1
    
    # Data Paths
    LOG_DIR = "data/logs"
    CODEBASE_DIR = "data/codebase" 
    METRICS_DB = "data/metrics.db"
    INCIDENTS_CSV = "data/incidents.csv"
    
    # Agent Configuration
    MAX_LOG_LINES = 100
    MAX_CODE_PREVIEW_CHARS = 800
    MAX_INCIDENT_RESULTS = 5
    
    # JIRA Configuration
    JIRA_PROJECT_KEY = "OPS"
    DEFAULT_ASSIGNEE = "DevOps Team"
    
# ==============================================================================
# ADVANCED ANALYSIS UTILITIES  
# ==============================================================================

class AnalysisUtils:
    @staticmethod
    def extract_error_patterns(text: str) -> List[str]:
        """Extract common error patterns from text"""
        patterns = [
            r'Exception in thread.*',
            r'.*Exception:.*',
            r'Error:.*',
            r'FATAL:.*',
            r'.*timeout.*',
            r'.*connection.*failed.*'
        ]
        
        found_patterns = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found_patterns.extend(matches)
        
        return list(set(found_patterns))
    
    @staticmethod
    def calculate_severity(error_count: int, duration: int, cpu_usage: float) -> str:
        """Calculate incident severity based on metrics"""
        if error_count > 5 or cpu_usage > 90:
            return "CRITICAL"
        elif error_count > 2 or cpu_usage > 70 or duration > 300:
            return "HIGH" 
        elif error_count > 0 or cpu_usage > 50:
            return "MEDIUM"
        else:
            return "LOW"
    
    @staticmethod
    def generate_recommendations(analysis_results: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if "nullpointer" in str(analysis_results).lower():
            recommendations.append("🔧 Add null checks and defensive programming practices")
            
        if "timeout" in str(analysis_results).lower():
            recommendations.append("⏱️ Review and increase timeout configurations")
            recommendations.append("🔄 Implement retry mechanisms with exponential backoff")
            
        if "memory" in str(analysis_results).lower():
            recommendations.append("🧠 Investigate memory leaks and optimize memory usage")
            
        if "database" in str(analysis_results).lower():
            recommendations.append("🗄️ Review database connection pool settings")
            recommendations.append("📊 Add database performance monitoring")
            
        return recommendations

# ==============================================================================
# ENHANCED CREW WITH CALLBACKS
# ==============================================================================

class OpsAnalysisCrew:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            api_key=Config.OPENAI_API_KEY
        )
        self.agents = self._create_agents()
        self.analysis_results = {}
    
    def _create_agents(self):
        """Create all agents with enhanced configurations"""
        return {
            'log_agent': Agent(
                role="Senior Log Analysis Specialist",
                goal="Perform deep analysis of system logs to identify root causes and error patterns",
                backstory="""You are a veteran system administrator with 15+ years of experience 
                in log analysis. You can quickly identify critical errors, trace error propagation, 
                and understand system behavior patterns from log data.""",
                tools=[LogAnalysisTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False
            ),
            'code_agent': Agent(
                role="Senior Code Analysis Expert", 
                goal="Analyze code for bugs, security issues, and performance problems",
                backstory="""You are a principal software engineer with expertise in multiple 
                programming languages. You excel at static code analysis, identifying anti-patterns, 
                and suggesting architectural improvements.""",
                tools=[CodeAnalysisTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False
            ),
            'db_agent': Agent(
                role="Database Performance Specialist",
                goal="Analyze database metrics and identify performance bottlenecks", 
                backstory="""You are a database expert with deep knowledge of query optimization, 
                index tuning, and database performance monitoring. You can correlate metrics 
                with application performance issues.""",
                tools=[DatabaseMetricsTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False
            ),
            'incident_agent': Agent(
                role="Incident Management Expert",
                goal="Research historical incidents and provide resolution strategies",
                backstory="""You are a senior SRE with extensive experience in incident response 
                and post-mortem analysis. You excel at finding patterns in historical data 
                and predicting potential issues.""",
                tools=[IncidentHistoryTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False
            ),
            'jira_agent': Agent(
                role="Technical Project Manager",
                goal="Create comprehensive tickets with actionable next steps",
                backstory="""You are an experienced technical project manager who excels at 
                synthesizing complex technical information into clear, actionable tickets 
                that development teams can execute efficiently.""",
                tools=[JiraTicketTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False
            )
        }
    
    def create_enhanced_tasks(self, user_query: str):
        """Create enhanced tasks with better context and dependencies"""
        
        # Extract task ID and classify query type
        task_id_match = re.search(r"TID[-_]?\d+", user_query)
        task_id = task_id_match.group(0) if task_id_match else "UNKNOWN"
        
        query_lower = user_query.lower()
        is_performance_query = any(word in query_lower for word in ['slow', 'latency', 'performance', 'timeout'])
        is_error_query = any(word in query_lower for word in ['fail', 'error', 'exception', 'crash'])
        
        # Task 1: Log Analysis
        log_task = Task(
            description=f"""
            Perform comprehensive log analysis for task {task_id}:
            
            PRIMARY OBJECTIVES:
            1. Search all log files for entries related to {task_id}
            2. Identify and classify all errors, warnings, and exceptions
            3. Create a timeline of events leading to the issue
            4. Extract stack traces and error messages
            5. Determine error severity and impact
            
            ANALYSIS FOCUS:
            - Look for: {', '.join(['exceptions', 'timeouts', 'connection failures', 'null pointer errors'])}
            - Pay special attention to: {"performance issues" if is_performance_query else "error patterns"}
            - Timeline reconstruction from log timestamps
            
            DELIVERABLES:
            - Complete error timeline
            - Error classification and severity
            - Key error messages and stack traces
            - Potential root cause hypotheses
            
            User Query: {user_query}
            Task ID: {task_id}
            """,
            agent=self.agents['log_agent'],
            expected_output="Comprehensive log analysis report with error timeline and classification"
        )
        
        # Task 2: Code Analysis
        code_task = Task(
            description=f"""
            Analyze codebase for issues related to task {task_id} and log findings:
            
            PRIMARY OBJECTIVES:
            1. Locate code files relevant to {task_id} or error patterns from logs
            2. Perform static code analysis for common bug patterns
            3. Identify potential null pointer exceptions, resource leaks, timeout issues
            4. Review error handling and exception management
            5. Suggest code improvements and fixes
            
            ANALYSIS FOCUS:
            - Null safety and defensive programming
            - Resource management (connections, memory, files)
            - Error handling patterns
            - Performance bottlenecks in code
            - Threading and concurrency issues
            
            CONTEXT: Use the log analysis results to focus your code review on specific areas mentioned in error messages.
            
            DELIVERABLES:
            - Code issue summary with severity ratings
            - Specific line numbers and problematic code sections
            - Recommended fixes and improvements
            - Prevention strategies for similar issues
            """,
            agent=self.agents['code_agent'],
            expected_output="Detailed code analysis with identified bugs and recommended fixes",
            context=[log_task]
        )
        
        # Task 3: Database Metrics Analysis
        db_task = Task(
            description=f"""
            Retrieve and analyze performance metrics for task {task_id}:
            
            PRIMARY OBJECTIVES:
            1. Query database for all metrics related to {task_id}
            2. Analyze execution timing and resource utilization
            3. Identify performance anomalies and bottlenecks
            4. Compare with baseline performance metrics
            5. Correlate metrics with error patterns
            
            ANALYSIS FOCUS:
            - Task execution duration and timing
            - CPU and memory utilization patterns  
            - Error count trends and spikes
            - Performance degradation indicators
            - Resource saturation points
            
            CORRELATION ANALYSIS:
            - Cross-reference timing with log error timestamps
            - Identify performance impact of errors
            - Establish baseline vs actual performance
            
            DELIVERABLES:
            - Performance metrics summary
            - Anomaly detection results
            - Resource utilization analysis
            - Performance impact assessment
            """,
            agent=self.agents['db_agent'],
            expected_output="Performance metrics analysis with anomaly detection and correlation findings"
        )
        
        # Task 4: Incident History Research
        incident_task = Task(
            description=f"""
            Research historical incidents similar to current {task_id} issue:
            
            PRIMARY OBJECTIVES:
            1. Search incident database for similar error patterns
            2. Find incidents with matching task types or error signatures  
            3. Extract successful resolution strategies
            4. Identify recurring patterns and systemic issues
            5. Compile lessons learned and preventive measures
            
            SEARCH STRATEGY:
            - Exact task ID matches for direct relevance
            - Error message pattern matching from log analysis
            - Similar symptom pattern recognition
            - Time-based correlation analysis
            
            CONTEXT ANALYSIS:
            Use insights from log analysis and code review to refine search terms and improve relevance of historical incident matches.
            
            DELIVERABLES:
            - List of similar historical incidents
            - Resolution strategies that worked
            - Common root causes for this issue type
            - Preventive measures and monitoring recommendations
            - Escalation patterns and team involvement history
            """,
            agent=self.agents['incident_agent'],
            expected_output="Historical incident analysis with proven resolution strategies and prevention recommendations",
            context=[log_task, code_task]
        )
        
        # Task 5: Comprehensive JIRA Ticket Creation
        jira_task = Task(
            description=f"""
            Create a comprehensive, actionable JIRA ticket for {task_id} issue:
            
            PRIMARY OBJECTIVES:
            1. Synthesize all analysis findings into a clear problem statement
            2. Create actionable next steps with clear ownership
            3. Set appropriate priority and severity levels
            4. Include all supporting evidence and analysis
            5. Provide clear acceptance criteria for resolution
            
            TICKET STRUCTURE:
            - Executive Summary (2-3 sentences)
            - Detailed Problem Description
            - Root Cause Analysis Summary
            - Impact Assessment
            - Recommended Solution Steps
            - Supporting Evidence (logs, code, metrics, incidents)
            - Acceptance Criteria
            - Related Links and References
            
            PRIORITIZATION FACTORS:
            - Error frequency and impact scope
            - Performance degradation severity
            - Historical incident patterns
            - Business impact assessment
            
            CONTEXT INTEGRATION:
            Synthesize findings from all previous analysis tasks (logs, code, database metrics, incident history) into a cohesive narrative that tells the complete story of the issue.
            
            DELIVERABLES:
            - Complete JIRA ticket with all sections filled
            - Priority and severity justification
            - Clear next steps with estimated effort
            - Monitoring and validation criteria
            """,
            agent=self.agents['jira_agent'],
            expected_output="Complete, actionable JIRA ticket with comprehensive analysis synthesis and clear resolution steps",
            context=[log_task, code_task, db_task, incident_task]
        )
        
        return [log_task, code_task, db_task, incident_task, jira_task]
    
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
        
        # Create enhanced tasks
        tasks = self.create_enhanced_tasks(user_query)
        
        # Create crew with sequential process for better context flow
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,  # Enable memory for better context retention
        )
        
        try:
            print(f"\n🚀 Initiating multi-agent analysis...")
            print(f"👥 Agents: {len(self.agents)} specialized agents")
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

# ==============================================================================
# SAMPLE USAGE AND TESTING
# ==============================================================================

def test_different_scenarios():
    """Test the system with different types of operational queries"""
    
    test_scenarios = [
        {
            "query": "Why is task TID-12345 failing?",
            "description": "Basic failure analysis"
        },
        {
            "query": "Task TID-12346 is running very slowly, can you investigate?", 
            "description": "Performance analysis"
        },
        {
            "query": "We're seeing timeouts for TID-12347, need urgent help",
            "description": "Timeout troubleshooting"
        },
        {
            "query": "Memory issues with TID-12348, system becoming unstable",
            "description": "Memory leak investigation"
        }
    ]
    
    crew_system = OpsAnalysisCrew()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"TEST SCENARIO {i}: {scenario['description']}")
        print(f"{'='*60}")
        
        try:
            result = crew_system.execute_analysis(scenario['query'])
            print(f"✅ Scenario {i} completed successfully")
        except Exception as e:
            print(f"❌ Scenario {i} failed: {e}")
        
        # Add delay between tests
        import time
        time.sleep(2)

# ==============================================================================
# ADDITIONAL SAMPLE DATA FILES
# ==============================================================================

def create_extended_sample_data():
    """Create additional sample data for more comprehensive testing"""
    
    # Create more diverse log files
    create_performance_logs()
    create_security_logs() 
    create_additional_code_samples()
    create_extended_metrics()
    create_more_incidents()
    
    print("✅ Extended sample data created!")

def create_performance_logs():
    """Create performance-focused log files"""
    perf_log = """2024-07-20 14:30:00 INFO [PerformanceMonitor] Starting performance monitoring
2024-07-20 14:30:15 WARN [TaskProcessor] Task TID-12346 execution time: 45.2 seconds (threshold: 30s)
2024-07-20 14:30:16 WARN [MemoryManager] Memory usage at 78% for task TID-12346
2024-07-20 14:30:20 INFO [TaskProcessor] Task TID-12346 memory optimization applied
2024-07-20 14:30:25 ERROR [TaskProcessor] Task TID-12346 still exceeding memory threshold: 82%
2024-07-20 14:30:30 CRITICAL [SystemMonitor] Memory usage critical: 95% - Task TID-12346
2024-07-20 14:30:35 INFO [TaskProcessor] Task TID-12346 terminated due to resource constraints
"""
    
    with open("data/logs/performance.log", "w") as f:
        f.write(perf_log)

def create_security_logs():
    """Create security-focused log files"""
    security_log = """2024-07-20 16:45:00 INFO [SecurityMonitor] Security scan initiated
2024-07-20 16:45:15 WARN [AuthManager] Multiple failed login attempts for task TID-12347
2024-07-20 16:45:20 ERROR [SecurityManager] Potential SQL injection attempt in task TID-12347
2024-07-20 16:45:25 CRITICAL [SecurityManager] Task TID-12347 blocked due to security violation
2024-07-20 16:45:30 INFO [AuditLogger] Security incident logged for task TID-12347
"""
    
    with open("data/logs/security.log", "w") as f:
        f.write(security_log)

def create_additional_code_samples():
    """Create additional code samples with different types of issues"""
    
    # Memory leak prone code
    memory_code = """# memory_processor.py
import threading
from typing import List, Dict

class MemoryLeakProcessor:
    def __init__(self):
        self.cache = {}  # This cache never gets cleaned up - memory leak!
        self.active_tasks = []
        self.lock = threading.Lock()
    
    def process_task_batch(self, task_ids: List[str]):
        '''Process multiple tasks - TID-12348 type tasks'''
        for task_id in task_ids:
            # Memory leak: storing large objects without cleanup
            task_data = self.fetch_large_dataset(task_id)
            self.cache[task_id] = task_data  # Never removed!
            
            # Thread leak: creating threads without proper cleanup
            thread = threading.Thread(target=self.process_single_task, args=(task_id,))
            thread.start()  # Never joined or cleaned up!
            
    def process_single_task(self, task_id: str):
        # Simulate processing that takes memory
        large_list = []
        for i in range(1000000):  # Creates large memory footprint
            large_list.append(f"data_item_{i}_{task_id}")
        
        # Simulate work but never clean up large_list
        return len(large_list)
    
    def fetch_large_dataset(self, task_id: str) -> Dict:
        # Simulate fetching large data that stays in memory
        return {f"key_{i}": f"large_data_value_{i}_{task_id}" for i in range(50000)}
"""
    
    with open("data/codebase/memory_processor.py", "w") as f:
        f.write(memory_code)
    
    # Performance bottleneck code
    perf_code = """// PerformanceBottleneck.java
import java.util.*;

public class PerformanceBottleneck {
    private Map<String, Object> dataCache = new HashMap<>();
    
    public void processTaskBatch(List<String> taskIds) {
        // Performance issue: nested loops with database calls
        for (String taskId : taskIds) {
            for (int i = 0; i < 1000; i++) {  // Unnecessary nested loop
                // Performance killer: database call in loop
                Object data = fetchDataFromDatabase(taskId + "_" + i);
                
                // Inefficient: linear search in large collection
                if (findInLargeCollection(data)) {
                    processData(data, taskId);
                }
            }
        }
    }
    
    private Object fetchDataFromDatabase(String key) {
        // Simulate expensive database call
        try {
            Thread.sleep(10);  // 10ms per call = 10 seconds for 1000 calls!
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return "data_" + key;
    }
    
    private boolean findInLargeCollection(Object data) {
        // Inefficient linear search - should use HashMap
        List<Object> largeCollection = Arrays.asList(new Object[10000]);
        return largeCollection.contains(data);  // O(n) operation!
    }
    
    private void processData(Object data, String taskId) {
        // More performance issues: string concatenation in loop
        String result = "";
        for (int i = 0; i < 1000; i++) {
            result += data.toString() + "_" + taskId;  // Creates new string each time!
        }
        dataCache.put(taskId, result);
    }
}
"""
    
    with open("data/codebase/PerformanceBottleneck.java", "w") as f:
        f.write(perf_code)

def create_extended_metrics():
    """Add more metrics data for different scenarios"""
    conn = sqlite3.connect("data/metrics.db")
    cursor = conn.cursor()
    
    additional_data = [
        ("TID-12348", "2024-07-20 14:30:00", "2024-07-20 14:30:35", 35, "FAILED", 95.8, 1920, 1),
        ("TID-12349", "2024-07-20 15:00:00", "2024-07-20 15:02:30", 150, "TIMEOUT", 88.4, 1650, 5),
        ("TID-12350", "2024-07-20 16:45:00", "2024-07-20 16:45:05", 5, "SECURITY_BLOCKED", 15.2, 200, 1),
        ("TID-12351", "2024-07-20 17:00:00", "2024-07-20 17:00:45", 45, "SUCCESS", 42.1, 385, 0)
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO task_metrics 
        (task_id, start_time, end_time, duration_seconds, status, cpu_usage, memory_usage, error_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, additional_data)
    
    conn.commit()
    conn.close()

def create_more_incidents():
    """Add more historical incidents for better pattern matching"""
    additional_incidents = [
        {
            "date": "2024-07-18",
            "incident_id": "INC-005",
            "severity": "CRITICAL",
            "description": "Memory leak in batch processing causing system crashes for tasks TID-12340 to TID-12350",
            "resolution": "Implemented proper memory cleanup and added memory monitoring alerts",
            "resolved_by": "Platform Team"
        },
        {
            "date": "2024-07-12",
            "incident_id": "INC-006", 
            "severity": "HIGH",
            "description": "Performance degradation in task processing due to inefficient database queries affecting TID-12346",
            "resolution": "Optimized database queries and implemented connection pooling",
            "resolved_by": "Database Team"
        },
        {
            "date": "2024-07-16",
            "incident_id": "INC-007",
            "severity": "MEDIUM",
            "description": "Security violations detected in task authentication for TID-12347 and similar tasks",
            "resolution": "Enhanced input validation and implemented additional security checks",
            "resolved_by": "Security Team"
        }
    ]
    
    # Read existing incidents and append new ones
    existing_df = pd.read_csv("data/incidents.csv")
    new_df = pd.DataFrame(additional_incidents)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.to_csv("data/incidents.csv", index=False)

# ==============================================================================
# MAIN EXECUTION WITH ENHANCED FEATURES
# ==============================================================================

if __name__ == "__main__":
    print("🚀 Multi-Agent Operational Intelligence System")
    print("=" * 50)
    
    # Setup sample data
    print("\n📁 Setting up comprehensive sample data...")
    setup_sample_data()
    create_extended_sample_data()
    
    # Initialize the enhanced crew system
    crew_system = OpsAnalysisCrew()
    
    # Run different test scenarios
    print("\n🧪 Running test scenarios...")
    
    # Scenario 1: Basic failure analysis
    print("\n" + "="*60)
    print("SCENARIO 1: Basic Task Failure Analysis")
    print("="*60)
    result1 = crew_system.execute_analysis("Why is task TID-12345 failing?")
    
    # Scenario 2: Performance issue
    print("\n" + "="*60) 
    print("SCENARIO 2: Performance Issue Investigation")
    print("="*60)
    result2 = crew_system.execute_analysis("Task TID-12346 is running very slowly, can you investigate performance issues?")
    
    # Interactive mode
    print("\n🎮 Interactive Mode Available")
    print("You can now run custom queries by calling:")
    print("crew_system.execute_analysis('Your custom query here')")
    print("\nExample queries:")
    print("- 'Investigate memory issues with TID-12348'")
    print("- 'Why are tasks timing out for TID-12349?'")
    print("- 'Security alert for task TID-12350, need analysis'")
    
    # Uncomment the following line to run all test scenarios
    # test_different_scenarios()
