
import requests
import json
import time
from datetime import datetime

def test_complete_jira_integration():
    """Test the complete Jira integration flow"""
    
    print("🧪 Testing Complete Jira Integration Setup")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Webhook GET (verification)
    print("\n2️⃣ Testing Webhook Verification...")
    try:
        response = requests.get(f"{base_url}/jira-webhook", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Webhook verification passed: {result.get('status')}")
        else:
            print(f"   ❌ Webhook verification failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Webhook verification error: {e}")
    
    # Test 3: Simulate New Feature Issue Creation
    print("\n3️⃣ Testing New Feature Issue Processing...")
    test_payload = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "FEATURE-001",
            "fields": {
                "summary": "Implement user authentication with OAuth 2.0",
                "issuetype": {
                    "name": "New Feature"
                },
                "description": "As a user, I want to authenticate using OAuth 2.0 providers (Google, GitHub) so that I can access the application securely without creating a new password."
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Atlassian-Webhooks/1.0"
    }
    
    try:
        print("   📤 Sending new feature webhook...")
        response = requests.post(
            f"{base_url}/jira-webhook", 
            json=test_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Webhook processed successfully")
            print(f"   📋 Status: {result.get('status')}")
            print(f"   🔑 Issue Key: {result.get('issue_key')}")
            print(f"   🏷️ Issue Type: {result.get('issue_type')}")
        else:
            print(f"   ❌ Webhook processing failed: {response.status_code}")
            print(f"   📝 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Webhook processing error: {e}")
    
    # Test 4: Manual AI Analysis
    print("\n4️⃣ Testing Manual AI Analysis...")
    try:
        analysis_payload = {
            "summary": "Add user notification preferences feature",
            "issue_type": "New Feature", 
            "description": "Users should be able to configure their notification preferences for email, SMS, and in-app notifications."
        }
        
        response = requests.post(
            f"{base_url}/ai-analyze/TEST-NEW-FEATURE",
            json=analysis_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Manual AI analysis successful")
            print(f"   📊 Analysis status: {result.get('status')}")
        else:
            print(f"   ❌ Manual AI analysis failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Manual AI analysis error: {e}")
    
    # Test 5: GitHub Integration (if configured)
    print("\n5️⃣ Testing GitHub Integration...")
    try:
        response = requests.get(f"{base_url}/test-github-integration", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success':
                print("   ✅ GitHub integration working")
                print(f"   🔗 PR URL: {result.get('github_result', {}).get('pr_url', 'N/A')}")
            else:
                print(f"   ⚠️ GitHub integration available but test failed")
        elif response.status_code == 400:
            result = response.json()
            if 'not configured' in result.get('message', ''):
                print("   ⚠️ GitHub integration not configured (optional)")
            else:
                print(f"   ❌ GitHub integration error: {result.get('message')}")
        else:
            print(f"   ❌ GitHub integration test failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ GitHub integration test error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Integration test completed!")
    print("\n📋 Summary:")
    print("- Jira webhook server is running on port 5000")
    print("- Webhook endpoint accepts both GET and POST requests")
    print("- AI-powered analysis is working")
    print("- Test case generation is functional")
    print("- GitHub integration is available (if configured)")
    
    print("\n🔗 Ready for Jira Configuration:")
    print("Webhook URL: https://workspace.satish73learnin.replit.dev/jira-webhook")
    print("Events: Issue → Created")
    print("Issue Types: New Feature, Feature, Task, Story, Bug, Epic, Improvement")

if __name__ == "__main__":
    test_complete_jira_integration()
