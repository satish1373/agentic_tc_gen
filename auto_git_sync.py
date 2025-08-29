
#!/usr/bin/env python3
"""
Automatic Git Sync Script for Replit
Syncs with remote repository every minute (push and pull)
"""

import subprocess
import time
import logging
import os
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('git_sync.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AutoGitSync:
    def __init__(self, sync_interval=60, auto_commit=True):
        """
        Initialize auto git sync
        
        Args:
            sync_interval (int): Sync interval in seconds (default: 60 = 1 minute)
            auto_commit (bool): Automatically commit changes before push
        """
        self.sync_interval = sync_interval
        self.auto_commit = auto_commit
        self.running = False
        
        # Git configuration
        self.remote_name = 'origin'
        self.branch_name = self.get_current_branch()
        
        # Configure git to handle divergent branches automatically
        self.configure_git()
        
        logger.info(f"🔄 Auto Git Sync initialized")
        logger.info(f"📋 Branch: {self.branch_name}")
        logger.info(f"⏱️ Sync interval: {sync_interval} seconds")
        logger.info(f"🤖 Auto-commit: {auto_commit}")
    
    def configure_git(self):
        """Configure git settings for automatic sync"""
        try:
            # Set pull strategy to merge (handles divergent branches)
            self.run_git_command(
                ['git', 'config', 'pull.rebase', 'false'],
                "Configuring git pull strategy"
            )
            
            # Set push strategy to simple
            self.run_git_command(
                ['git', 'config', 'push.default', 'simple'],
                "Configuring git push strategy"
            )
            
            logger.info("✅ Git configuration completed")
            
        except Exception as e:
            logger.warning(f"⚠️ Git configuration warning: {str(e)}")
    
    def run_git_command(self, command, description=""):
        """Run a git command and return result"""
        try:
            if description:
                logger.info(f"🔄 {description}...")
            
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                shell=False,
                timeout=30
            )
            
            if result.returncode == 0:
                if description:
                    logger.info(f"✅ {description} successful")
                return {"status": "success", "output": result.stdout.strip()}
            else:
                if description:
                    logger.warning(f"⚠️ {description} warning: {result.stderr}")
                return {"status": "warning", "output": result.stderr.strip()}
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {description} timed out")
            return {"status": "timeout", "output": "Command timed out"}
        except Exception as e:
            logger.error(f"❌ {description} failed: {str(e)}")
            return {"status": "error", "output": str(e)}
    
    def get_current_branch(self):
        """Get current git branch"""
        result = self.run_git_command(
            ['git', 'branch', '--show-current'],
            "Getting current branch"
        )
        return result.get("output", "main")
    
    def check_git_status(self):
        """Check if there are any changes to commit"""
        result = self.run_git_command(
            ['git', 'status', '--porcelain'],
            "Checking git status"
        )
        
        if result["status"] == "success":
            changes = result["output"].strip()
            return len(changes) > 0, changes
        return False, ""
    
    def commit_changes(self):
        """Commit any pending changes"""
        has_changes, changes = self.check_git_status()
        
        if not has_changes:
            logger.info("📋 No changes to commit")
            return {"status": "no_changes", "output": "No changes"}
        
        logger.info(f"📝 Found changes:\n{changes}")
        
        # Add all changes
        add_result = self.run_git_command(
            ['git', 'add', '.'],
            "Adding changes"
        )
        
        if add_result["status"] != "success":
            return add_result
        
        # Commit changes
        commit_message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        commit_result = self.run_git_command(
            ['git', 'commit', '-m', commit_message],
            "Committing changes"
        )
        
        return commit_result
    
    def pull_changes(self):
        """Pull latest changes from remote"""
        # Fetch first
        fetch_result = self.run_git_command(
            ['git', 'fetch', self.remote_name],
            "Fetching from remote"
        )
        
        if fetch_result["status"] == "error":
            return fetch_result
        
        # Check if remote has changes
        result = self.run_git_command(
            ['git', 'rev-list', '--count', f'{self.branch_name}..{self.remote_name}/{self.branch_name}'],
            "Checking for remote changes"
        )
        
        if result["status"] == "success" and result["output"].strip() == "0":
            logger.info("📋 No remote changes to pull")
            return {"status": "no_changes", "output": "No remote changes"}
        
        # Try pull with merge strategy (handles divergent branches)
        pull_result = self.run_git_command(
            ['git', 'pull', '--no-rebase', self.remote_name, self.branch_name],
            "Pulling changes with merge strategy"
        )
        
        # If pull still fails due to divergent branches, reset to remote
        if pull_result["status"] != "success" and "divergent branches" in pull_result.get("output", ""):
            logger.warning("⚠️ Divergent branches detected, resetting to remote state")
            reset_result = self.run_git_command(
                ['git', 'reset', '--hard', f'{self.remote_name}/{self.branch_name}'],
                "Resetting to remote state"
            )
            return reset_result
        
        # Handle merge conflicts
        if "CONFLICT" in pull_result.get("output", ""):
            logger.warning("⚠️ Merge conflicts detected, resetting to remote state")
            reset_result = self.run_git_command(
                ['git', 'reset', '--hard', f'{self.remote_name}/{self.branch_name}'],
                "Resetting to remote state"
            )
            return reset_result
        
        return pull_result
    
    def push_changes(self):
        """Push local changes to remote"""
        # Check if there are commits to push
        result = self.run_git_command(
            ['git', 'rev-list', '--count', f'{self.remote_name}/{self.branch_name}..{self.branch_name}'],
            "Checking for local commits"
        )
        
        if result["status"] == "success" and result["output"].strip() == "0":
            logger.info("📋 No local changes to push")
            return {"status": "no_changes", "output": "No local changes"}
        
        # Push changes
        push_result = self.run_git_command(
            ['git', 'push', self.remote_name, self.branch_name],
            "Pushing changes"
        )
        
        return push_result
    
    def sync_cycle(self):
        """Perform one complete sync cycle"""
        logger.info("🔄 Starting sync cycle...")
        
        sync_results = {
            "timestamp": datetime.now().isoformat(),
            "commit": None,
            "pull": None,
            "push": None,
            "status": "success"
        }
        
        try:
            # Step 1: Commit local changes (if auto_commit enabled)
            if self.auto_commit:
                commit_result = self.commit_changes()
                sync_results["commit"] = commit_result
                
                if commit_result["status"] == "error":
                    logger.error("❌ Commit failed, skipping push")
                    sync_results["status"] = "error"
                    return sync_results
            
            # Step 2: Pull remote changes
            pull_result = self.pull_changes()
            sync_results["pull"] = pull_result
            
            if pull_result["status"] == "error":
                logger.error("❌ Pull failed, skipping push")
                sync_results["status"] = "error"
                return sync_results
            
            # Step 3: Push local changes
            if self.auto_commit:  # Only push if we're auto-committing
                push_result = self.push_changes()
                sync_results["push"] = push_result
                
                if push_result["status"] == "error":
                    logger.error("❌ Push failed")
                    sync_results["status"] = "error"
            
            logger.info("✅ Sync cycle completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Sync cycle failed: {str(e)}")
            sync_results["status"] = "error"
            sync_results["error"] = str(e)
        
        return sync_results
    
    def start_sync(self):
        """Start the automatic sync loop"""
        logger.info(f"🚀 Starting auto git sync every {self.sync_interval} seconds")
        logger.info("Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                self.sync_cycle()
                
                # Wait for next cycle
                logger.info(f"⏱️ Waiting {self.sync_interval} seconds until next sync...")
                time.sleep(self.sync_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Sync stopped by user")
        except Exception as e:
            logger.error(f"❌ Sync loop error: {str(e)}")
        finally:
            self.running = False
            logger.info("🏁 Auto git sync stopped")
    
    def stop_sync(self):
        """Stop the sync loop"""
        logger.info("🛑 Stopping auto git sync...")
        self.running = False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto Git Sync for Replit')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Sync interval in seconds (default: 60)')
    parser.add_argument('--no-auto-commit', action='store_true',
                       help='Disable automatic commits (pull only)')
    parser.add_argument('--test', action='store_true',
                       help='Run one sync cycle and exit')
    
    args = parser.parse_args()
    
    # Create sync instance
    sync = AutoGitSync(
        sync_interval=args.interval,
        auto_commit=not args.no_auto_commit
    )
    
    if args.test:
        logger.info("🧪 Running test sync cycle...")
        result = sync.sync_cycle()
        logger.info(f"🧪 Test result: {result}")
    else:
        sync.start_sync()

if __name__ == "__main__":
    main()
