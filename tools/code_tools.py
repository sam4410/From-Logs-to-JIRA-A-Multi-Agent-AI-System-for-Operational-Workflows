
import os
import ast
import re
import glob
from typing import List, Dict, Any, Optional
from crewai_tools import BaseTool

class CodeAnalysisTool(BaseTool):
    """Tool for analyzing code for bugs, security issues, and performance problems"""
    
    name: str = "code_analysis_tool"
    description: str = "Analyzes codebase for bugs, security vulnerabilities, and performance issues"
    
    def _run(self, task_id: str = "", query: str = "", code_directory: str = "data/codebase") -> str:
        """
        Analyze code for issues related to the task
        
        Args:
            task_id: The task ID to focus analysis on
            query: Additional search terms or focus areas
            code_directory: Directory containing code files
            
        Returns:
            Formatted code analysis results
        """
        try:
            code_files = self._find_code_files(code_directory)
            
            if not code_files:
                return "No code files found in the specified directory"
            
            analysis_results = {
                'files_analyzed': len(code_files),
                'issues': [],
                'security_issues': [],
                'performance_issues': [],
                'code_smells': [],
                'task_related_files': []
            }
            
            for file_path in code_files:
                file_analysis = self._analyze_file(file_path, task_id, query)
                analysis_results['issues'].extend(file_analysis['issues'])
                analysis_results['security_issues'].extend(file_analysis['security_issues'])
                analysis_results['performance_issues'].extend(file_analysis['performance_issues'])
                analysis_results['code_smells'].extend(file_analysis['code_smells'])
                
                if file_analysis['task_related']:
                    analysis_results['task_related_files'].append(file_path)
            
            # Generate comprehensive report
            report = self._generate_code_report(task_id, analysis_results)
            
            return report
            
        except Exception as e:
            return f"Error analyzing code: {str(e)}"
    
    def _find_code_files(self, directory: str) -> List[str]:
        """Find all code files in the directory"""
        extensions = ["*.py", "*.java", "*.js", "*.cpp", "*.c", "*.go", "*.rb", "*.php"]
        code_files = []
        
        for ext in extensions:
            code_files.extend(glob.glob(os.path.join(directory, "**", ext), recursive=True))
        
        return code_files
    
    def _analyze_file(self, file_path: str, task_id: str, query: str) -> Dict[str, Any]:
        """Analyze a single code file for issues"""
        analysis = {
            'issues': [],
            'security_issues': [],
            'performance_issues': [],
            'code_smells': [],
            'task_related': False
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Check if file is related to task
            if task_id and task_id.lower() in content.lower():
                analysis['task_related'] = True
            
            # Analyze each line
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for various issue types
                issues = self._check_line_issues(line_stripped, file_path, line_num)
                analysis['issues'].extend(issues['general'])
                analysis['security_issues'].extend(issues['security'])
                analysis['performance_issues'].extend(issues['performance'])
                analysis['code_smells'].extend(issues['code_smells'])
            
            # Additional file-level analysis
            if file_path.endswith('.py'):
                analysis.update(self._analyze_python_file(file_path, content))
            elif file_path.endswith('.java'):
                analysis.update(self._analyze_java_file(file_path, content))
        
        except Exception as e:
            analysis['issues'].append({
                'file': file_path,
                'line': 0,
                'issue': f"Error analyzing file: {str(e)}",
                'severity': 'LOW',
                'type': 'AnalysisError'
            })
        
        return analysis
    
    def _check_line_issues(self, line: str, file_path: str, line_num: int) -> Dict[str, List]:
        """Check a single line for various types of issues"""
        issues = {
            'general': [],
            'security': [],
            'performance': [],
            'code_smells': []
        }
        
        line_lower = line.lower()
        
        # Null pointer issues
        if any(pattern in line for pattern in ['.get(', '.fetch(', '.find(']):
            if 'null' not in line_lower and 'none' not in line_lower:
                issues['general'].append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'Potential null pointer access without null check',
                    'severity': 'HIGH',
                    'type': 'NullPointerRisk',
                    'code': line.strip()
                })
        
        # Resource leaks
        if any(pattern in line_lower for pattern in ['connection(', 'open(', 'stream(']):
            if 'close()' not in line_lower and 'with' not in line_lower:
                issues['general'].append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'Potential resource leak - missing close()',
                    'severity': 'MEDIUM',
                    'type': 'ResourceLeak',
                    'code': line.strip()
                })
        
        # Security issues
        if any(pattern in line_lower for pattern in ['sql', 'query', 'execute']):
            if any(vuln in line_lower for vuln in ['input', 'request', 'param']):
                issues['security'].append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'Potential SQL injection vulnerability',
                    'severity': 'CRITICAL',
                    'type': 'SQLInjection',
                    'code': line.strip()
                })
        
        # Hardcoded credentials
        if any(pattern in line_lower for pattern in ['password', 'apikey', 'secret', 'token']):
            if '=' in line and any(quote in line for quote in ['"', "'"]):
                issues['security'].append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'Potential hardcoded credential',
                    'severity': 'HIGH',
                    'type': 'HardcodedCredential',
                    'code': line.strip()
                })
        
        # Performance issues
        if any(pattern in line_lower for pattern in ['sleep(', 'thread.sleep', 'time.sleep']):
            issues['performance'].append({
                'file': file_path,
                'line': line_num,
                'issue': 'Synchronous sleep may block execution',
                'severity': 'MEDIUM',
                'type': 'PerformanceBlock',
                'code': line.strip()
            })
        
        # Nested loops (simplified detection)
        if line_lower.strip().startswith('for ') and '    for ' in line:
            issues['performance'].append({
                'file': file_path,
                'line': line_num,
                'issue': 'Nested loop detected - potential performance impact',
                'severity': 'MEDIUM',
                'type': 'NestedLoop',
                'code': line.strip()
            })
        
        # Code smells
        if len(line.strip()) > 120:
            issues['code_smells'].append({
                'file': file_path,
                'line': line_num,
                'issue': f'Long line ({len(line)} characters) - consider refactoring',
                'severity': 'LOW',
                'type': 'LongLine',
                'code': line.strip()[:100] + '...'
            })
        
        # TODO comments
        if 'todo' in line_lower or 'fixme' in line_lower:
            issues['code_smells'].append({
                'file': file_path,
                'line': line_num,
                'issue': 'TODO/FIXME comment found',
                'severity': 'LOW',
                'type': 'TodoComment',
                'code': line.strip()
            })
        
        return issues
    
    def _analyze_python_file(self, file_path: str, content: str) -> Dict[str, List]:
        """Specific analysis for Python files"""
        additional_issues = {
            'issues': [],
            'security_issues': [],
            'performance_issues': [],
            'code_smells': []
        }
        
        try:
            # Parse AST for more sophisticated analysis
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for functions with too many parameters
                    if len(node.args.args) > 7:
                        additional_issues['code_smells'].append({
                            'file': file_path,
                            'line': node.lineno,
                            'issue': f'Function {node.name} has {len(node.args.args)} parameters (consider refactoring)',
                            'severity': 'MEDIUM',
                            'type': 'TooManyParameters',
                            'code': f'def {node.name}(...)'
                        })
                
                # Check for bare except clauses
                elif isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        additional_issues['issues'].append({
                            'file': file_path,
                            'line': node.lineno,
                            'issue': 'Bare except clause - should specify exception type',
                            'severity': 'MEDIUM',
                            'type': 'BareExcept',
                            'code': 'except:'
                        })
        
        except SyntaxError as e:
            additional_issues['issues'].append({
                'file': file_path,
                'line': e.lineno or 0,
                'issue': f'Syntax error: {e.msg}',
                'severity': 'CRITICAL',
                'type': 'SyntaxError',
                'code': str(e)
            })
        except Exception:
            pass  # Skip AST analysis if it fails
        
        return additional_issues
    
    def _analyze_java_file(self, file_path: str, content: str) -> Dict[str, List]:
        """Specific analysis for Java files"""
        additional_issues = {
            'issues': [],
            'security_issues': [],
            'performance_issues': [],
            'code_smells': []
        }
        
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Check for potential null pointer exceptions
            if '.get(' in line and 'null' not in line.lower():
                additional_issues['issues'].append({
                    'file': file_path,
                    'line': line_num,
                    'issue': 'Potential NullPointerException in Java code',
                    'severity': 'HIGH',
                    'type': 'JavaNullPointer',
                    'code': line.strip()
                })
            
            # Check for resource management
            if any(pattern in line for pattern in ['new FileInputStream', 'new Connection', 'new Socket']):
                if 'try-with-resources' not in content and 'finally' not in content:
                    additional_issues['issues'].append({
                        'file': file_path,
                        'line': line_num,
                        'issue': 'Resource not managed with try-with-resources',
                        'severity': 'MEDIUM',
                        'type': 'JavaResourceLeak',
                        'code': line.strip()
                    })
        
        return additional_issues
    
    def _generate_code_report(self, task_id: str, analysis_results: Dict) -> str:
        """Generate comprehensive code analysis report"""
        
        total_issues = (len(analysis_results['issues']) + 
                       len(analysis_results['security_issues']) + 
                       len(analysis_results['performance_issues']) + 
                       len(analysis_results['code_smells']))
        
        # Count by severity
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        all_issues = (analysis_results['issues'] + 
                     analysis_results['security_issues'] + 
                     analysis_results['performance_issues'] + 
                     analysis_results['code_smells'])
        
        for issue in all_issues:
            severity = issue.get('severity', 'LOW')
            severity_counts[severity] += 1
        
        report = f"""
========================================
CODE ANALYSIS REPORT - {task_id}
========================================

EXECUTIVE SUMMARY:
- Files analyzed: {analysis_results['files_analyzed']}
- Task-related files: {len(analysis_results['task_related_files'])}
- Total issues found: {total_issues}
- Analysis timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SEVERITY BREAKDOWN:
- CRITICAL: {severity_counts['CRITICAL']} issues
- HIGH: {severity_counts['HIGH']} issues  
- MEDIUM: {severity_counts['MEDIUM']} issues
- LOW: {severity_counts['LOW']} issues

ISSUE CATEGORIES:
- General Issues: {len(analysis_results['issues'])}
- Security Issues: {len(analysis_results['security_issues'])}
- Performance Issues: {len(analysis_results['performance_issues'])}
- Code Smells: {len(analysis_results['code_smells'])}
"""

        # Critical and High severity issues
        critical_high_issues = [issue for issue in all_issues 
                               if issue.get('severity') in ['CRITICAL', 'HIGH']]
        
        if critical_high_issues:
            report += f"""
CRITICAL & HIGH PRIORITY ISSUES:
"""
            for i, issue in enumerate(critical_high_issues[:10], 1):  # Show top 10
                report += f"{i}. [{issue['severity']}] {issue['type']}: {issue['issue']}\n"
                report += f"   File: {issue['file']}, Line: {issue['line']}\n"
                report += f"   Code: {issue.get('code', 'N/A')}\n\n"
