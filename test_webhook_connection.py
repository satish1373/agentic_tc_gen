
"""
Test script to verify Jira webhook connection
"""
import requests
import json

def test_webhook_connection():
    """Test the webhook endpoint connectivity"""
    
    # Try to get the correct Replit URL
    import os
    base_url = os.environ.get('REPL_URL')
    
    # Check if server is running locally first
    local_url = "http://127.0.0.1:5000"
    external_url = base_url or "https://workspace.satish73learnin.replit.dev"
    
    # Test local first, then external
    webhook_url = local_url + "/jira-webhook"
    
    print("🧪 Testing Jira Webhook Connection")
    print(f"🔗 Testing URL: {webhook_url}")
    
    # Test 1: Basic GET request (webhook verification)
    try:
        print("\n1️⃣ Testing GET request (webhook verification)...")
        response = requests.get(webhook_url, timeout=10)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ GET request successful")
        else:
            print("   ❌ GET request failed")
            
    except Exception as e:
        print(f"   ❌ GET request error: {e}")
    
    # Test 2: Simulate Jira webhook POST
    try:
        print("\n2️⃣ Testing POST request (simulated Jira webhook)...")
        
        # Sample Jira webhook payload
        test_payload = {
            "webhookEvent": "jira:issue_created",
            "issue": {
                "key": "TEST-999",
                "fields": {
                    "summary": "Test webhook connectivity issue",
                    "issuetype": {
                        "name": "Bug"
                    },
                    "description": "This is a test issue to verify webhook connectivity"
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Atlassian-Webhooks/1.0"
        }
        
        response = requests.post(
            webhook_url, 
            json=test_payload,
            headers=headers,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ POST request successful")
        else:
            print("   ❌ POST request failed")
            
    except Exception as e:
        print(f"   ❌ POST request error: {e}")
    
    # Test 3: Check if server is accessible locally
    try:
        print("\n3️⃣ Testing local server accessibility...")
        local_urls = ["http://127.0.0.1:5000/health", "http://localhost:5000/health"]
        
        for url in local_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ Local server accessible at {url}")
                    break
            except:
                continue
        else:
            print("   ❌ Local server not accessible")
            
    except Exception as e:
        print(f"   ❌ Server accessibility error: {e}")
    
    # Test 4: Check deployment URL if available
    try:
        print("\n4️⃣ Testing deployment accessibility...")
        repl_url = os.environ.get('REPL_URL')
        if repl_url:
            health_url = f"{repl_url}/health"
            response = requests.get(health_url, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Deployment accessible at {health_url}")
            else:
                print(f"   ⚠️ Deployment returned status: {response.status_code}")
        else:
            print("   ⚠️ REPL_URL environment variable not set")
    except Exception as e:
        print(f"   ❌ Deployment accessibility error: {e}")
    
    print("\n📋 Webhook Configuration Instructions:")
    print("=" * 50)
    print("1. Go to your Jira instance")
    print("2. Navigate to System → WebHooks")
    print("3. Create a new webhook with:")
    if os.environ.get('REPL_URL'):
        print(f"   URL: {os.environ.get('REPL_URL')}/jira-webhook")
    else:
        print(f"   URL: {webhook_url} (update with your actual deployment URL)")
    print("   Events: Issue → created")
    print("4. Test the webhook in Jira")
    print("5. Check the Replit console for incoming requests")

if __name__ == "__main__":
    test_webhook_connection()
