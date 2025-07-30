"""Main application file implementing the GitHub webhook server."""
from flask import Flask, request, jsonify
import os
import asyncio
import tempfile
from typing import Dict, Any

from src.config import settings
from src.services.github_service import GitHubService
from src.services.repo_service import RepoService
from src.utils.logging import logger
from src.analyzer.main import IntelligentTestAgent

app = Flask(__name__)
github_service = GitHubService()
repo_service = RepoService()
logger.info("Starting Test Impact Analyzer server...")

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming GitHub webhook events."""
    
    payload = request.json
    
    if payload['action'] not in ['opened', 'synchronize', 'reopened']:
        return jsonify({"status": "ignored"})
        
    # Extract PR information
    pr_number = payload['number']
    base_branch = payload['pull_request']['base']['ref']
    head_branch = payload['pull_request']['head']['ref']
    repo_url = payload['repository']['clone_url']
    repo_name = payload['repository']['name']
    
    # Set up repository path
    repo_path = os.path.join(tempfile.gettempdir(), "repos", repo_name)
    
    # Clone/update the repository
    if not repo_service.clone_or_update_repo(repo_url, repo_path, head_branch):
        return jsonify({
            "status": "error", 
            "message": "Failed to clone/update repository"
        }), 500
    
    try:
        # Initialize and run analysis
        agent = IntelligentTestAgent(repo_path)
        results = asyncio.run(agent.process_pr(base_branch, 'HEAD', format='detailed'))
        
        # Post results as PR comment
        github_service.post_pr_comment(payload['pull_request']['comments_url'], results)
        logger.info(f"Analysis results for PR #{pr_number}: {results}")
        
        return jsonify({
            "status": "success", 
            "results": results
        })
            
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": f"Analysis failed: {str(e)}"
        }), 500

def main():
    """Run the application."""
    port = settings.PORT
    host = settings.HOST
    debug = settings.DEBUG
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
