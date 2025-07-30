# main.py
import os
import asyncio
from typing import List, Dict, Any
from langchain_ollama import OllamaLLM
from langgraph.graph import Graph, END
from crewai import Agent, Task, Crew
from git import Repo
import json
import subprocess
import ast
import re
from datetime import datetime

class MarkdownFormatter:
    """Utility class for formatting results as GitHub-friendly markdown"""
    
    @staticmethod
    def format_test_results(results: Dict[str, Any]) -> str:
        """Format test results as markdown tables for GitHub comments"""
        
        if results.get("status") == "no_changes":
            return "## 🔍 Test Impact Analysis\n\n✅ **No changes detected** - No tests need to be run."
        
        if results.get("status") == "no_tests":
            return "## 🔍 Test Impact Analysis\n\n⚠️ **No test files identified** - Please verify test coverage."
        
        markdown = "## 🔍 Test Impact Analysis\n\n"
        
        # Summary section
        markdown += "### 📊 Summary\n\n"
        markdown += f"| Metric | Count |\n"
        markdown += f"|--------|-------|\n"
        markdown += f"| Changed Files | {results.get('changes', 0)} |\n"
        markdown += f"| Impacted Tests | {results.get('impacted_tests', 0)} |\n"
        
        # Test files section
        if results.get('test_files'):
            markdown += "\n### 📁 Identified Test Files\n\n"
            for i, test_file in enumerate(results.get('test_files', []), 1):
                markdown += f"{i}. `{test_file}`\n"
        
        # Test results section
        test_results = results.get('results', {}).get('test_results', [])
        if test_results:
            markdown += "\n### 🧪 Test Execution Results\n\n"
            markdown += "| Test File | Status | Details |\n"
            markdown += "|-----------|--------|----------|\n"
            
            for test_result in test_results:
                file_name = test_result.get('file', 'Unknown')
                
                if 'error' in test_result:
                    status = "❌ Error"
                    details = f"Error: {test_result['error']}"
                elif 'result' in test_result:
                    result = test_result['result']
                    if result.get('success', False):
                        status = "✅ Passed"
                        details = "All tests passed"
                    else:
                        status = "❌ Failed"
                        details = f"Exit code: {result.get('exit_code', 'Unknown')}"
                else:
                    status = "⚠️ Unknown"
                    details = "No result data"
                
                markdown += f"| `{file_name}` | {status} | {details} |\n"
        
        # Add execution timestamp
        markdown += f"\n---\n*Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        
        return markdown
    
    @staticmethod
    def format_detailed_results(results: Dict[str, Any]) -> str:
        """Format detailed test results with expandable sections"""
        
        markdown = MarkdownFormatter.format_test_results(results)
        
        # Add detailed results in collapsible sections
        test_results = results.get('results', {}).get('test_results', [])
        if test_results:
            markdown += "\n\n### 📋 Detailed Test Output\n\n"
            
            for test_result in test_results:
                file_name = test_result.get('file', 'Unknown')
                markdown += f"<details>\n<summary>📄 {file_name}</summary>\n\n"
                
                if 'error' in test_result:
                    markdown += f"**Error:** {test_result['error']}\n"
                elif 'result' in test_result:
                    result = test_result['result']
                    
                    if result.get('stdout'):
                        markdown += "**Standard Output:**\n```\n"
                        markdown += result['stdout'][:1000]  # Limit output length
                        if len(result['stdout']) > 1000:
                            markdown += "\n... (truncated)"
                        markdown += "\n```\n\n"
                    
                    if result.get('stderr'):
                        markdown += "**Standard Error:**\n```\n"
                        markdown += result['stderr'][:1000]  # Limit output length
                        if len(result['stderr']) > 1000:
                            markdown += "\n... (truncated)"
                        markdown += "\n```\n\n"
                    
                    markdown += f"**Exit Code:** {result.get('exit_code', 'Unknown')}\n"
                
                markdown += "</details>\n\n"
        
        return markdown

