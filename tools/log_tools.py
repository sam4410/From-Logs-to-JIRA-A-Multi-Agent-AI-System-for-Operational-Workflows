
import os
import json
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from crewai_tools import BaseTool
import re

class LogAnalysisTool(BaseTool):
    """Tool for analyzing system logs and extracting error patterns"""
    
    name: str = "log_analysis_tool"
    description: str = "Analyzes system logs to identify errors, patterns, and create timelines for operational issues"
    
    def _run(self, task_id: str, query: str = "", log_directory: str = "data/logs") -> str:
        """
        Analyze logs for a specific task ID and query
        
        Args:
            task_id: The task ID to search for
            query: Additional search terms
            log_directory: Directory containing log files
            
        Returns:
            Formatted analysis results
        """
        try:
            log_files = self._find_log_files(log_directory)
            
            if not log_files:
                return "No log files found in the specified directory"
            
            # Search for task-related entries
            task_entries = []
            error_entries = []
            timeline = []
            
            for log_file in log_files:
                entries = self._parse_log_file(log_file, task_id, query)
                task_entries.extend(entries['task_related'])
                error_entries.extend(entries['errors'])
                timeline.extend(entries['timeline'])
            
            # Sort timeline chronologically
            timeline.sort(key=lambda x: x['timestamp'])
            
            # Analyze patterns
            error_patterns = self._analyze_error_patterns(error_entries)
            severity_analysis = self._analyze_severity(error_entries)
            
            # Generate report
            report = self._generate_log_report(
                task_id, task_entries, error_entries, 
                timeline, error_patterns, severity_analysis
            )
            
            return report
            
        except Exception as e:
            return f"Error analyzing logs: {str(e)}"
    
    def _find_log_files(self, directory: str) -> List[str]:
        """Find all log files in the directory"""
        patterns = ["*.log", "*.txt", "*.out"]
        log_files = []
        
        for pattern in patterns:
            log_files.extend(glob.glob(os.path.join(directory, pattern)))
            log_files.extend(glob.glob(os.path.join(directory, "*", pattern)))
        
        return log_files
    
    def _parse_log_file(self, file_path: str, task_id: str, query: str) -> Dict[str, List]:
        """Parse a single log file for relevant entries"""
        entries = {
            'task_related': [],
            'errors': [],
            'timeline': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Extract timestamp
                timestamp = self._extract_timestamp(line)
                
                # Check for task ID
                if task_id.lower() in line.lower():
                    entry = {
                        'file': file_path,
                        'line_number': line_num,
                        'content': line,
                        'timestamp': timestamp
                    }
                    entries['task_related'].append(entry)
                    entries['timeline'].append(entry)
                
                # Check for errors
                if self._is_error_line(line):
                    error_entry = {
                        'file': file_path,
                        'line_number': line_num,
                        'content': line,
                        'timestamp': timestamp,
                        'error_type': self._classify_error(line),
                        'severity': self._determine_severity(line)
                    }
                    entries['errors'].append(error_entry)
                    
                    # Add to timeline if related to task
                    if task_id.lower() in line.lower():
                        entries['timeline'].append(error_entry)
                
                # Check for query terms
                if query and query.lower() in line.lower():
                    entry = {
                        'file': file_path,
                        'line_number': line_num,
                        'content': line,
                        'timestamp': timestamp,
                        'match_type': 'query_match'
                    }
                    entries['timeline'].append(entry)
        
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
        
        return entries
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Common timestamp patterns
        patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # 2024-01-15 14:30:45
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',  # 01/15/2024 14:30:45
            r'\w{3} \d{2} \d{2}:\d{2}:\d{2}',        # Jan 15 14:30:45
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        return None
    
    def _is_error_line(self, line: str) -> bool:
        """Check if line contains error indicators"""
        error_keywords = [
            'error', 'exception', 'failed', 'failure', 'timeout',
            'null pointer', 'connection refused', 'out of memory',
            'stack trace', 'fatal', 'critical', 'alert'
        ]
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in error_keywords)
    
    def _classify_error(self, line: str) -> str:
        """Classify the type of error"""
        line_lower = line.lower()
        
        if 'null pointer' in line_lower or 'nullpointerexception' in line_lower:
            return 'NullPointerException'
        elif 'timeout' in line_lower:
            return 'TimeoutError'
        elif 'connection' in line_lower and ('refused' in line_lower or 'failed' in line_lower):
            return 'ConnectionError'
        elif 'memory' in line_lower:
            return 'MemoryError'
        elif 'security' in line_lower or 'unauthorized' in line_lower:
            return 'SecurityError'
        elif 'database' in line_lower or 'sql' in line_lower:
            return 'DatabaseError'
        else:
            return 'GeneralError'
    
    def _determine_severity(self, line: str) -> str:
        """Determine error severity"""
        line_lower = line.lower()
        
        if any(word in line_lower for word in ['fatal', 'critical', 'emergency']):
            return 'CRITICAL'
        elif any(word in line_lower for word in ['error', 'exception', 'failed']):
            return 'HIGH'
        elif any(word in line_lower for word in ['warning', 'warn']):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _analyze_error_patterns(self, error_entries: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in error entries"""
        patterns = {}
        
        # Group by error type
        error_types = {}
        for entry in error_entries:
            error_type = entry.get('error_type', 'Unknown')
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(entry)
        
        patterns['error_distribution'] = {
            k: len(v) for k, v in error_types.items()
        }
        
        # Most common errors
        patterns['most_frequent'] = sorted(
            patterns['error_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # Time-based patterns (simplified)
        patterns['total_errors'] = len(error_entries)
        
        return patterns
    
    def _analyze_severity(self, error_entries: List[Dict]) -> Dict[str, int]:
        """Analyze severity distribution"""
        severity_counts = {}
        for entry in error_entries:
            severity = entry.get('severity', 'UNKNOWN')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def _generate_log_report(self, task_id: str, task_entries: List[Dict], 
                           error_entries: List[Dict], timeline: List[Dict],
                           error_patterns: Dict, severity_analysis: Dict) -> str:
        """Generate comprehensive log analysis report"""
        
        report = f"""
========================================
LOG ANALYSIS REPORT - {task_id}
========================================

EXECUTIVE SUMMARY:
- Task-related entries found: {len(task_entries)}
- Total errors detected: {len(error_entries)}
- Timeline events: {len(timeline)}
- Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SEVERITY BREAKDOWN:
"""
        
        for severity, count in severity_analysis.items():
            report += f"- {severity}: {count} occurrences\n"
        
        report += f"""
ERROR PATTERN ANALYSIS:
Top Error Types:
"""
        
        for error_type, count in error_patterns['most_frequent']:
            report += f"- {error_type}: {count} occurrences\n"
        
        if timeline:
            report += f"""
CRITICAL TIMELINE EVENTS:
"""
            # Show first 10 timeline events
            for i, event in enumerate(timeline[:10]):
                timestamp = event.get('timestamp', 'Unknown time')
                content = event['content'][:100] + '...' if len(event['content']) > 100 else event['content']
                report += f"{i+1}. [{timestamp}] {content}\n"
        
        if error_entries:
            report += f"""
RECENT CRITICAL ERRORS:
"""
            # Show most recent critical errors
            critical_errors = [e for e in error_entries if e.get('severity') == 'CRITICAL'][:5]
            for i, error in enumerate(critical_errors):
                report += f"{i+1}. {error['error_type']}: {error['content'][:100]}...\n"
                report += f"   File: {error['file']}, Line: {error['line_number']}\n"
        
        report += f"""
RECOMMENDATIONS:
- Focus on {error_patterns['most_frequent'][0][0] if error_patterns['most_frequent'] else 'general'} error resolution
- Review timeline around critical error occurrences
- Implement enhanced monitoring for detected error patterns
- Consider code review for areas with high error frequency

========================================
"""
        
        return report
