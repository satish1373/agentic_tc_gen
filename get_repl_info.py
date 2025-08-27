
import os
import requests

print("=== REPL INFORMATION ===")
print(f"Repl ID: {os.environ.get('REPL_ID', 'Not available')}")
print(f"Repl Owner: {os.environ.get('REPL_OWNER', 'Not available')}")
print(f"Repl Slug: {os.environ.get('REPL_SLUG', 'Not available')}")

# Try to construct the URL
repl_owner = os.environ.get('REPL_OWNER', '').lower()
repl_slug = os.environ.get('REPL_SLUG', '').lower()

if repl_owner and repl_slug:
    repl_url = f"https://{repl_slug}.{repl_owner}.replit.dev"
    webhook_url = f"{repl_url}/jira-webhook"
    
    print(f"\n=== YOUR REPL URLs ===")
    print(f"Repl URL: {repl_url}")
    print(f"Jira Webhook URL: {webhook_url}")
    
    # Test if the webhook endpoint is accessible
    try:
        response = requests.get(f"{repl_url}/health")
        if response.status_code == 200:
            print(f"✅ Webhook server is accessible")
        else:
            print(f"⚠️ Webhook server returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach webhook server: {e}")
        
    print(f"\n=== CONFIGURATION ===")
    print("Configure your Jira webhook with this URL:")
    print(f"🔗 {webhook_url}")
else:
    print("\n❌ Cannot determine Repl URL from environment variables")
    print("Check your browser's address bar for the actual URL")

# Check environment variables
print(f"\n=== ENVIRONMENT CHECK ===")
print(f"OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}")
print(f"JIRA_URL: {'✅ Set' if os.getenv('JIRA_URL') else '❌ Not set'}")
print(f"JIRA_USERNAME: {'✅ Set' if os.getenv('JIRA_USERNAME') else '❌ Not set'}")
print(f"JIRA_API_TOKEN: {'✅ Set' if os.getenv('JIRA_API_TOKEN') else '❌ Not set'}")