class TestImpactAnalyzer:
    def __init__(self, repo_path: str, ollama_model: str = "qwen2.5-coder:7b"):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.llm = OllamaLLM(model=ollama_model, base_url="http://localhost:11434")
        
    def get_pr_changes(self, base_branch: str = "main", target_branch: str = "HEAD") -> List[Dict]:
        """Extract changed files and their modifications"""
        try:
            # Get diff between branches
            diff = self.repo.git.diff(f"{base_branch}..{target_branch}", name_only=True)
            changed_files = diff.strip().split('\n') if diff.strip() else []
            
            changes = []
            for file_path in changed_files:
                if file_path and os.path.exists(os.path.join(self.repo_path, file_path)):
                    file_diff = self.repo.git.diff(f"{base_branch}..{target_branch}", file_path)
                    changes.append({
                        'file_path': file_path,
                        'diff': file_diff,
                        'file_type': self._get_file_type(file_path)
                    })
            return changes
        except Exception as e:
            print(f"Error getting PR changes: {e}")
            return []
    
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type based on extension"""
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
        return type_map.get(ext, 'unknown')
    
    def analyze_test_impact(self, changes: List[Dict]) -> List[str]:
        """Use LLM to analyze which tests might be impacted"""
        if not changes:
            return []
            
        # Create prompt for LLM analysis
        prompt = self._create_impact_analysis_prompt(changes)
        
        try:
            response = self.llm.invoke(prompt)
            # Parse the response to extract test file paths
            test_files = self._parse_test_files_from_response(response)
            return test_files
        except Exception as e:
            print(f"Error analyzing test impact: {e}")
            return []
    
    def _create_impact_analysis_prompt(self, changes: List[Dict]) -> str:
        """Create a structured prompt for impact analysis"""
        change_summary = ""
        for change in changes:
            change_summary += f"\nFile: {change['file_path']}\n"
            change_summary += f"Type: {change['file_type']}\n"
            change_summary += f"Changes:\n{change['diff'][:500]}...\n"
            change_summary += "---\n"
        
        prompt = f"""You are a code analysis expert. Analyze the following code changes and identify which test files might be impacted.

Code Changes:
{change_summary}

Based on these changes, identify:
1. Direct test files that test the modified functions/classes
2. Integration tests that might be affected
3. Test files that import or depend on the changed modules

Rules:
- Look for test files typically in directories like: tests/, test/, spec/, __tests__/
- Common test file patterns: test_*.py, *_test.py, *.test.js, *.spec.js, *.test.ts, *.spec.ts
- Consider import statements and dependencies
- Include both unit tests and integration tests

Return your response as a JSON list of test file paths:
["path/to/test1.py", "path/to/test2.py"]

