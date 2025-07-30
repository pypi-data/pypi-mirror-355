# github_webhook.py
from flask import Flask, request, jsonify
import os
import subprocess
import shutil
import asyncio
from main import IntelligentTestAgent
import tempfile
import requests

app = Flask(__name__)

def clone_or_update_repo(repo_url, repo_path, branch=None):
    """Clone repository or update if it already exists"""
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

def post_pr_comment(payload, results):
    """Post analysis results as a comment on the PR"""
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("GITHUB_TOKEN not set, skipping PR comment.")
        return
    comment_url = payload['pull_request']['comments_url']
    comment_body = {
        "body": f"**Test Impact Analysis Results:**\n```\n{results}\n```"
    }
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(comment_url, json=comment_body, headers=headers)
    if response.status_code == 201:
        print("Posted analysis results as PR comment.")
    else:
        print(f"Failed to post PR comment: {response.status_code} {response.text}")
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.json
    
    if payload['action'] in ['opened', 'synchronize', 'reopened']:
        # Extract PR information
        pr_number = payload['number']
        base_branch = payload['pull_request']['base']['ref']
        head_branch = payload['pull_request']['head']['ref']
        repo_url = payload['repository']['clone_url']
        repo_name = payload['repository']['name']
        
        # Set up repository path
        repo_path = os.path.join(tempfile.gettempdir(), "repos", repo_name)
        
        # Actually clone/update the repository
        if not clone_or_update_repo(repo_url, repo_path, head_branch):
            return jsonify({
                "status": "error", 
                "message": "Failed to clone/update repository"
            }), 500
        
        try:
            # Run analysis
            agent = IntelligentTestAgent(repo_path)
            results = asyncio.run(agent.process_pr(base_branch, 'HEAD', format='detailed'))
            
            # Post results as PR comment (implement GitHub API call)
            post_pr_comment(payload, results)
            print(f"Analysis results for PR #{pr_number}: {results}")
            return jsonify({"status": "success", "results": results})
            
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": f"Analysis failed: {str(e)}"
            }), 500
    
    return jsonify({"status": "ignored"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5043)