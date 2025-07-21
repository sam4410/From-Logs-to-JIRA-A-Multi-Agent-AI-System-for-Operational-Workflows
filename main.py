import os
from dotenv import load_dotenv
from datetime import datetime
from agents.orchestrator_agent import OpsAnalysisOrchestrator
from config.config import Config

# Load environment variables
load_dotenv()

def setup_sample_data():
    """Create sample data files for testing"""
    from tools.log_tools import create_sample_logs
    from tools.code_tools import create_sample_code
    from tools.db_tools import create_sample_database
    from tools.incident_tools import create_sample_incidents
    
    # Create directories
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/codebase", exist_ok=True)
    
    # Create sample data files
    create_sample_logs()
    create_sample_code()
    create_sample_database()
    create_sample_incidents()
    
    print("✅ Sample data created successfully!")

def create_extended_sample_data():
    """Create additional sample data for more comprehensive testing"""
    from tools.log_tools import create_performance_logs, create_security_logs
    from tools.code_tools import create_additional_code_samples
    from tools.db_tools import create_extended_metrics
    from tools.incident_tools import create_more_incidents
    
    create_performance_logs()
    create_security_logs()
    create_additional_code_samples()
    create_extended_metrics()
    create_more_incidents()
    
    print("✅ Extended sample data created!")

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
    
    orchestrator = OpsAnalysisOrchestrator()
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*60}")
        print(f"TEST SCENARIO {i}: {scenario['description']}")
        print(f"{'='*60}")
        
        try:
            result = orchestrator.execute_analysis(scenario['query'])
            print(f"✅ Scenario {i} completed successfully")
        except Exception as e:
            print(f"❌ Scenario {i} failed: {e}")
        
        # Add delay between tests
        import time
        time.sleep(2)

def main():
    """Main execution function"""
    print("🚀 Multi-Agent Operational Intelligence System")
    print("=" * 50)
    
    # Setup sample data
    print("\n📁 Setting up comprehensive sample data...")
    setup_sample_data()
    create_extended_sample_data()
    
    # Initialize the orchestrator
    orchestrator = OpsAnalysisOrchestrator()
    
    # Run different test scenarios
    print("\n🧪 Running test scenarios...")
    
    # Scenario 1: Basic failure analysis
    print("\n" + "="*60)
    print("SCENARIO 1: Basic Task Failure Analysis")
    print("="*60)
    result1 = orchestrator.execute_analysis("Why is task TID-12345 failing?")
    
    # Scenario 2: Performance issue
    print("\n" + "="*60) 
    print("SCENARIO 2: Performance Issue Investigation")
    print("="*60)
    result2 = orchestrator.execute_analysis("Task TID-12346 is running very slowly, can you investigate performance issues?")
    
    # Interactive mode information
    print("\n🎮 Interactive Mode Available")
    print("You can now run custom queries by calling:")
    print("orchestrator.execute_analysis('Your custom query here')")
    print("\nExample queries:")
    print("- 'Investigate memory issues with TID-12348'")
    print("- 'Why are tasks timing out for TID-12349?'")
    print("- 'Security alert for task TID-12350, need analysis'")
    
    return orchestrator

if __name__ == "__main__":
    orchestrator = main()
    
    # Uncomment the following line to run all test scenarios
    # test_different_scenarios()