Response:"""
        return prompt
    
    def _parse_test_files_from_response(self, response: str) -> List[str]:
        """Parse test file paths from LLM response"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                test_files = json.loads(json_match.group())
                # Filter to only existing files
                existing_files = []
                for file_path in test_files:
                    full_path = os.path.join(self.repo_path, file_path)
                    if os.path.exists(full_path):
                        existing_files.append(file_path)
                return existing_files
        except Exception as e:
            print(f"Error parsing test files: {e}")
        
        # Fallback: find all test files in the repository
        return self._find_all_test_files()
    
    def _find_all_test_files(self) -> List[str]:
        """Fallback method to find all test files"""
        test_files = []
        test_patterns = [
            'test_*.py', '*_test.py', 'test*.py',
            '*.test.js', '*.spec.js', 'test*.js',
            '*.test.ts', '*.spec.ts', 'test*.ts'
        ]
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip hidden directories and common non-test directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__']]
            
            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                if any(file.startswith('test') or file.endswith(pattern.replace('*', '')) 
                       for pattern in test_patterns):
                    test_files.append(file_path)
        
        return test_files
    
    def run_tests(self, test_files: List[str]) -> Dict[str, Any]:
        """Run the identified test files"""
        if not test_files:
            return {"status": "no_tests", "message": "No test files identified"}
        
        results = {"status": "success", "test_results": []}
        
        for test_file in test_files:
            try:
                # Determine test runner based on file extension
                if test_file.endswith('.py'):
                    result = self._run_python_tests(test_file)
                elif test_file.endswith(('.js', '.ts')):
                    result = self._run_javascript_tests(test_file)
                else:
                    continue
                    
                results["test_results"].append({
                    "file": test_file,
                    "result": result
                })
            except Exception as e:
                results["test_results"].append({
                    "file": test_file,
                    "error": str(e)
                })
        
        return results
    
    def _run_python_tests(self, test_file: str) -> Dict[str, Any]:
        """Run Python tests using pytest"""
        try:
            full_path = os.path.join(self.repo_path, test_file)
            result = subprocess.run(
                ['python', '-m', 'pytest', full_path, '-v', '--tb=short'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out"}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_javascript_tests(self, test_file: str) -> Dict[str, Any]:
        """Run JavaScript/TypeScript tests"""
        try:
            # Try common JS test runners
            runners = ['npm test', 'yarn test', 'jest']
            
            for runner in runners:
                try:
                    cmd = runner.split() + [test_file] if runner != 'npm test' else ['npm', 'test', '--', test_file]
                    result = subprocess.run(
                        cmd,
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    return {
                        "runner": runner,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.returncode == 0
                    }
                except FileNotFoundError:
                    continue
            
            return {"error": "No suitable test runner found"}
        except Exception as e:
            return {"error": str(e)}

class IntelligentTestAgent:
    def __init__(self, repo_path: str):
        self.analyzer = TestImpactAnalyzer(repo_path)
        self.setup_crew()
    
    def setup_crew(self):
        """Set up CrewAI agents for different tasks"""
        
        # Code Analysis Agent
        self.code_analyzer = Agent(
            role='Code Analysis Expert',
            goal='Analyze code changes and identify potential test impacts',
            backstory='Expert in code analysis and dependency mapping',
            verbose=True,
            allow_delegation=False,
            llm=self.analyzer.llm
        )
        
        # Test Strategy Agent
        self.test_strategist = Agent(
            role='Test Strategy Expert',
            goal='Determine optimal test execution strategy',
            backstory='Expert in test optimization and execution planning',
            verbose=True,
            allow_delegation=False,
            llm=self.analyzer.llm
        )
        
        # Test Execution Agent
        self.test_executor = Agent(
            role='Test Execution Specialist',
            goal='Execute tests efficiently and report results',
            backstory='Expert in test automation and result analysis',
            verbose=True,
            allow_delegation=False,
            llm=self.analyzer.llm
        )
    
    async def process_pr(self, base_branch: str = "main", target_branch: str = "HEAD", format: str = "markdown") -> Dict[str, Any]:
        """Main workflow to process PR and run impacted tests"""
        
        # Task 1: Analyze changes
        analyze_task = Task(
            description=f"Analyze code changes between {base_branch} and {target_branch}",
            agent=self.code_analyzer,
            expected_output="List of changed files with analysis"
        )
        
        # Task 2: Identify test impact
        impact_task = Task(
            description="Identify which tests should be run based on code changes",
            agent=self.test_strategist,
            expected_output="List of test files to execute"
        )
        
        # Task 3: Execute tests
        execution_task = Task(
            description="Execute identified tests and report results",
            agent=self.test_executor,
            expected_output="Test execution results and summary"
        )
        
        # Create and run crew
        crew = Crew(
            agents=[self.code_analyzer, self.test_strategist, self.test_executor],
            tasks=[analyze_task, impact_task, execution_task],
            verbose=True
        )
        
        # Get PR changes
        changes = self.analyzer.get_pr_changes(base_branch, target_branch)
        
        if not changes:
            return {"status": "no_changes", "message": "No changes detected"}
        
        # Analyze test impact
        impacted_tests = self.analyzer.analyze_test_impact(changes)
        
        # Run tests
        test_results = self.analyzer.run_tests(impacted_tests)
        
        results = {
            "changes": len(changes),
            "impacted_tests": len(impacted_tests),
            "test_files": impacted_tests,
            "results": test_results
        }
        # Format results based on specified format
        if format == 'json':
            return results
        elif format == 'detailed':
            return MarkdownFormatter.format_detailed_results(results)
        else:  # markdown
            return MarkdownFormatter.format_test_results(results)

# CLI Interface
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='AI-powered intelligent test runner')
    parser.add_argument('--repo-path', required=True, help='Path to the repository')
    parser.add_argument('--base-branch', default='main', help='Base branch for comparison')
    parser.add_argument('--target-branch', default='HEAD', help='Target branch for comparison')
    parser.add_argument('--format', choices=['json', 'markdown', 'detailed'], default='markdown', 
                       help='Output format (json, markdown, or detailed)')
    parser.add_argument('--output-file', help='Output file path (optional)')
    
    args = parser.parse_args()
    
    agent = IntelligentTestAgent(args.repo_path)
    results = await agent.process_pr(args.base_branch, args.target_branch)
    
    # Format output based on user preference
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    elif args.format == 'detailed':
        output = MarkdownFormatter.format_detailed_results(results)
    else:  # markdown
        output = MarkdownFormatter.format_test_results(results)
    
    # Output to file or console
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(output)
        print(f"Results written to {args.output_file}")
    else:
        print(output)

if __name__ == "__main__":
    asyncio.run(main())