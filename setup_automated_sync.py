
import os
import requests
import json

def setup_github_webhook_for_sync():
    """Set up GitHub webhook to sync changes back to Replit"""
    
    print("🔄 Setting up GitHub Webhook for Replit Sync")
    print("=" * 50)
    
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
        print("\n💡 Add these to your Replit Secrets")
        return False
    
    webhook_url = f"{replit_url}/github-sync"
    
    # GitHub API headers
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check if webhook already exists
    print("🔍 Checking for existing webhooks...")
    api_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/hooks"
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            webhooks = response.json()
            existing_webhook = None
            
            for webhook in webhooks:
                if webhook.get('config', {}).get('url') == webhook_url:
                    existing_webhook = webhook
                    break
            
            if existing_webhook:
                print(f"✅ Webhook already exists (ID: {existing_webhook['id']})")
                print(f"🔗 URL: {webhook_url}")
                print(f"📋 Events: {existing_webhook.get('events', [])}")
                return True
        
    except Exception as e:
        print(f"⚠️ Error checking existing webhooks: {e}")
    
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
        print("🔐 Webhook secret configured")
    else:
        print("⚠️ No webhook secret configured - add GITHUB_WEBHOOK_SECRET to Secrets")
    
    try:
        # Create webhook
        print("🔨 Creating GitHub webhook...")
        response = requests.post(api_url, headers=headers, json=webhook_config)
        
        if response.status_code == 201:
            webhook_data = response.json()
            print(f"✅ GitHub webhook created successfully!")
            print(f"   Webhook ID: {webhook_data['id']}")
            print(f"   Webhook URL: {webhook_url}")
            print(f"   Events: {webhook_data['events']}")
            return True
            
        elif response.status_code == 422:
            error_data = response.json()
            if "Hook already exists" in str(error_data):
                print("✅ Webhook already exists")
                return True
            else:
                print(f"❌ Webhook creation failed: {error_data}")
                return False
        else:
            print(f"❌ Webhook creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating webhook: {e}")
        return False

def test_github_sync():
    """Test the GitHub sync functionality"""
    
    print("\n🧪 Testing GitHub Sync Functionality")
    print("=" * 40)
    
    # Test local webhook endpoint
    try:
        response = requests.get("http://127.0.0.1:5000/sync-status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Sync endpoint is active")
            print(f"   Auto-deploy: {status.get('auto_deploy_enabled')}")
            print(f"   Target branch: {status.get('target_branch')}")
            print(f"   GitHub integration: {status.get('github_integration', {}).get('enabled')}")
        else:
            print(f"❌ Sync endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Could not reach sync endpoint: {e}")
    
    # Test manual sync
    try:
        print("\n🔄 Testing manual sync...")
        response = requests.post("http://127.0.0.1:5000/manual-sync", 
                               json={"restart": False}, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ Manual sync test successful")
            print(f"   Pull status: {result.get('pull', {}).get('status')}")
            print(f"   Dependencies: {result.get('dependencies', {}).get('status')}")
        else:
            print(f"❌ Manual sync test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual sync test error: {e}")

def display_setup_summary():
    """Display setup summary and next steps"""
    
    replit_url = os.getenv('REPL_URL', 'https://workspace.satish73learnin.replit.dev')
    
    print("\n" + "=" * 60)
    print("🎉 GitHub Sync Setup Complete!")
    print("=" * 60)
    
    print("\n📋 Workflow Summary:")
    print("1. Create Jira issue → Webhook triggers AI analysis")
    print("2. AI creates GitHub branch and PR with generated files")
    print("3. You review and push changes to GitHub")
    print("4. GitHub webhook automatically syncs changes to Replit")
    print("5. Replit workspace updated with latest code")
    
    print("\n🔗 Important URLs:")
    print(f"   Jira Webhook: {replit_url}/jira-webhook")
    print(f"   GitHub Webhook: {replit_url}/github-sync")
    print(f"   Sync Status: {replit_url}/sync-status")
    print(f"   Manual Sync: {replit_url}/manual-sync")
    
    print("\n💡 Testing Your Setup:")
    print("1. Create a test Jira issue (type: Feature)")
    print("2. Check that GitHub branch and PR are created")
    print("3. Make changes to the PR and merge it")
    print("4. Verify changes appear in Replit workspace")
    
    print("\n🔧 Troubleshooting:")
    print("- Check Replit console for webhook logs")
    print("- Verify GitHub webhook is delivering successfully")
    print("- Test manual sync if automatic sync fails")
    print("- Ensure all secrets are properly configured")

def main():
    """Main setup function"""
    
    print("🚀 Automated GitHub Sync Setup for Replit")
    print("This will configure automatic syncing from GitHub to Replit")
    print("=" * 60)
    
    # Setup webhook
    webhook_success = setup_github_webhook_for_sync()
    
    # Test functionality
    test_github_sync()
    
    # Display summary
    display_setup_summary()
    
    if webhook_success:
        print("\n✅ Setup completed successfully!")
        print("Your Replit workspace will now automatically sync with GitHub changes.")
    else:
        print("\n⚠️ Setup completed with some issues.")
        print("Check the errors above and ensure all secrets are configured.")

if __name__ == "__main__":
    main()
