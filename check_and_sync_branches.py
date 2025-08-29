
#!/usr/bin/env python3
"""
Check and sync all merged branches from GitHub to Replit
Fixes divergent branch issues and ensures all branches are available locally
"""

import subprocess
import sys
import json
import requests
import os
from datetime import datetime

class GitBranchSyncer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_owner = os.getenv('GITHUB_OWNER')
        self.github_repo = os.getenv('GITHUB_REPO')
        
    def run_git_command(self, command, description=""):
        """Run a git command and return the result"""
        try:
            if description:
                print(f"🔄 {description}...")
            
            result = subprocess.run(command, capture_output=True, text=True, shell=False, timeout=60)
            
            if result.returncode == 0:
                if description:
                    print(f"✅ {description} successful")
                return {"status": "success", "output": result.stdout.strip()}
            else:
                if description:
                    print(f"⚠️ {description} warning: {result.stderr}")
                return {"status": "warning", "output": result.stderr.strip()}
                
        except subprocess.TimeoutExpired:
            print(f"❌ {description} timed out")
            return {"status": "timeout", "output": "Command timed out"}
        except Exception as e:
            print(f"❌ {description} failed: {str(e)}")
            return {"status": "error", "output": str(e)}
    
    def fix_divergent_branches(self):
        """Fix divergent branches by configuring git properly"""
        print("🔧 Fixing divergent branches configuration...")
        
        # Set pull strategy to merge
        self.run_git_command(['git', 'config', 'pull.rebase', 'false'], "Setting pull strategy to merge")
        
        # Set push strategy
        self.run_git_command(['git', 'config', 'push.default', 'simple'], "Setting push strategy")
        
        # Configure merge strategy
        self.run_git_command(['git', 'config', 'merge.ours.driver', 'true'], "Setting merge driver")
        
        return True
    
    def get_github_branches(self):
        """Get all branches from GitHub API"""
        if not all([self.github_token, self.github_owner, self.github_repo]):
            print("⚠️ GitHub credentials not configured, using git commands only")
            return []
        
        try:
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            url = f"https://api.github.com/repos/{self.github_owner}/{self.github_repo}/branches"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                branches = response.json()
                return [branch['name'] for branch in branches]
            else:
                print(f"⚠️ GitHub API error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"⚠️ Error fetching GitHub branches: {e}")
            return []
    
    def get_local_branches(self):
        """Get all local branches"""
        result = self.run_git_command(['git', 'branch'], "Getting local branches")
        
        if result["status"] == "success":
            branches = []
            for line in result["output"].split('\n'):
                branch = line.strip().replace('* ', '').strip()
                if branch:
                    branches.append(branch)
            return branches
        return []
    
    def get_remote_branches(self):
        """Get all remote branches"""
        result = self.run_git_command(['git', 'branch', '-r'], "Getting remote branches")
        
        if result["status"] == "success":
            branches = []
            for line in result["output"].split('\n'):
                branch = line.strip()
                if branch and 'origin/' in branch and 'HEAD' not in branch:
                    clean_branch = branch.replace('origin/', '').strip()
                    branches.append(clean_branch)
            return branches
        return []
    
    def force_sync_with_remote(self):
        """Force sync with remote to resolve conflicts"""
        print("🔄 Force syncing with remote to resolve conflicts...")
        
        # Get current branch
        current_branch_result = self.run_git_command(['git', 'branch', '--show-current'], "Getting current branch")
        current_branch = current_branch_result.get("output", "main")
        
        # Fetch all updates
        self.run_git_command(['git', 'fetch', 'origin', '--prune'], "Fetching all updates")
        
        # Reset to remote state to resolve divergent branches
        reset_result = self.run_git_command(['git', 'reset', '--hard', f'origin/{current_branch}'], 
                                          f"Resetting {current_branch} to match remote")
        
        if reset_result["status"] == "success":
            print(f"✅ Successfully synced {current_branch} with remote")
            return True
        else:
            print(f"❌ Failed to sync {current_branch}")
            return False
    
    def create_local_tracking_branch(self, branch_name):
        """Create a local tracking branch for a remote branch"""
        try:
            # Check if local branch already exists
            check_result = self.run_git_command(['git', 'show-ref', '--verify', f'refs/heads/{branch_name}'], 
                                              f"Checking if {branch_name} exists locally")
            
            if check_result["status"] == "success":
                print(f"📍 Branch {branch_name} already exists locally")
                return True
            
            # Create tracking branch
            create_result = self.run_git_command(['git', 'checkout', '-b', branch_name, f'origin/{branch_name}'], 
                                               f"Creating tracking branch {branch_name}")
            
            if create_result["status"] == "success":
                print(f"✅ Created local tracking branch: {branch_name}")
                return True
            else:
                print(f"❌ Failed to create tracking branch: {branch_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating tracking branch {branch_name}: {e}")
            return False
    
    def sync_all_branches(self):
        """Sync all branches from GitHub to Replit"""
        print("🚀 Starting comprehensive branch sync...")
        print("=" * 60)
        
        # Step 1: Fix git configuration
        self.fix_divergent_branches()
        
        # Step 2: Force sync current branch with remote
        if not self.force_sync_with_remote():
            print("❌ Failed to sync current branch, continuing with other branches...")
        
        # Step 3: Get all branch information
        print("\n📋 Gathering branch information...")
        github_branches = self.get_github_branches()
        local_branches = self.get_local_branches()
        remote_branches = self.get_remote_branches()
        
        print(f"🔗 GitHub branches: {len(github_branches)}")
        print(f"📍 Local branches: {len(local_branches)}")
        print(f"🌐 Remote tracking branches: {len(remote_branches)}")
        
        # Step 4: Find missing branches
        missing_branches = []
        for branch in remote_branches:
            if branch not in local_branches:
                missing_branches.append(branch)
        
        print(f"\n🆕 Missing local branches: {len(missing_branches)}")
        
        # Step 5: Create missing local tracking branches
        if missing_branches:
            print("\n🔄 Creating missing local tracking branches...")
            current_branch = self.run_git_command(['git', 'branch', '--show-current'], "Getting current branch").get("output", "main")
            
            success_count = 0
            for branch in missing_branches:
                if self.create_local_tracking_branch(branch):
                    success_count += 1
            
            # Switch back to original branch
            self.run_git_command(['git', 'checkout', current_branch], f"Switching back to {current_branch}")
            
            print(f"✅ Successfully created {success_count}/{len(missing_branches)} local tracking branches")
        else:
            print("✅ All remote branches are already tracked locally")
        
        # Step 6: Final status
        final_local = self.get_local_branches()
        final_remote = self.get_remote_branches()
        
        print("\n" + "=" * 60)
        print("📊 SYNC SUMMARY")
        print("=" * 60)
        print(f"✅ Local branches after sync: {len(final_local)}")
        print(f"🔗 Remote branches available: {len(final_remote)}")
        
        # Show branch details
        print(f"\n📍 Local Branches ({len(final_local)}):")
        for branch in sorted(final_local)[:10]:
            print(f"   • {branch}")
        if len(final_local) > 10:
            print(f"   ... and {len(final_local) - 10} more")
        
        print(f"\n🌐 Remote Branches ({len(final_remote)}):")
        for branch in sorted(final_remote)[:10]:
            print(f"   • {branch}")
        if len(final_remote) > 10:
            print(f"   ... and {len(final_remote) - 10} more")
        
        # Check for any remaining missing branches
        still_missing = [b for b in final_remote if b not in final_local]
        if still_missing:
            print(f"\n⚠️ Still missing branches: {still_missing}")
        else:
            print("\n🎉 All remote branches are now available locally!")
        
        return len(still_missing) == 0

def main():
    print("🔍 Checking and Syncing GitHub Branches to Replit")
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    syncer = GitBranchSyncer()
    
    try:
        success = syncer.sync_all_branches()
        
        if success:
            print("\n🎉 All branches successfully synced!")
            print("💡 Your Replit workspace now has all GitHub branches available")
        else:
            print("\n⚠️ Some branches may still be missing")
            print("💡 Check the output above for details")
            
    except KeyboardInterrupt:
        print("\n🛑 Sync interrupted by user")
    except Exception as e:
        print(f"\n❌ Sync failed with error: {e}")
    
    print(f"\n🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
