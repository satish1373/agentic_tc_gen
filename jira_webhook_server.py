
from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv
from jira import JIRA
from jira_langgraph_generator import generate_test_cases_for_jira_issue

load_dotenv()

app = Flask(__name__)

# Jira configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Initialize Jira client (if credentials are available)
jira = None
if JIRA_URL and JIRA_USERNAME and JIRA_API_TOKEN:
    try:
        jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))
        print("✅ Jira client initialized successfully")
    except Exception as e:
        print(f"⚠️ Failed to initialize Jira client: {e}")
else:
    print("⚠️ Jira credentials not configured - webhook will work but won't update Jira")

@app.route('/jira-webhook', methods=['POST'])
def handle_jira_webhook():
    """Handle incoming Jira webhook events"""
    try:
        print("🔔 Received webhook request")
        payload = request.get_json()
        
        if not payload:
            print("❌ No JSON payload received")
            return jsonify({"status": "error", "message": "No JSON payload"}), 400
        
        print(f"📦 Webhook Event: {payload.get('webhookEvent', 'Unknown')}")
        
        # Log the full payload for debugging (remove in production)
        print(f"🔍 Payload keys: {list(payload.keys())}")
        
        # Check if this is an issue creation event
        if payload.get('webhookEvent') == 'jira:issue_created':
            issue_data = payload.get('issue', {})
            issue_key = issue_data.get('key')
            issue_summary = issue_data.get('fields', {}).get('summary')
            issue_type = issue_data.get('fields', {}).get('issuetype', {}).get('name')
            
            print(f"✅ New Jira issue created: {issue_key} - {issue_summary} ({issue_type})")
            
            # Trigger code completion based on issue type
            if issue_type in ['Bug', 'Task', 'Story']:
                print(f"🚀 Triggering test generation for {issue_type}")
                trigger_code_completion(issue_key, issue_summary, issue_type)
            else:
                print(f"⏭️ Skipping issue type: {issue_type}")
            
            return jsonify({
                "status": "success", 
                "message": f"Webhook processed for {issue_key}",
                "issue_key": issue_key,
                "issue_type": issue_type
            }), 200
        
        # Handle other webhook events
        elif payload.get('webhookEvent') == 'jira:issue_updated':
            issue_data = payload.get('issue', {})
            issue_key = issue_data.get('key')
            print(f"📝 Jira issue updated: {issue_key} (not processing)")
            
        return jsonify({"status": "ignored", "message": f"Event {payload.get('webhookEvent')} not processed"}), 200
        
    except Exception as e:
        error_msg = f"Error processing webhook: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"status": "error", "message": error_msg}), 500

def trigger_code_completion(issue_key, summary, issue_type):
    """Trigger automated test case generation using LangGraph"""
    try:
        print(f"🚀 Triggering LangGraph test generation for {issue_key}")
        print(f"📋 Issue: {summary}")
        print(f"🏷️ Type: {issue_type}")
        
        # Check if OpenAI API key is available
        if not os.getenv('OPENAI_API_KEY'):
            print("⚠️ OPENAI_API_KEY not found - using fallback template generation")
        
        # Generate test cases using LangGraph
        filename = generate_test_cases_for_jira_issue(issue_key, summary, issue_type)
        
        if filename:
            print(f"✅ LangGraph test generation successful: {filename}")
            # Update Jira issue with generated artifacts
            update_jira_issue(issue_key, filename)
            print(f"📄 Generated file: {filename}")
        else:
            print(f"❌ LangGraph test generation failed for {issue_key}")
            # Try updating Jira anyway to show the attempt
            update_jira_issue(issue_key, None)
            
    except Exception as e:
        error_msg = f"Error in LangGraph test generation: {str(e)}"
        print(f"❌ {error_msg}")
        # Try to update Jira with error information
        try:
            update_jira_issue(issue_key, None)
        except:
            pass

# Old test case generation functions removed - now using LangGraph AI generator

def update_jira_issue(issue_key, filename=None):
    """Update Jira issue with generated test case information"""
    try:
        if not jira:
            print("⚠️ Jira client not available - skipping issue update")
            return
            
        issue = jira.issue(issue_key)
        
        # Add comment with test case generation info
        if filename:
            comment_text = f"""
🤖 **Automated Test Cases Generated using LangGraph AI**

✅ **Generated file:** `{filename}`

🧪 **Features:**
- AI-powered test case analysis and generation
- Issue-type specific test scenarios
- Comprehensive coverage including positive, negative, and edge cases
- Automated traceability to this Jira issue

📍 **Location:** Test cases can be found in the project repository.

*Generated by LangGraph Agent on {issue_key}*
            """
        else:
            comment_text = f"""
⚠️ **Test Case Generation Attempted**

An attempt was made to generate automated test cases for this issue, but it was not successful. Please check the server logs for more details.

*Attempted by LangGraph Agent on {issue_key}*
            """
        
        jira.add_comment(issue, comment_text)
        print(f"✅ Updated Jira issue {issue_key} with test case information")
        
    except Exception as e:
        print(f"❌ Error updating Jira issue: {str(e)}")

@app.route('/')
def home():
    """Home page with server information"""
    return """
    <html>
    <head><title>Jira LangGraph Webhook Server</title></head>
    <body>
        <h1>🚀 Jira LangGraph Webhook Server</h1>
        <p><strong>Status:</strong> Running</p>
        <p><strong>Available Endpoints:</strong></p>
        <ul>
            <li><code>/jira-webhook</code> - POST endpoint for Jira webhooks</li>
            <li><code>/health</code> - GET endpoint for health checks</li>
        </ul>
        <p><strong>Configuration:</strong></p>
        <ul>
            <li>🤖 LangGraph AI-powered test case generation enabled</li>
            <li>🔗 Configure your Jira webhook to point to: <code>https://your-repl-url.replit.dev/jira-webhook</code></li>
        </ul>
    </body>
    </html>
    """

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/test-webhook', methods=['GET'])
def test_webhook():
    """Test endpoint to simulate a Jira webhook"""
    print("🧪 Testing webhook with sample data")
    
    # Simulate a Jira issue creation
    test_issue_key = "TEST-123"
    test_summary = "Sample bug for testing webhook integration"
    test_issue_type = "Bug"
    
    trigger_code_completion(test_issue_key, test_summary, test_issue_type)
    
    return jsonify({
        "status": "test_completed",
        "message": f"Test webhook triggered for {test_issue_key}",
        "issue_key": test_issue_key,
        "issue_type": test_issue_type
    }), 200

if __name__ == '__main__':
    print("🚀 Starting Jira LangGraph Webhook Server...")
    print("🔗 Configure your Jira webhook to point to: https://your-repl-url.replit.dev/jira-webhook")
    print("🤖 LangGraph AI-powered test case generation enabled")
    print("⚠️  Make sure OPENAI_API_KEY is set in Secrets for full AI capabilities")
    app.run(host='0.0.0.0', port=5000, debug=True)
