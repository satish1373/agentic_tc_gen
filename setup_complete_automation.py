#!/usr/bin/env python3
"""
Complete Automation Setup
Sets up both Jira and GitHub webhooks for the unified automation system
"""

import os
import requests
import json
from datetime import datetime

def setup_secrets_guide():
    """Display guide for setting up secrets"""
    print("🔧 REQUIRED SECRETS CONFIGURATION")
    print("=" * 60)
    print("\n📋 Add these to your Replit Secrets:")
    print("   OPENAI_API_KEY=your_openai_api_key")
    print("   GITHUB_TOKEN=your_github_personal_access_token")
    print("   GITHUB_OWNER=your_github_username_or_org")
    print("   GITHUB_REPO=your_repository_name")
    print("   GITHUB_WEBHOOK_SECRET=your_random_secret_string")
    print("   JIRA_WEBHOOK_SECRET=your_jira_webhook_secret")
    print("   REPL_URL=your_replit_workspace_url")
    
    print("\n🔑 OpenAI API Key:")
    print("   - Go to https://platform.openai.com/api-keys")
    print("   - Create a new API key")
    print("   - Add it as OPENAI_API_KEY in Replit Secrets")
    
    print("\n🔑 GitHub Setup:")
    print("   - Go to GitHub Settings > Developer settings > Personal access tokens")
    print("   - Create token with 'repo' and 'webhook' permissions")
    print("   - Add as GITHUB_TOKEN in Replit Secrets")

def setup_jira_webhook():
    """Setup Jira webhook"""
    print("\n🎫 JIRA WEBHOOK SETUP")
    print("=" * 40)
    
    replit_url = os.getenv('REPL_URL', 'your-repl-url')
    webhook_url = f"{replit_url}/jira-webhook"
    
    print(f"📋 Jira Webhook Configuration:")
    print(f"   URL: {webhook_url}")
    print(f"   Content type: application/json")
    print(f"   Events: Issue created, Issue updated")
    print(f"   Secret: Use JIRA_WEBHOOK_SECRET value")
    
    print("\n📖 Manual Setup Steps:")
    print("1. Go to your Jira project settings")
    print("2. Navigate to Webhooks")
    print("3. Create new webhook with above URL")
    print("4. Select 'Issue created' and 'Issue updated' events")
    print("5. Add the secret from JIRA_WEBHOOK_SECRET")
    
    return True

def setup_github_webhook():
    """Setup GitHub webhook automatically"""
    print("\n🔗 GITHUB WEBHOOK SETUP")
    print("=" * 40)
    
    # Get configuration
    github_token = os.getenv('GITHUB_TOKEN')
    github_owner = os.getenv('GITHUB_OWNER')
    github_repo = os.getenv('GITHUB_REPO')
    replit_url = os.getenv('REPL_URL', 'your-repl-url')
    webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
    
    if not all([github_token, github_owner, github_repo]):
        print("❌ Missing GitHub configuration in secrets")
        print("   Please add GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return False
    
    webhook_url = f"{replit_url}/github-webhook"
    
    # GitHub API headers
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Check for existing webhooks
    api_url = f"https://api.github.com/repos/{github_owner}/{github_repo}/hooks"
    
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            webhooks = response.json()
            for webhook in webhooks:
                if webhook.get('config', {}).get('url') == webhook_url:
                    print(f"✅ GitHub webhook already exists (ID: {webhook['id']})")
                    return True
    except Exception as e:
        print(f"⚠️ Error checking existing webhooks: {e}")
    
    # Create new webhook
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
        response = requests.post(api_url, headers=headers, json=webhook_config)
        
        if response.status_code == 201:
            webhook_data = response.json()
            print(f"✅ GitHub webhook created successfully!")
            print(f"   Webhook ID: {webhook_data['id']}")
            print(f"   Webhook URL: {webhook_url}")
            return True
        else:
            print(f"❌ Failed to create webhook: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating webhook: {e}")
        return False

def test_automation_system():
    """Test the automation system"""
    print("\n🧪 TESTING AUTOMATION SYSTEM")
    print("=" * 40)
    
    # Test automation system status
    try:
        response = requests.get("http://127.0.0.1:8000/automation/status", timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Automation system is running")
            print(f"   AI enabled: {status['services']['ai_enabled']}")
            print(f"   Jira webhook: {status['services']['jira_webhook']}")
            print(f"   GitHub webhook: {status['services']['github_webhook']}")
        else:
            print(f"❌ Automation system error: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach automation system: {e}")
        print("   Make sure the Automation System workflow is running on port 8000")
    
    # Test with sample Jira ticket
    try:
        print("\n🎫 Testing Jira automation...")
        response = requests.post("http://127.0.0.1:8000/test/jira", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Jira test successful")
            print(f"   Status: {result.get('status')}")
            print(f"   Analysis: {result.get('analysis', {}).get('change_type', 'N/A')}")
            print(f"   Implementation: {result.get('implementation', {}).get('status', 'N/A')}")
        else:
            print(f"❌ Jira test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Jira test error: {e}")

def display_workflow_summary():
    """Display the complete workflow"""
    replit_url = os.getenv('REPL_URL', 'your-repl-url')
    
    print("\n" + "=" * 60)
    print("🎉 COMPLETE AUTOMATION WORKFLOW")
    print("=" * 60)
    
    print("\n📋 Full Pipeline:")
    print("1. 🎫 Create Jira ticket (Feature/Bug/Enhancement)")
    print("2. 🤖 AI analyzes ticket and determines implementation approach")
    print("3. 🔧 System automatically implements simple features (like due dates)")
    print("4. 📝 Creates git commit with changes")
    print("5. 🚀 Pushes to GitHub automatically")
    print("6. 🔄 GitHub webhook triggers deployment to Replit")
    print("7. ✅ Todo app is updated with new features")
    
    print("\n🔗 Webhook URLs:")
    print(f"   Jira: {replit_url}/jira-webhook")
    print(f"   GitHub: {replit_url}/github-webhook")
    print(f"   Status: {replit_url}/automation/status")
    
    print("\n📊 Running Services:")
    print("   • Todo App: http://localhost:5000")
    print("   • Automation System: http://localhost:8000")
    
    print("\n🎯 Supported Automatic Implementations:")
    print("   • Add due date to todo items")
    print("   • Add categories/tags to todos")
    print("   • UI enhancements (planned)")
    print("   • Bug fixes (assisted)")
    
    print("\n💡 Testing Your Setup:")
    print("1. Create a Jira ticket: 'Add due date feature to todo items'")
    print("2. Watch the automation system logs")
    print("3. Check if code was automatically modified")
    print("4. Verify changes appear in your todo app")

def main():
    """Main setup function"""
    print("🚀 COMPLETE AUTOMATION SETUP")
    print("Setting up Jira → AI → Code → GitHub → Deploy pipeline")
    print("=" * 60)
    
    # Display secrets guide
    setup_secrets_guide()
    
    # Setup webhooks
    jira_setup = setup_jira_webhook()
    github_setup = setup_github_webhook()
    
    # Test the system
    test_automation_system()
    
    # Display workflow summary
    display_workflow_summary()
    
    print("\n" + "=" * 60)
    if github_setup:
        print("✅ Setup completed successfully!")
        print("🤖 Your automation pipeline is ready!")
        print("\n🎯 Next steps:")
        print("1. Create a test Jira ticket")
        print("2. Watch the magic happen!")
    else:
        print("⚠️ Setup completed with some issues")
        print("📝 Please check the GitHub webhook configuration")
    
    print(f"\n📖 Full documentation and logs available in automation system")

if __name__ == "__main__":
    main()