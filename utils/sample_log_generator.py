
import os

# Sample data creation functions
def create_sample_logs():
    """Create sample log files for testing"""
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Application log
    app_log_content = f"""2024-01-15 14:30:45 INFO  [main] Application started successfully
2024-01-15 14:31:12 DEBUG [worker-1] Processing task TID-12345
2024-01-15 14:31:15 ERROR [worker-1] NullPointerException in TaskProcessor.process() for TID-12345
2024-01-15 14:31:15 ERROR [worker-1] java.lang.NullPointerException: Cannot invoke method on null object
2024-01-15 14:31:16 WARN  [worker-1] Retrying task TID-12345 (attempt 1/3)
2024-01-15 14:31:45 ERROR [worker-1] Task TID-12345 failed after 3 attempts
2024-01-15 14:32:00 INFO  [worker-2] Processing task TID-12346
2024-01-15 14:32:30 WARN  [worker-2] Slow performance detected for TID-12346: 30s elapsed
2024-01-15 14:33:00 ERROR [db-pool] Connection timeout for TID-12347
2024-01-15 14:33:01 FATAL [system] OutOfMemoryError detected for TID-12348
2024-01-15 14:33:02 ERROR [security] Unauthorized access attempt blocked
2024-01-15 14:34:00 INFO  [main] System health check completed"""
    
    with open(f"{log_dir}/application.log", "w") as f:
        f.write(app_log_content)
    
    # Error log
    error_log_content = f"""2024-01-15 14:31:15 [ERROR] TID-12345 NullPointerException in com.example.TaskProcessor.process(TaskProcessor.java:142)
2024-01-15 14:31:45 [ERROR] TID-12345 Task execution failed: Maximum retry attempts exceeded
2024-01-15 14:33:00 [ERROR] TID-12347 Database connection timeout after 30 seconds
2024-01-15 14:33:01 [FATAL] TID-12348 java.lang.OutOfMemoryError: Java heap space
2024-01-15 14:35:00 [ERROR] TID-12349 Connection refused to external service"""
    
    with open(f"{log_dir}/error.log", "w") as f:
        f.write(error_log_content)

def create_performance_logs():
    """Create performance-specific log files"""
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    perf_log_content = f"""2024-01-15 14:30:00 [PERF] TID-12346 Task execution started
2024-01-15 14:30:05 [PERF] TID-12346 Database query took 5200ms (threshold: 1000ms)
2024-01-15 14:30:10 [PERF] TID-12346 Memory usage: 85% of heap (warning threshold)
2024-01-15 14:30:15 [PERF] TID-12346 CPU usage spike: 95% for 10 seconds
2024-01-15 14:30:30 [PERF] TID-12346 Task completed in 30.2 seconds (SLA: 15 seconds)"""
    
    with open(f"{log_dir}/performance.log", "w") as f:
        f.write(perf_log_content)

def create_security_logs():
    """Create security-specific log files"""
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    security_log_content = f"""2024-01-15 14:32:00 [SECURITY] Authentication failure for user admin
2024-01-15 14:32:05 [SECURITY] Multiple failed login attempts from IP 192.168.1.100
2024-01-15 14:32:10 [SECURITY] TID-12350 Potential SQL injection attempt blocked
2024-01-15 14:32:15 [SECURITY] Unauthorized API access attempt for TID-12350
2024-01-15 14:32:20 [SECURITY] Rate limiting activated for suspicious activity"""
    
    with open(f"{log_dir}/security.log", "w") as f:
        f.write(security_log_content)
