"""Test Impact Analyzer core implementation."""
import os
import asyncio
import subprocess
from typing import Dict, List, Any, Optional
from datetime import datetime
import ast
import re

from git import Repo
from crewai import Agent, Task, Crew
from langchain_ollama import OllamaLLM

class TestAnalyzer:
    """Analyzes code to determine which tests should be run."""
    
    def __init__(self, repo_path: str):
        """Initialize analyzer with repository path."""
        self.repo_path = repo_path
        self.repo = Repo(repo_path)

    def get_changed_files(self, base_ref: str, target_ref: str = 'HEAD') -> List[str]:
        """Get list of files changed between two git refs."""
        try:
            diff_index = self.repo.index.diff(base_ref)
            return [item.a_path for item in diff_index]
        except Exception as e:
            print(f"Error getting changed files: {e}")
            return []

    def find_related_tests(self, changed_files: List[str]) -> List[str]:
        """Find test files related to changed files."""
        test_files = []
        
        for changed_file in changed_files:
            # Look for corresponding test file
            file_name = os.path.basename(changed_file)
            name_without_ext = os.path.splitext(file_name)[0]
            
            # Common test file patterns
            patterns = [
                f"test_{name_without_ext}.*",
                f"{name_without_ext}_test.*",
                f"{name_without_ext}.test.*",
                f"{name_without_ext}.spec.*"
            ]
            
            # Search for test files in common test directories
            test_dirs = ['tests', 'test', '__tests__', 'src/test', 'src/tests']
            for test_dir in test_dirs:
                for pattern in patterns:
                    matches = self._find_files_by_pattern(test_dir, pattern)
                    test_files.extend(matches)
        
        return list(set(test_files))  # Remove duplicates

    def _find_files_by_pattern(self, directory: str, pattern: str) -> List[str]:
        """Find files matching pattern in directory."""
        matches = []
        try:
            for root, _, files in os.walk(os.path.join(self.repo_path, directory)):
                for filename in files:
                    if re.match(pattern, filename):
                        matches.append(os.path.join(root, filename))
        except Exception as e:
            print(f"Error searching for test files: {e}")
        return matches

    def analyze_test_impact(self, base_ref: str, target_ref: str = 'HEAD') -> Dict[str, Any]:
        """Analyze which tests should be run based on changes."""
        changed_files = self.get_changed_files(base_ref, target_ref)
        
        if not changed_files:
            return {"status": "no_changes"}
            
        test_files = self.find_related_tests(changed_files)
        
        if not test_files:
            return {"status": "no_tests"}
            
        results = {
            "status": "success",
            "changes": len(changed_files),
            "changed_files": changed_files,
            "impacted_tests": len(test_files),
            "test_files": test_files,
            "results": {
                "test_results": []
            }
        }
        
        # Run identified tests
        for test_file in test_files:
            test_result = self._run_test(test_file)
            results["results"]["test_results"].append(test_result)
            
        return results

    def _run_test(self, test_file: str) -> Dict[str, Any]:
        """Run a test file and return results."""
        ext = os.path.splitext(test_file)[1].lower()
        
        if ext in ['.py']:
            return self._run_python_tests(test_file)
        elif ext in ['.js', '.ts', '.jsx', '.tsx']:
            return self._run_javascript_tests(test_file)
        else:
            return {
                "file": test_file,
                "error": f"Unsupported test file type: {ext}"
            }

    def _run_python_tests(self, test_file: str) -> Dict[str, Any]:
        """Run Python tests."""
        try:
            # Try common Python test runners
            runners = ['pytest', 'python -m unittest']
            for runner in runners:
                try:
                    cmd = runner.split() + [test_file]
                    result = subprocess.run(
                        cmd,
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    return {
                        "file": test_file,
                        "result": {
                            "runner": runner,
                            "exit_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.returncode == 0
                        }
                    }
                except FileNotFoundError:
                    continue
            return {"file": test_file, "error": "No suitable test runner found"}
        except Exception as e:
            return {"file": test_file, "error": str(e)}

    def _run_javascript_tests(self, test_file: str) -> Dict[str, Any]:
        """Run JavaScript/TypeScript tests."""
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
                        "file": test_file,
                        "result": {
                            "runner": runner,
                            "exit_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "success": result.returncode == 0
                        }
                    }
                except FileNotFoundError:
                    continue
            return {"file": test_file, "error": "No suitable test runner found"}
        except Exception as e:
            return {"file": test_file, "error": str(e)}

