
import os

class Config:
    """Configuration class containing all system settings"""
    
    # LLM Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    LLM_MODEL = "gpt-4o-mini"
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
    
    # Analysis Configuration
    ERROR_KEYWORDS = ["exception", "traceback", "fail", "error", "timeout", "null"]
    PERFORMANCE_KEYWORDS = ['slow', 'latency', 'performance', 'timeout']
    ERROR_QUERY_KEYWORDS = ['fail', 'error', 'exception', 'crash']
    
    # File Extensions for Code Analysis
    CODE_EXTENSIONS = [".py", ".java", ".js", ".go", ".cpp", ".c", ".rb", ".php"]
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create directories if they don't exist
        for directory in [cls.LOG_DIR, cls.CODEBASE_DIR, os.path.dirname(cls.METRICS_DB)]:
            os.makedirs(directory, exist_ok=True)
        
        return True
