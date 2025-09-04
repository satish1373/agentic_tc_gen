#!/usr/bin/env python3
"""
Unified Automation System
Handles both Jira webhooks and GitHub webhooks for complete automation pipeline:
Jira Ticket → AI Analysis → Code Generation → GitHub Push → Auto-Deploy
"""

import os
import json
import hmac
import hashlib
import subprocess
import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from openai import OpenAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TodoCodeModifier:
    """Handles automatic code modifications for the todo app"""
    
    def __init__(self):
        self.app_file = "todo_app.py"
        
    def implement_feature(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Implement a feature based on AI analysis"""
        try:
            change_type = analysis.get('change_type', 'manual_review')
            
            if change_type == 'feature':
                return self._add_feature(analysis, ticket_key)
            elif change_type == 'ui':
                return self._modify_ui(analysis, ticket_key)
            elif change_type == 'enhancement':
                return self._add_enhancement(analysis, ticket_key)
            else:
                return {'status': 'manual_review_required', 'message': 'Complex changes require manual implementation'}
                
        except Exception as e:
            logger.error(f"❌ Error implementing feature: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _add_feature(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Add a new feature to the todo app"""
        # For demonstration, let's implement a due date feature
        if 'due date' in analysis.get('code_changes', '').lower():
            return self._add_due_date_feature(ticket_key)
        elif 'category' in analysis.get('code_changes', '').lower():
            return self._add_category_feature(ticket_key)
        else:
            # Create a generic enhancement
            return self._create_feature_branch(analysis, ticket_key)
    
    def _add_due_date_feature(self, ticket_key: str) -> Dict[str, Any]:
        """Add due date functionality to todo items"""
        try:
            # Read current file
            with open(self.app_file, 'r') as f:
                content = f.read()
            
            # Check if due date is already implemented
            if 'due_date' in content:
                return {'status': 'already_implemented', 'message': 'Due date feature already exists'}
            
            # Add due_date to TodoItem class
            old_init = '''def __init__(self, id: str, title: str, description: str = "", completed: bool = False, 
                 priority: str = "Medium", created_at: Optional[str] = None):'''
            
            new_init = '''def __init__(self, id: str, title: str, description: str = "", completed: bool = False, 
                 priority: str = "Medium", due_date: Optional[str] = None, created_at: Optional[str] = None):'''
            
            if old_init in content:
                content = content.replace(old_init, new_init)
                
                # Add due_date property
                old_properties = '''        self.priority = priority
        self.created_at = created_at if created_at is not None else datetime.now().isoformat()'''
                
                new_properties = '''        self.priority = priority
        self.due_date = due_date
        self.created_at = created_at if created_at is not None else datetime.now().isoformat()'''
                
                content = content.replace(old_properties, new_properties)
                
                # Update to_dict method
                old_dict = '''        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'priority': self.priority,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }'''
                
                new_dict = '''        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'priority': self.priority,
            'due_date': self.due_date,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }'''
                
                content = content.replace(old_dict, new_dict)
                
                # Update from_dict method
                old_from_dict = '''        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            completed=data.get('completed', False),
            priority=data.get('priority', 'Medium'),
            created_at=data.get('created_at')
        )'''
                
                new_from_dict = '''        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            completed=data.get('completed', False),
            priority=data.get('priority', 'Medium'),
            due_date=data.get('due_date'),
            created_at=data.get('created_at')
        )'''
                
                content = content.replace(old_from_dict, new_from_dict)
                
                # Update add_todo method
                old_add_todo = '''    def add_todo(self, title: str, description: str = "", priority: str = "Medium") -> TodoItem:
        """Add a new todo item"""
        todo_id = str(len(self.todos) + 1).zfill(3)
        todo = TodoItem(todo_id, title, description, priority=priority)'''
                
                new_add_todo = '''    def add_todo(self, title: str, description: str = "", priority: str = "Medium", due_date: Optional[str] = None) -> TodoItem:
        """Add a new todo item"""
        todo_id = str(len(self.todos) + 1).zfill(3)
        todo = TodoItem(todo_id, title, description, priority=priority, due_date=due_date)'''
                
                content = content.replace(old_add_todo, new_add_todo)
                
                # Add due date input field to form
                old_form = '''                <select name="priority">
                    <option value="Low">Low Priority</option>
                    <option value="Medium" selected>Medium Priority</option>
                    <option value="High">High Priority</option>
                </select>
                <button type="submit">Add Todo</button>'''
                
                new_form = '''                <select name="priority">
                    <option value="Low">Low Priority</option>
                    <option value="Medium" selected>Medium Priority</option>
                    <option value="High">High Priority</option>
                </select>
                <input type="date" name="due_date" placeholder="Due date (optional)">
                <button type="submit">Add Todo</button>'''
                
                content = content.replace(old_form, new_form)
                
                # Update add_todo route
                old_route = '''    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'Medium')
    
    if title:
        todo_manager.add_todo(title, description, priority)'''
                
                new_route = '''    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'Medium')
    due_date = request.form.get('due_date', '').strip() or None
    
    if title:
        todo_manager.add_todo(title, description, priority, due_date)'''
                
                content = content.replace(old_route, new_route)
                
                # Write the modified content back
                with open(self.app_file, 'w') as f:
                    f.write(content)
                
                # Create git commit
                self._create_git_commit(f"Add due date feature for {ticket_key}")
                
                return {
                    'status': 'implemented',
                    'message': 'Due date feature added successfully',
                    'changes': ['TodoItem class updated', 'Form updated', 'Routes updated']
                }
            else:
                return {'status': 'error', 'message': 'Could not find TodoItem __init__ method to modify'}
                
        except Exception as e:
            logger.error(f"❌ Error adding due date feature: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _add_category_feature(self, ticket_key: str) -> Dict[str, Any]:
        """Add category functionality to todo items"""
        # Similar implementation for categories
        return {
            'status': 'planned',
            'message': 'Category feature implementation planned',
            'ticket': ticket_key
        }
    
    def _create_feature_branch(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Create a feature branch and implementation plan"""
        try:
            branch_name = f"feature/{ticket_key.lower()}-{datetime.now().strftime('%Y%m%d')}"
            
            # Create branch
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            
            # Create implementation file
            impl_file = f"feature_implementation_{ticket_key}.md"
            with open(impl_file, 'w') as f:
                f.write(f"# Feature Implementation: {ticket_key}\n\n")
                f.write(f"## Analysis\n{json.dumps(analysis, indent=2)}\n\n")
                f.write(f"## Implementation Status\nBranch created: {branch_name}\n")
                f.write(f"Ready for manual implementation\n")
            
            # Commit the plan
            subprocess.run(['git', 'add', impl_file], check=True)
            subprocess.run(['git', 'commit', '-m', f"Add implementation plan for {ticket_key}"], check=True)
            
            return {
                'status': 'branch_created',
                'message': f'Feature branch {branch_name} created with implementation plan',
                'branch_name': branch_name,
                'plan_file': impl_file
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating feature branch: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _modify_ui(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Modify UI based on analysis"""
        return {
            'status': 'ui_plan_created',
            'message': 'UI modification plan created - requires manual implementation',
            'ticket': ticket_key
        }
    
    def _add_enhancement(self, analysis: Dict[str, Any], ticket_key: str) -> Dict[str, Any]:
        """Add enhancement based on analysis"""
        return {
            'status': 'enhancement_planned',
            'message': 'Enhancement planned for implementation',
            'ticket': ticket_key
        }
    
    def _create_git_commit(self, message: str):
        """Create a git commit with the changes"""
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', message], check=True)
            logger.info(f"✅ Git commit created: {message}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"⚠️ Git commit failed: {e}")

class UnifiedAutomationSystem:
    """Main automation system handling both Jira and GitHub webhooks"""
    
    def __init__(self):
        self.openai_client = self._setup_openai()
        self.code_modifier = TodoCodeModifier()
        self.jira_secret = os.getenv('JIRA_WEBHOOK_SECRET', '')
        self.github_secret = os.getenv('GITHUB_WEBHOOK_SECRET', '')
        
    def _setup_openai(self) -> Optional[OpenAI]:
        """Setup OpenAI client"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                return OpenAI(api_key=api_key)
            else:
                logger.warning("⚠️ OpenAI API key not found")
                return None
        except Exception as e:
            logger.error(f"❌ OpenAI setup failed: {e}")
            return None
    
    def analyze_jira_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Jira ticket using AI"""
        try:
            summary = ticket_data.get('summary', '')
            description = ticket_data.get('description', '')
            issue_type = ticket_data.get('issuetype', {}).get('name', '')
            
            if self.openai_client:
                return self._ai_analyze_ticket(summary, description, issue_type)
            else:
                return self._fallback_analyze_ticket(summary, description, issue_type)
                
        except Exception as e:
            logger.error(f"❌ Ticket analysis error: {e}")
            return {'error': str(e)}
    
    def _ai_analyze_ticket(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
        """AI-powered ticket analysis"""
        try:
            prompt = f"""
            Analyze this Jira ticket for a Todo application and provide implementation guidance:
            
            Summary: {summary}
            Description: {description}
            Type: {issue_type}
            
            Current Todo App Features:
            - Add/edit/delete todos with title, description, priority
            - Mark todos complete/incomplete
            - View statistics (total, completed, pending)
            - Simple web interface with forms
            - JSON persistence
            
            Respond with JSON containing:
            {{
                "change_type": "feature|bugfix|ui|enhancement",
                "complexity": "simple|medium|complex",
                "implementation_approach": "automatic|assisted|manual",
                "code_changes": "specific description of what to implement",
                "files_to_modify": ["todo_app.py"],
                "implementation_steps": ["step1", "step2", "step3"],
                "testing_notes": "how to test the changes"
            }}
            
            For simple features like "add due date" or "add categories", use implementation_approach: "automatic"
            """
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                result = response.choices[0].message.content
                if result:
                    try:
                        return json.loads(result)
                    except json.JSONDecodeError:
                        return {"ai_response": result, "change_type": "manual_review"}
                else:
                    return {"change_type": "manual_review", "message": "Empty AI response"}
            else:
                return self._fallback_analyze_ticket(summary, description, issue_type)
                
        except Exception as e:
            logger.error(f"❌ AI analysis failed: {e}")
            return self._fallback_analyze_ticket(summary, description, issue_type)
    
    def _fallback_analyze_ticket(self, summary: str, description: str, issue_type: str) -> Dict[str, Any]:
        """Fallback analysis without AI"""
        change_type = "enhancement"
        implementation_approach = "manual"
        
        # Simple keyword detection
        summary_lower = summary.lower()
        if any(word in summary_lower for word in ['bug', 'fix', 'error', 'broken']):
            change_type = "bugfix"
        elif any(word in summary_lower for word in ['ui', 'interface', 'design', 'style']):
            change_type = "ui"
        elif any(word in summary_lower for word in ['add', 'new', 'feature']):
            change_type = "feature"
            # Check for simple features we can auto-implement
            if any(word in summary_lower for word in ['due date', 'deadline', 'category', 'tag']):
                implementation_approach = "automatic"
        
        return {
            "change_type": change_type,
            "complexity": "medium",
            "implementation_approach": implementation_approach,
            "code_changes": f"Implement: {summary}",
            "files_to_modify": ["todo_app.py"],
            "implementation_steps": [
                f"Analyze requirement: {summary}",
                "Modify todo_app.py",
                "Test changes",
                "Commit and push"
            ],
            "testing_notes": "Test todo functionality manually"
        }
    
    def process_jira_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Jira webhook and trigger automation"""
        try:
            webhook_event = payload.get('webhookEvent', '')
            
            if webhook_event != 'jira:issue_created':
                return {'status': 'ignored', 'reason': f'Event {webhook_event} not processed'}
            
            issue = payload.get('issue', {})
            fields = issue.get('fields', {})
            issue_key = issue.get('key', '')
            
            logger.info(f"🎫 Processing Jira issue: {issue_key}")
            
            # Extract ticket data
            ticket_data = {
                'key': issue_key,
                'summary': fields.get('summary', ''),
                'description': fields.get('description', ''),
                'issuetype': fields.get('issuetype', {}),
                'priority': fields.get('priority', {})
            }
            
            # Analyze ticket
            analysis = self.analyze_jira_ticket(ticket_data)
            
            # Implement changes if possible
            implementation_result = {'status': 'analysis_only'}
            
            if analysis.get('implementation_approach') == 'automatic':
                logger.info(f"🤖 Attempting automatic implementation for {issue_key}")
                implementation_result = self.code_modifier.implement_feature(analysis, issue_key)
                
                # If implementation was successful, push to GitHub
                if implementation_result.get('status') in ['implemented', 'branch_created']:
                    try:
                        subprocess.run(['git', 'push', 'origin', '--all'], check=True)
                        logger.info(f"🚀 Changes pushed to GitHub for {issue_key}")
                        implementation_result['pushed_to_github'] = True
                    except subprocess.CalledProcessError as e:
                        logger.warning(f"⚠️ Failed to push to GitHub: {e}")
                        implementation_result['pushed_to_github'] = False
            
            return {
                'status': 'processed',
                'issue_key': issue_key,
                'analysis': analysis,
                'implementation': implementation_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Jira webhook processing error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def process_github_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process GitHub webhook for deployment"""
        try:
            ref = payload.get('ref', '')
            repository = payload.get('repository', {}).get('name', 'Unknown')
            
            # Only process pushes to main branch
            if ref != 'refs/heads/main':
                return {'status': 'ignored', 'reason': f'Not main branch: {ref}'}
            
            logger.info(f"🔄 GitHub push received for {repository}")
            
            # Pull latest changes
            try:
                subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
                logger.info("✅ Successfully pulled latest changes")
                
                # Restart the application (for deployment)
                # In Replit, changes are automatically reflected
                return {
                    'status': 'deployed',
                    'message': 'Changes pulled and deployed successfully',
                    'repository': repository,
                    'timestamp': datetime.now().isoformat()
                }
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Git pull failed: {e}")
                return {'status': 'error', 'message': f'Deployment failed: {e}'}
                
        except Exception as e:
            logger.error(f"❌ GitHub webhook processing error: {e}")
            return {'status': 'error', 'message': str(e)}

# Create Flask app
app = Flask(__name__)
automation_system = UnifiedAutomationSystem()

@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    """Jira webhook endpoint"""
    try:
        payload = request.get_json()
        result = automation_system.process_jira_webhook(payload)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"❌ Jira webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/github-webhook', methods=['POST'])  
def github_webhook():
    """GitHub webhook endpoint"""
    try:
        payload = request.get_json()
        result = automation_system.process_github_webhook(payload)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"❌ GitHub webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/automation/status')
def automation_status():
    """Get automation system status"""
    return jsonify({
        'status': 'running',
        'services': {
            'jira_webhook': '/jira-webhook',
            'github_webhook': '/github-webhook',
            'ai_enabled': automation_system.openai_client is not None,
            'code_modifier': 'active'
        },
        'endpoints': {
            'jira_webhook_url': f"{os.getenv('REPL_URL', 'your-repl-url')}/jira-webhook",
            'github_webhook_url': f"{os.getenv('REPL_URL', 'your-repl-url')}/github-webhook"
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test/jira', methods=['POST'])
def test_jira():
    """Test Jira automation with sample ticket"""
    sample_ticket = {
        "webhookEvent": "jira:issue_created",
        "issue": {
            "key": "TODO-001",
            "fields": {
                "summary": "Add due date feature to todo items",
                "description": "Users should be able to set due dates for their todo items and see overdue tasks highlighted in the interface",
                "issuetype": {"name": "Feature"},
                "priority": {"name": "Medium"}
            }
        }
    }
    
    result = automation_system.process_jira_webhook(sample_ticket)
    return jsonify(result)

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'automation_system': 'running',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🤖 Starting Unified Automation System...")
    print("🎫 Jira webhook: http://localhost:8000/jira-webhook")
    print("🔗 GitHub webhook: http://localhost:8000/github-webhook")
    print("📊 Status: http://localhost:8000/automation/status")
    app.run(host='0.0.0.0', port=8000, debug=True)