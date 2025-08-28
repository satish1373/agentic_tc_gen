
import os
import subprocess
import hmac
import hashlib
from flask import Flask, request, jsonify
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubSyncHandler:
    """Handle GitHub webhook events and sync with Replit"""
    
    def __init__(self):
        self.github_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
        self.auto_deploy = os.getenv('AUTO_DEPLOY_ON_PUSH', 'true').lower() == 'true'
        self.target_branch = os.getenv('TARGET_BRANCH', 'main')
        
    def verify_signature(self, payload_body, signature_header):
        """Verify GitHub webhook signature"""
        if not self.github_secret:
            logger.warning("GitHub webhook secret not configured - skipping verification")
            return True
            
        if not signature_header:
            return False
            
        hash_object = hmac.new(
            self.github_secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        )
        expected_signature = "sha256=" + hash_object.hexdigest()
        
        return hmac.compare_digest(expected_signature, signature_header)
    
    def pull_latest_changes(self):
        """Pull latest changes from GitHub"""
        try:
            logger.info("📥 Pulling latest changes from GitHub...")
            
            # Ensure we're on the correct branch
            subprocess.run(['git', 'checkout', self.target_branch], check=True, capture_output=True)
            
            # Pull latest changes
            result = subprocess.run(['git', 'pull', 'origin', self.target_branch], 
                                  check=True, capture_output=True, text=True)
            
            logger.info(f"✅ Git pull successful: {result.stdout}")
            return {"status": "success", "output": result.stdout}
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Git pull failed: {e.stderr}"
            logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def install_dependencies(self):
        """Install/update dependencies if requirements changed"""
        try:
            logger.info("📦 Checking for dependency updates...")
            
            # Check if requirements.txt was modified
            result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'], 
                                  capture_output=True, text=True)
            
            if 'requirements.txt' in result.stdout:
                logger.info("📦 Requirements.txt changed, updating dependencies...")
                subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
                logger.info("✅ Dependencies updated successfully")
                return {"status": "updated", "message": "Dependencies updated"}
            else:
                logger.info("📦 No dependency updates needed")
                return {"status": "skipped", "message": "No dependency changes"}
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Dependency installation failed: {e}"
            logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def restart_application(self):
        """Restart the application after sync"""
        try:
            logger.info("🔄 Restarting application...")
            
            # Kill existing Python processes
            subprocess.run(['pkill', '-f', 'jira_webhook_server.py'], check=False)
            
            # Start the application in background
            subprocess.Popen(['python', 'jira_webhook_server.py'])
            
            logger.info("✅ Application restarted successfully")
            return {"status": "success", "message": "Application restarted"}
            
        except Exception as e:
            error_msg = f"Application restart failed: {e}"
            logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}
    
    def handle_push_event(self, payload):
        """Handle GitHub push event"""
        try:
            repository = payload.get('repository', {}).get('name', 'Unknown')
            branch = payload.get('ref', '').replace('refs/heads/', '')
            commits = payload.get('commits', [])
            
            logger.info(f"📨 Received push to {repository}:{branch} with {len(commits)} commits")
            
            # Only process pushes to target branch
            if branch != self.target_branch:
                logger.info(f"⏭️ Ignoring push to {branch} (target: {self.target_branch})")
                return {"status": "ignored", "reason": f"Not target branch ({self.target_branch})"}
            
            # Execute sync workflow
            results = {
                "repository": repository,
                "branch": branch,
                "commits_count": len(commits),
                "steps": {}
            }
            
            # Step 1: Pull changes
            pull_result = self.pull_latest_changes()
            results["steps"]["pull"] = pull_result
            
            if pull_result["status"] == "error":
                return results
            
            # Step 2: Update dependencies
            deps_result = self.install_dependencies()
            results["steps"]["dependencies"] = deps_result
            
            # Step 3: Restart application
            if self.auto_deploy:
                restart_result = self.restart_application()
                results["steps"]["restart"] = restart_result
            else:
                results["steps"]["restart"] = {"status": "skipped", "message": "Auto-deploy disabled"}
            
            logger.info("🎉 GitHub sync completed successfully")
            return results
            
        except Exception as e:
            error_msg = f"Error handling push event: {e}"
            logger.error(f"❌ {error_msg}")
            return {"status": "error", "error": error_msg}

# Initialize sync handler
sync_handler = GitHubSyncHandler()

def create_sync_app():
    """Create Flask app for GitHub sync webhook"""
    app = Flask(__name__)
    
    @app.route('/github-sync', methods=['POST'])
    def handle_github_webhook():
        """Handle GitHub webhook for automatic sync"""
        try:
            # Verify signature
            signature = request.headers.get('X-Hub-Signature-256')
            if not sync_handler.verify_signature(request.data, signature):
                logger.warning("❌ Invalid webhook signature")
                return jsonify({"error": "Invalid signature"}), 401
            
            payload = request.get_json()
            event_type = request.headers.get('X-GitHub-Event')
            
            logger.info(f"📨 Received GitHub event: {event_type}")
            
            if event_type == 'push':
                result = sync_handler.handle_push_event(payload)
                return jsonify({
                    "status": "processed",
                    "event": "push",
                    "result": result
                }), 200
            else:
                logger.info(f"⏭️ Ignoring event type: {event_type}")
                return jsonify({
                    "status": "ignored",
                    "event": event_type,
                    "message": "Event type not processed"
                }), 200
                
        except Exception as e:
            error_msg = f"Error processing GitHub webhook: {e}"
            logger.error(f"❌ {error_msg}")
            return jsonify({"error": error_msg}), 500
    
    @app.route('/sync-status', methods=['GET'])
    def sync_status():
        """Get current sync configuration status"""
        return jsonify({
            "github_secret_configured": bool(sync_handler.github_secret),
            "auto_deploy_enabled": sync_handler.auto_deploy,
            "target_branch": sync_handler.target_branch,
            "webhook_url": f"{os.environ.get('REPL_URL', 'your-repl-url')}/github-sync"
        })
    
    @app.route('/manual-sync', methods=['POST'])
    def manual_sync():
        """Manually trigger sync from GitHub"""
        try:
            logger.info("🔄 Manual sync triggered")
            
            # Pull changes
            pull_result = sync_handler.pull_latest_changes()
            if pull_result["status"] == "error":
                return jsonify(pull_result), 500
            
            # Update dependencies
            deps_result = sync_handler.install_dependencies()
            
            # Restart if requested
            restart_requested = request.json.get('restart', True) if request.json else True
            restart_result = None
            
            if restart_requested:
                restart_result = sync_handler.restart_application()
            
            return jsonify({
                "status": "success",
                "pull": pull_result,
                "dependencies": deps_result,
                "restart": restart_result
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

if __name__ == '__main__':
    app = create_sync_app()
    port = int(os.environ.get('SYNC_PORT', 5001))
    print(f"🔄 Starting GitHub Sync Server on port {port}")
    print(f"🔗 Webhook URL: {os.environ.get('REPL_URL', 'your-repl-url')}/github-sync")
    app.run(host='0.0.0.0', port=port, debug=True)
