"""Repository service for handling git operations."""
import os
import shutil
import subprocess
from typing import Optional

class RepoService:
    def __init__(self):
        self.temp_path = os.path.join(os.path.expanduser("~"), ".test-impact-analyzer")
        os.makedirs(self.temp_path, exist_ok=True)

    def clone_or_update_repo(self, repo_url: str, repo_path: str, branch: Optional[str] = None) -> bool:
        """Clone repository or update if it already exists.
        
        Args:
            repo_url: The URL of the repository to clone
            repo_path: The path to clone the repository to
            branch: Optional branch to check out
            
        Returns:
            bool: Whether the operation was successful
        """
        try:
            if os.path.exists(repo_path):
                # Repository exists, delete it
                print(f"Deleting existing repository at {repo_path}")
                shutil.rmtree(repo_path)

            # Clone fresh repository
            print(f"Cloning repository {repo_url} to {repo_path}")
            os.makedirs(os.path.dirname(repo_path), exist_ok=True)
            clone_cmd = ['git', 'clone', repo_url, repo_path]
            subprocess.run(clone_cmd, check=True)
            
            if branch:
                switch_cmd = ['git', 'switch', branch]
                branchcheck_cmd = ['git', 'branch']
                subprocess.run(branchcheck_cmd, check=True, cwd=repo_path)
                subprocess.run(switch_cmd, check=True, cwd=repo_path)
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git operation failed: {e}")
            return False
        except Exception as e:
            print(f"Repository operation failed: {e}")
            return False
