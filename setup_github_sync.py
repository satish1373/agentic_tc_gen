
#!/usr/bin/env python3
"""
Setup script for GitHub sync automation
Run this to configure GitHub webhooks and test the sync functionality
"""

import os
import requests
import json
from datetime import datetime

def setup_github_webhook():
    """Setup GitHub webhook for automatic sync"""
    
    # Configuration
    github_token = os.getenv('GITHUB_TOKEN')
    github_owner = os.getenv('GITHUB_OWNER')
    github_repo = os.getenv('GITHUB_REPO')
    replit_url = os.getenv('REPL_URL', 'https://workspace.satish73learnin.replit.dev')
    webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    if not all([github_token, github_owner, github_repo]):
        print("❌ Missing required environment variables:")
        print("   - GITHUB_TOKEN")
        print("   - GITHUB_OWNER") 
        print("   - GITHUB_REPO")
        return False
    
    webhook_url = f"{replit_url}/github-sync"
    
    # GitHub API headers
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Webhook configuration
    webhook_config = {
        "name": "web",
        "active": True,
        "events": ["push", "pull_request"],
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "insecure_ssl": "0"
        }
    }
    
    if webhook_secret:
        webhook_config["config"]["secret"] = webhook_secret
    
    try:
        # Create webhook
        api_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/hooks"
        response = requests.post(api_url, headers=headers, json=webhook_config)
        
        if response.status_code == 201:
            webhook_data = response.json()
            print("✅ GitHub webhook created successfully!")
            print(f"   Webhook ID: {webhook_data['id']}")
            print(f"   Webhook URL: {webhook_url}")
            print(f"   Events: {', '.join(webhook_data['events'])}")
            return True
        elif response.status_code == 422:
            print("⚠️ Webhook already exists or validation failed")
            print(f"   Response: {response.json()}")
            return False
        else:
            print(f"❌ Failed to create webhook: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating webhook: {e}")
        return False

def test_sync_functionality():
    """Test the sync functionality"""
    # Use local URL for testing when running from within Replit
    local_url = "http://127.0.0.1:5000"
    replit_url = os.getenv('REPL_URL', 'https://workspace.satish73learnin.replit.dev')
    
    print("\n🧪 Testing sync functionality...")
    
    # Test 1: Check sync status - try local first, then external
    try:
        test_url = local_url
        try:
            response = requests.get(f"{test_url}/sync-status", timeout=5)
        except requests.exceptions.ConnectionError:
            # If local fails, try external URL
            test_url = replit_url
            response = requests.get(f"{test_url}/sync-status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ Sync status endpoint working")
            print(f"   URL tested: {test_url}")
            print(f"   GitHub secret configured: {status['github_secret_configured']}")
            print(f"   Auto-deploy enabled: {status['auto_deploy_enabled']}")
            print(f"   Target branch: {status['target_branch']}")
        else:
            print(f"❌ Sync status check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking sync status: {e}")
    
    # Test 2: Manual sync test
    try:
        print("\n🔄 Testing manual sync...")
        test_url = local_url
        try:
            response = requests.post(f"{test_url}/manual-sync", 
                                   json={"restart": False}, timeout=5)
        except requests.exceptions.ConnectionError:
            # If local fails, try external URL
            test_url = replit_url
            response = requests.post(f"{test_url}/manual-sync", 
                                   json={"restart": False}, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Manual sync test successful")
            print(f"   URL tested: {test_url}")
            print(f"   Pull status: {result.get('pull', {}).get('status')}")
            print(f"   Dependencies: {result.get('dependencies', {}).get('status')}")
        else:
            print(f"❌ Manual sync test failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing manual sync: {e}")

def display_configuration_guide():
    """Display configuration guide"""
    replit_url = os.getenv('REPL_URL', 'https://workspace.satish73learnin.replit.dev')
    
    print("\n" + "="*60)
    print("🔧 GITHUB SYNC CONFIGURATION GUIDE")
    print("="*60)
    
    print("\n📋 Required Secrets (add to Replit Secrets):")
    print("   GITHUB_TOKEN=your_github_personal_access_token")
    print("   GITHUB_OWNER=your_github_username_or_org")
    print("   GITHUB_REPO=your_repository_name")
    print("   GITHUB_WEBHOOK_SECRET=your_random_secret_string")
    print("   TARGET_BRANCH=main (optional, defaults to main)")
    print("   AUTO_DEPLOY_ON_PUSH=true (optional, defaults to true)")
    
    print("\n🔗 Webhook Configuration:")
    print(f"   URL: {replit_url}/github-sync")
    print("   Content type: application/json")
    print("   Events: push, pull_request")
    print("   Secret: Use GITHUB_WEBHOOK_SECRET value")
    
    print("\n📖 Usage:")
    print("   1. Push code to GitHub → Automatic sync & deploy")
    print("   2. Manual sync: POST /manual-sync")
    print("   3. Check status: GET /sync-status")
    
    print("\n🔄 Sync Workflow:")
    print("   1. Receive GitHub webhook")
    print("   2. Verify signature")
    print("   3. Pull latest changes")
    print("   4. Update dependencies (if requirements.txt changed)")
    print("   5. Restart application (if AUTO_DEPLOY_ON_PUSH=true)")

def main():
    print("🚀 GitHub Sync Setup for Replit")
    print("=" * 40)
    
    # Display configuration guide
    display_configuration_guide()
    
    # Setup webhook
    print("\n🔧 Setting up GitHub webhook...")
    webhook_success = setup_github_webhook()
    
    # Test functionality
    test_sync_functionality()
    
    # Summary
    print("\n" + "="*60)
    if webhook_success:
        print("✅ Setup completed successfully!")
        print("📝 Your workflow is now:")
        print("   Jira Issue → GitHub PR → Push to GitHub → Auto-sync to Replit → Auto-deploy")
    else:
        print("⚠️ Webhook setup had issues - check the configuration")
        print("💡 You can still use manual sync: POST /manual-sync")
    
    print(f"\n🔗 GitHub webhook URL: {os.getenv('REPL_URL', 'your-repl-url')}/github-sync")
    print("🎉 Happy coding!")

if __name__ == "__main__":
    main()
