"""GitHub service module for handling GitHub-related operations."""
import os
import requests

class GitHubService:
    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN")
    
    def post_pr_comment(self, comments_url: str, results: str) -> bool:
        """Post analysis results as a comment on the PR.
        
        Args:
            comments_url: The URL to post the comment to
            results: The analysis results to post
            
        Returns:
            bool: Whether the comment was posted successfully
        """
        if not self.github_token:
            print("GITHUB_TOKEN not set, skipping PR comment.")
            return False
            
        comment_body = {
            "body": f"**Test Impact Analysis Results:**\n```\n{results}\n```"
        }
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json"
        }

        response = requests.post(comments_url, json=comment_body, headers=headers)
        if response.status_code == 201:
            print("Posted analysis results as PR comment.")
            return True
        else:
            print(f"Failed to post PR comment: {response.status_code} {response.text}")
            return False
