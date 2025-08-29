
#!/usr/bin/env python3
"""
Script to refresh and sync Git branches from GitHub
Run this when you need to see the latest branches that have been merged
"""

import subprocess
import sys
import json
from datetime import datetime

def run_git_command(command, description=""):
    """Run a git command and return the result"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(command, capture_output=True, text=True, shell=False)
        
        if result.returncode == 0:
            print(f"✅ {description} successful")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return {"status": "success", "output": result.stdout.strip()}
        else:
            print(f"⚠️ {description} had warnings: {result.stderr}")
            return {"status": "warning", "output": result.stderr.strip()}
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return {"status": "error", "output": str(e)}

def refresh_branches():
    """Refresh all branches from GitHub"""
    
    print("🚀 Refreshing Git Branches from GitHub")
    print("=" * 50)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check if we're in a git repository
    git_status = run_git_command(['git', 'status'], "Checking git repository status")
    if git_status["status"] == "error":
        print("❌ Not in a git repository or git not available")
        return False
    
    # Step 2: Fetch all branches and prune deleted ones
    fetch_result = run_git_command(['git', 'fetch', 'origin', '--prune'], 
                                   "Fetching all branches and pruning deleted ones")
    
    # Step 3: Get current branch
    current_branch = run_git_command(['git', 'branch', '--show-current'], 
                                    "Getting current branch")
    
    # Step 4: List all local branches
    local_branches = run_git_command(['git', 'branch'], 
                                    "Listing local branches")
    
    # Step 5: List all remote branches
    remote_branches = run_git_command(['git', 'branch', '-r'], 
                                     "Listing remote branches")
    
    # Step 6: List all branches (local + remote)
    all_branches = run_git_command(['git', 'branch', '-a'], 
                                  "Listing all branches (local + remote)")
    
    # Step 7: Show merged branches
    merged_branches = run_git_command(['git', 'branch', '--merged'], 
                                     "Showing merged branches")
    
    print("\n" + "=" * 50)
    print("📋 Branch Refresh Summary")
    print("=" * 50)
    
    print(f"\n🌿 Current Branch: {current_branch.get('output', 'Unknown')}")
    
    if local_branches.get('output'):
        local_list = [branch.strip('* ').strip() for branch in local_branches['output'].split('\n') if branch.strip()]
        print(f"\n📍 Local Branches ({len(local_list)}):")
        for branch in local_list[:10]:  # Show first 10
            print(f"   • {branch}")
        if len(local_list) > 10:
            print(f"   ... and {len(local_list) - 10} more")
    
    if remote_branches.get('output'):
        remote_list = [branch.strip().replace('origin/', '') for branch in remote_branches['output'].split('\n') 
                      if branch.strip() and 'origin/' in branch and 'HEAD' not in branch]
        print(f"\n🔗 Remote Branches ({len(remote_list)}):")
        for branch in remote_list[:10]:  # Show first 10
            print(f"   • {branch}")
        if len(remote_list) > 10:
            print(f"   ... and {len(remote_list) - 10} more")
    
    # Step 8: Check for new branches that aren't tracked locally
    if remote_branches.get('output') and local_branches.get('output'):
        remote_list = [branch.strip().replace('origin/', '') for branch in remote_branches['output'].split('\n') 
                      if branch.strip() and 'origin/' in branch and 'HEAD' not in branch]
        local_list = [branch.strip('* ').strip() for branch in local_branches['output'].split('\n') if branch.strip()]
        
        new_branches = [branch for branch in remote_list if branch not in local_list and branch != 'HEAD']
        
        if new_branches:
            print(f"\n🆕 New Remote Branches Available ({len(new_branches)}):")
            for branch in new_branches[:5]:  # Show first 5
                print(f"   • {branch}")
            if len(new_branches) > 5:
                print(f"   ... and {len(new_branches) - 5} more")
            
            print("\n💡 To checkout a new remote branch, use:")
            print("   git checkout -b <branch-name> origin/<branch-name>")
    
    print(f"\n✅ Branch refresh completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True

def checkout_branch(branch_name):
    """Checkout a specific branch"""
    print(f"\n🔄 Switching to branch: {branch_name}")
    
    # First try to checkout existing local branch
    checkout_result = run_git_command(['git', 'checkout', branch_name], 
                                     f"Checking out local branch {branch_name}")
    
    if checkout_result["status"] != "success":
        # Try to checkout remote branch
        print(f"🔄 Local branch not found, trying remote branch...")
        checkout_remote = run_git_command(['git', 'checkout', '-b', branch_name, f'origin/{branch_name}'], 
                                         f"Creating and checking out remote branch {branch_name}")
        
        if checkout_remote["status"] == "success":
            print(f"✅ Successfully created and checked out {branch_name} from remote")
            return True
        else:
            print(f"❌ Could not checkout branch {branch_name}")
            return False
    else:
        print(f"✅ Successfully switched to {branch_name}")
        return True

if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "refresh":
            refresh_branches()
        elif command == "checkout" and len(sys.argv) > 2:
            branch_name = sys.argv[2]
            if refresh_branches():
                checkout_branch(branch_name)
        else:
            print("Usage:")
            print("  python refresh_git_branches.py refresh")
            print("  python refresh_git_branches.py checkout <branch-name>")
    else:
        # Default: just refresh
        refresh_branches()
