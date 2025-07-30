import os
import asyncio
from src.analyzer.main import IntelligentTestAgent, TestAnalyzer
from src.utils.logging import logger

def test_analyzer():
    try:
        # Let's use our own repository for testing
        repo_path = os.getcwd()
        
        # First test basic TestAnalyzer
        print("\nTesting TestAnalyzer...")
        analyzer = TestAnalyzer(repo_path)
        changed_files = analyzer.get_changed_files('HEAD~1')
        print("Changed files:", changed_files)
        
        related_tests = analyzer.find_related_tests(changed_files)
        print("Related test files:", related_tests)
        
        # Then test IntelligentTestAgent
        print("\nTesting IntelligentTestAgent...")
        agent = IntelligentTestAgent(repo_path)
        result = asyncio.run(agent.process_pr(
            base_branch='HEAD~1',  # Compare with previous commit
            target_branch='HEAD'  # Current state
        ))
        print("Test analysis result:", result)
    except Exception as e:
        logger.error(f"Error testing analyzer: {e}")
        logger.error(f"Exception details:", exc_info=True)

if __name__ == '__main__':
    test_analyzer()
