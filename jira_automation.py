#!/usr/bin/env python3
"""
Jira Automation System
Automatically implements code changes based on Jira ticket requests
"""

import os
import json
import hmac
import hashlib
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
import requests
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraAutomationAgent:
    """AI agent for processing Jira tickets and implementing code changes"""
    
    def __init__(self):
        self.openai_client = None
        self.setup_openai()
        
    def setup_openai(self):
        """Initialize OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized")
            else:
                logger.warning("⚠️ OpenAI API key not found - AI features disabled")
        except Exception as e:
            logger.error(f"❌ OpenAI initialization failed: {e}")
    
    def analyze_jira_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Jira ticket and determine required changes"""
        try:
            summary = ticket_data.get('summary', '')
            description = ticket_data.get('description', '')
            issue_type = ticket_data.get('issuetype', {}).get('name', '')
            
            logger.info(f"🎫 Analyzing ticket: {summary}")
            
            # Use AI to analyze the ticket if available
            if self.openai_client:
                analysis = self._ai_analyze_ticket(summary, description, issue_type)
            else:
                analysis = self._fallback_analyze_ticket(summary, description, issue_type)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error analyzing ticket: {e}")
            return {'error': str(e)}
    
    def _ai_analyze_ticket(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
        """Use AI to analyze ticket and generate implementation plan"""
        try:
            prompt = f"""
            Analyze this Jira ticket for a Todo application and provide implementation guidance:
            
            Summary: {summary}
            Description: {description}
            Type: {issue_type}
            
            Current Todo App Features:
            - Add/edit/delete todos
            - Mark todos complete/incomplete
            - Set priority levels (Low/Medium/High)
            - View statistics
            - Basic web interface
            
            Provide a JSON response with:
            1. "change_type": "feature", "bugfix", "ui", or "enhancement"
            2. "files_to_modify": List of files that need changes
            3. "implementation_steps": Detailed steps to implement
            4. "code_changes": Specific code modifications needed
            5. "testing_strategy": How to test the changes
            6. "deployment_notes": Any deployment considerations
            
            Focus on practical, implementable changes for the existing todo app structure.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            # Try to parse as JSON, fallback to structured text if needed
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"ai_response": result, "change_type": "manual_review"}
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return self._fallback_analyze_ticket(summary, description, issue_type)
    
    def _fallback_analyze_ticket(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
        """Fallback analysis when AI is not available"""
        change_type = "enhancement"
        
        # Basic keyword detection
        if any(word in summary.lower() for word in ['bug', 'fix', 'error', 'broken']):
            change_type = "bugfix"
        elif any(word in summary.lower() for word in ['ui', 'interface', 'design', 'style']):
            change_type = "ui"
        elif any(word in summary.lower() for word in ['add', 'new', 'feature', 'implement']):
            change_type = "feature"
        
        return {
            "change_type": change_type,
            "files_to_modify": ["todo_app.py"],
            "implementation_steps": [
                f"Review ticket: {summary}",
                "Identify specific changes needed",
                "Modify todo_app.py accordingly",
                "Test the changes",
                "Deploy to development"
            ],
            "code_changes": f"Manual implementation required for: {summary}",
            "testing_strategy": "Manual testing of todo functionality",
            "deployment_notes": "Standard deployment process"
        }
    
    def implement_changes(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Implement the code changes based on analysis"""
        try:
            logger.info(f"🔧 Implementing changes for {ticket_key}")
            
            change_type = analysis.get('change_type', 'manual_review')
            files_to_modify = analysis.get('files_to_modify', [])
            
            if change_type == 'manual_review':
                return {
                    'status': 'manual_review_required',
                    'message': 'This ticket requires manual review and implementation'
                }
            
            # For now, create a branch and implementation plan
            branch_name = f"jira-{ticket_key.lower()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Create implementation plan file
            plan_file = f"implementation_plan_{ticket_key}.md"
            self._create_implementation_plan(plan_file, analysis, ticket_key)
            
            return {
                'status': 'plan_created',
                'branch_name': branch_name,
                'plan_file': plan_file,
                'files_to_modify': files_to_modify,
                'next_steps': analysis.get('implementation_steps', [])
            }
            
        except Exception as e:
            logger.error(f"❌ Error implementing changes: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _create_implementation_plan(self, plan_file: str, analysis: Dict[str, Any], ticket_key: str):
        """Create a detailed implementation plan file"""
        plan_content = f"""# Implementation Plan: {ticket_key}

## Analysis Results
- **Change Type**: {analysis.get('change_type', 'Unknown')}
- **Files to Modify**: {', '.join(analysis.get('files_to_modify', []))}

## Implementation Steps
"""
        
        for i, step in enumerate(analysis.get('implementation_steps', []), 1):
            plan_content += f"{i}. {step}\n"
        
        plan_content += f"""
## Code Changes Required
{analysis.get('code_changes', 'See AI analysis above')}

## Testing Strategy
{analysis.get('testing_strategy', 'Manual testing required')}

## Deployment Notes
{analysis.get('deployment_notes', 'Standard deployment process')}

## Generated At
{datetime.now().isoformat()}
"""
        
        with open(plan_file, 'w') as f:
            f.write(plan_content)
        
        logger.info(f"📋 Implementation plan created: {plan_file}")

class JiraWebhookHandler:
    """Handles incoming Jira webhooks"""
    
    def __init__(self):
        self.agent = JiraAutomationAgent()
        self.webhook_secret = os.getenv('JIRA_WEBHOOK_SECRET', '')
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Jira webhook signature"""
        if not self.webhook_secret:
            logger.warning("⚠️ No webhook secret configured - skipping verification")
            return True
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        except Exception as e:
            logger.error(f"❌ Signature verification failed: {e}")
            return False
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Jira webhook"""
        try:
            webhook_event = payload.get('webhookEvent', '')
            
            if webhook_event == 'jira:issue_created':
                return self._handle_issue_created(payload)
            elif webhook_event == 'jira:issue_updated':
                return self._handle_issue_updated(payload)
            else:
                return {'status': 'ignored', 'reason': f'Event type {webhook_event} not handled'}
                
        except Exception as e:
            logger.error(f"❌ Error processing webhook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_issue_created(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new issue creation"""
        try:
            issue = payload.get('issue', {})
            fields = issue.get('fields', {})
            issue_key = issue.get('key', '')
            
            logger.info(f"🆕 New Jira issue created: {issue_key}")
            
            # Extract ticket information
            ticket_data = {
                'key': issue_key,
                'summary': fields.get('summary', ''),
                'description': fields.get('description', ''),
                'issuetype': fields.get('issuetype', {}),
                'priority': fields.get('priority', {}),
                'assignee': fields.get('assignee', {}),
                'reporter': fields.get('reporter', {})
            }
            
            # Analyze and implement
            analysis = self.agent.analyze_jira_ticket(ticket_data)
            implementation = self.agent.implement_changes(analysis, issue_key)
            
            return {
                'status': 'processed',
                'issue_key': issue_key,
                'analysis': analysis,
                'implementation': implementation
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling issue creation: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_issue_updated(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle issue updates"""
        issue = payload.get('issue', {})
        issue_key = issue.get('key', '')
        
        logger.info(f"📝 Jira issue updated: {issue_key}")
        
        # For now, we'll only process new issues
        # Issue updates could trigger re-analysis if needed
        return {
            'status': 'acknowledged',
            'issue_key': issue_key,
            'message': 'Issue update noted but not processed'
        }

# Flask app for webhook endpoint
app = Flask(__name__)
webhook_handler = JiraWebhookHandler()

@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    """Jira webhook endpoint"""
    try:
        payload = request.get_json()
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Verify signature
        if not webhook_handler.verify_webhook_signature(request.data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Process webhook
        result = webhook_handler.process_webhook(payload)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Webhook endpoint error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/jira-webhook', methods=['GET'])
def jira_webhook_verify():
    """Webhook verification endpoint"""
    return jsonify({
        'status': 'active',
        'service': 'Jira Automation Webhook',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/automation/status')
def automation_status():
    """Get automation system status"""
    return jsonify({
        'status': 'running',
        'services': {
            'jira_webhook': 'active',
            'ai_agent': 'active' if webhook_handler.agent.openai_client else 'disabled',
            'deployment': 'configured'
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/automation/test', methods=['POST'])
def test_automation():
    """Test the automation with a sample ticket"""
    sample_ticket = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "TEST-001",
            "fields": {
                "summary": "Add due date feature to todo items",
                "description": "Users should be able to set due dates for their todo items and see overdue tasks highlighted",
                "issuetype": {"name": "Feature"},
                "priority": {"name": "Medium"}
            }
        }
    }
    
    result = webhook_handler.process_webhook(sample_ticket)
    return jsonify(result)

if __name__ == '__main__':
    print("🤖 Starting Jira Automation System...")
    print("🔗 Webhook endpoint: http://localhost:5001/jira-webhook")
    print("📊 Status endpoint: http://localhost:5001/automation/status")
    app.run(host='0.0.0.0', port=5001, debug=True)