class TestFormatter:
    """Formats test results in different output formats."""
    
    @staticmethod
    def format_results(results: Dict[str, Any], format: str = 'markdown') -> str:
        """Format results in specified format."""
        if format == 'json':
            return json.dumps(results, indent=2)
        elif format == 'detailed':
            return TestFormatter.format_detailed_results(results)
        else:
            return TestFormatter.format_markdown_results(results)

    @staticmethod
    def format_markdown_results(results: Dict[str, Any]) -> str:
        """Format results as GitHub-friendly markdown."""
        if results.get("status") == "no_changes":
            return "## 🔍 Test Impact Analysis\n\n✅ **No changes detected** - No tests need to be run."
        
        if results.get("status") == "no_tests":
            return "## 🔍 Test Impact Analysis\n\n⚠️ **No test files identified** - Please verify test coverage."
        
        markdown = "## 🔍 Test Impact Analysis\n\n"
        
        # Summary section
        markdown += "### 📊 Summary\n\n"
        markdown += f"| Metric | Count |\n|--------|-------|\n"
        markdown += f"| Changed Files | {results.get('changes', 0)} |\n"
        markdown += f"| Impacted Tests | {results.get('impacted_tests', 0)} |\n"
        
        # Test files section
        if results.get('test_files'):
            markdown += "\n### 📁 Identified Test Files\n\n"
            for i, test_file in enumerate(results.get('test_files', []), 1):
                markdown += f"{i}. `{test_file}`\n"
                
        # Add test results
        test_results = results.get('results', {}).get('test_results', [])
        if test_results:
            markdown += "\n### 🧪 Test Results\n\n"
            markdown += "| Test File | Status | Details |\n|-----------|--------|----------|\n"
            
            for result in test_results:
                file_name = result.get('file', 'Unknown')
                if 'error' in result:
                    status = "❌ Error"
                    details = f"Error: {result['error']}"
                elif 'result' in result:
                    if result['result'].get('success', False):
                        status = "✅ Passed"
                        details = "All tests passed"
                    else:
                        status = "❌ Failed"
                        details = f"Exit code: {result['result'].get('exit_code', 'Unknown')}"
                else:
                    status = "⚠️ Unknown"
                    details = "No result data"
                
                markdown += f"| `{file_name}` | {status} | {details} |\n"
        
        markdown += f"\n---\n*Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        return markdown

    @staticmethod
    def format_detailed_results(results: Dict[str, Any]) -> str:
        """Format detailed results with expandable sections."""
        markdown = TestFormatter.format_markdown_results(results)
        
        test_results = results.get('results', {}).get('test_results', [])
        if test_results:
            markdown += "\n\n### 📋 Detailed Test Output\n\n"
            
            for result in test_results:
                file_name = result.get('file', 'Unknown')
                markdown += f"<details>\n<summary>📄 {file_name}</summary>\n\n"
                
                if 'error' in result:
                    markdown += f"**Error:** {result['error']}\n"
                elif 'result' in result:
                    test_result = result['result']
                    if test_result.get('stdout'):
                        markdown += "**Standard Output:**\n```\n"
                        markdown += test_result['stdout'][:1000]
                        if len(test_result['stdout']) > 1000:
                            markdown += "\n... (truncated)"
                        markdown += "\n```\n\n"
                        
                    if test_result.get('stderr'):
                        markdown += "**Standard Error:**\n```\n"
                        markdown += test_result['stderr'][:1000]
                        if len(test_result['stderr']) > 1000:
                            markdown += "\n... (truncated)"
                        markdown += "\n```\n"
                        
                markdown += "\n</details>\n"
                
        return markdown

class IntelligentTestAgent:
    """Main agent class that orchestrates the test impact analysis."""
    
    def __init__(self, repo_path: str):
        """Initialize the agent with repository path."""
        self.repo_path = repo_path
        self.analyzer = TestAnalyzer(repo_path)

    async def process_pr(
        self, 
        base_branch: str, 
        target_branch: str = 'HEAD',
        format: str = 'markdown'
    ) -> str:
        """Process a pull request and analyze test impact."""
        try:
            # Analyze changes
            results = self.analyzer.analyze_test_impact(base_branch, target_branch)
            
            # Format results
            return TestFormatter.format_results(results, format)
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            return TestFormatter.format_results(error_result, format)
