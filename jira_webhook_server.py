
from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv
from jira import JIRA

load_dotenv()

app = Flask(__name__)

# Jira configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USERNAME = os.getenv('JIRA_USERNAME')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Initialize Jira client
jira = JIRA(server=JIRA_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))

@app.route('/jira-webhook', methods=['POST'])
def handle_jira_webhook():
    """Handle incoming Jira webhook events"""
    try:
        payload = request.get_json()
        
        # Check if this is an issue creation event
        if payload.get('webhookEvent') == 'jira:issue_created':
            issue_data = payload.get('issue', {})
            issue_key = issue_data.get('key')
            issue_summary = issue_data.get('fields', {}).get('summary')
            issue_type = issue_data.get('fields', {}).get('issuetype', {}).get('name')
            
            print(f"New Jira issue created: {issue_key} - {issue_summary}")
            
            # Trigger code completion based on issue type
            if issue_type in ['Bug', 'Task', 'Story']:
                trigger_code_completion(issue_key, issue_summary, issue_type)
            
            return jsonify({"status": "success", "message": "Webhook processed"}), 200
            
        return jsonify({"status": "ignored", "message": "Event not processed"}), 200
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def trigger_code_completion(issue_key, summary, issue_type):
    """Trigger automated code completion based on Jira issue"""
    try:
        # Generate test cases based on the issue
        if issue_type == 'Bug':
            generate_bug_test_cases(issue_key, summary)
        elif issue_type == 'Story':
            generate_story_test_cases(issue_key, summary)
        elif issue_type == 'Task':
            generate_task_test_cases(issue_key, summary)
            
        # Update Jira issue with generated artifacts
        update_jira_issue(issue_key)
        
    except Exception as e:
        print(f"Error in code completion: {str(e)}")

def generate_bug_test_cases(issue_key, summary):
    """Generate test cases for bug issues"""
    test_case_template = {
        "id": f"{issue_key}_BUG_001",
        "title": f"Verify fix for {issue_key} - {summary}",
        "description": f"Test to verify the bug fix for: {summary}",
        "test_type": "regression",
        "preconditions": [
            "System is operational and accessible",
            "Bug reproduction steps are available"
        ],
        "test_steps": [
            "Navigate to the affected functionality",
            "Reproduce the original bug scenario",
            "Verify the fix is applied",
            "Test edge cases related to the bug"
        ],
        "expected_result": f"Bug {issue_key} is fixed and system behaves as expected",
        "priority": "High",
        "tags": ["bug_fix", "regression", issue_key.lower()],
        "jira_issue": issue_key
    }
    
    # Save test case to file
    filename = f"jira_generated_test_cases_{issue_key}.json"
    with open(filename, 'w') as f:
        json.dump([test_case_template], f, indent=2)
    
    print(f"Generated bug test case for {issue_key}")

def generate_story_test_cases(issue_key, summary):
    """Generate test cases for story issues"""
    test_cases = [
        {
            "id": f"{issue_key}_STORY_POS_001",
            "title": f"Verify {issue_key} - Positive scenario",
            "description": f"Test successful execution of story: {summary}",
            "test_type": "positive",
            "preconditions": [
                "System is operational and accessible",
                "User has appropriate permissions"
            ],
            "test_steps": [
                "Navigate to the new functionality",
                "Execute the user story scenario",
                "Verify expected behavior",
                "Validate user interface elements"
            ],
            "expected_result": f"Story {issue_key} functionality works as specified",
            "priority": "Medium",
            "tags": ["story", "positive", issue_key.lower()],
            "jira_issue": issue_key
        },
        {
            "id": f"{issue_key}_STORY_NEG_002",
            "title": f"Verify {issue_key} - Negative scenario",
            "description": f"Test error handling for story: {summary}",
            "test_type": "negative",
            "preconditions": [
                "System is operational and accessible",
                "Error conditions can be simulated"
            ],
            "test_steps": [
                "Navigate to the new functionality",
                "Execute invalid scenarios",
                "Verify proper error handling",
                "Check error messages are user-friendly"
            ],
            "expected_result": f"Story {issue_key} handles errors gracefully",
            "priority": "Medium",
            "tags": ["story", "negative", issue_key.lower()],
            "jira_issue": issue_key
        }
    ]
    
    filename = f"jira_generated_test_cases_{issue_key}.json"
    with open(filename, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Generated story test cases for {issue_key}")

def generate_task_test_cases(issue_key, summary):
    """Generate test cases for task issues"""
    test_case_template = {
        "id": f"{issue_key}_TASK_001",
        "title": f"Verify {issue_key} - Task completion",
        "description": f"Test completion of task: {summary}",
        "test_type": "functional",
        "preconditions": [
            "System is operational and accessible",
            "Task prerequisites are met"
        ],
        "test_steps": [
            "Verify task implementation",
            "Test functionality changes",
            "Validate performance impact",
            "Check integration points"
        ],
        "expected_result": f"Task {issue_key} is completed successfully",
        "priority": "Medium",
        "tags": ["task", "functional", issue_key.lower()],
        "jira_issue": issue_key
    }
    
    filename = f"jira_generated_test_cases_{issue_key}.json"
    with open(filename, 'w') as f:
        json.dump([test_case_template], f, indent=2)
    
    print(f"Generated task test case for {issue_key}")

def update_jira_issue(issue_key):
    """Update Jira issue with generated test case information"""
    try:
        issue = jira.issue(issue_key)
        
        # Add comment with test case generation info
        comment_text = f"""
        Automated test cases have been generated for this issue.
        
        Generated files:
        - jira_generated_test_cases_{issue_key}.json
        
        Test cases are automatically created based on the issue type and can be found in the project repository.
        """
        
        jira.add_comment(issue, comment_text)
        print(f"Updated Jira issue {issue_key} with test case information")
        
    except Exception as e:
        print(f"Error updating Jira issue: {str(e)}")

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    print("Starting Jira webhook server...")
    print("Make sure to configure your Jira webhook to point to: https://your-repl-url.replit.dev/jira-webhook")
    app.run(host='0.0.0.0', port=5000, debug=True)
