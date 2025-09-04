#!/usr/bin/env python3
"""
Production Application Entry Point
Combines both Todo App and Automation System for deployment on port 5000
"""

import os
from flask import Flask, request, redirect, url_for, render_template_string
from todo_app import TodoManager
from unified_automation import UnifiedAutomationSystem

# Create a combined Flask application
app = Flask(__name__)

# Initialize managers
todo_manager = TodoManager()
automation_system = UnifiedAutomationSystem()

# Todo App routes
@app.route('/')
def index():
    """Main todo list page"""
    stats = todo_manager.get_stats()
    todos = todo_manager.get_all_todos()
    
    # Simple HTML template embedded in the response
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Todo App</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f4f4f4; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
            .stat {{ background: #e8f4fd; padding: 10px; border-radius: 4px; text-align: center; }}
            .todo-item {{ background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007cba; }}
            .todo-item.completed {{ opacity: 0.6; border-left-color: #28a745; }}
            .form-section {{ background: #f4f4f4; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            input, textarea, select, button {{ padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }}
            button {{ background: #007cba; color: white; cursor: pointer; }}
            button:hover {{ background: #005a87; }}
            .delete-btn {{ background: #dc3545; }}
            .delete-btn:hover {{ background: #c82333; }}
            .automation-info {{ background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🗒️ Todo App</h1>
            <p>Manage your tasks efficiently</p>
            <div class="automation-info">
                <small>🤖 Automation system active - <a href="/automation/status">Status</a></small>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <h3>Total</h3>
                <p>{stats['total']}</p>
            </div>
            <div class="stat">
                <h3>Pending</h3>
                <p>{stats['pending']}</p>
            </div>
            <div class="stat">
                <h3>Completed</h3>
                <p>{stats['completed']}</p>
            </div>
            <div class="stat">
                <h3>Completion Rate</h3>
                <p>{stats['completion_rate']}%</p>
            </div>
        </div>
        
        <div class="form-section">
            <h3>Add New Todo</h3>
            <form action="/add" method="post">
                <input type="text" name="title" placeholder="Todo title" required style="width: 300px;">
                <textarea name="description" placeholder="Description (optional)" style="width: 300px; height: 60px;"></textarea>
                <select name="priority">
                    <option value="Low">Low Priority</option>
                    <option value="Medium" selected>Medium Priority</option>
                    <option value="High">High Priority</option>
                </select>
                <button type="submit">Add Todo</button>
            </form>
        </div>
        
        <div class="todos">
            <h3>Your Todos</h3>
    """
    
    for todo in todos:
        checked = "checked" if todo.completed else ""
        completed_class = "completed" if todo.completed else ""
        
        html += f"""
            <div class="todo-item {completed_class}">
                <form action="/toggle/{todo.id}" method="post" style="display: inline;">
                    <input type="checkbox" {checked} onchange="this.form.submit()">
                </form>
                <strong>{todo.title}</strong>
                <span style="color: #666;">({todo.priority})</span>
                <br>
                <small>{todo.description}</small>
                <br>
                <small style="color: #999;">Created: {todo.created_at[:10]}</small>
                <form action="/delete/{todo.id}" method="post" style="display: inline; float: right;">
                    <button type="submit" class="delete-btn" onclick="return confirm('Delete this todo?')">Delete</button>
                </form>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html

@app.route('/add', methods=['POST'])
def add_todo():
    """Add a new todo"""
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'Medium')
    
    if title:
        todo_manager.add_todo(title, description, priority)
    
    return redirect(url_for('index'))

@app.route('/toggle/<todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    """Toggle todo completion status"""
    todo = todo_manager.get_todo(todo_id)
    if todo:
        todo_manager.update_todo(todo_id, completed=not todo.completed)
    
    return redirect(url_for('index'))

@app.route('/delete/<todo_id>', methods=['POST'])
def delete_todo(todo_id):
    """Delete a todo"""
    todo_manager.delete_todo(todo_id)
    return redirect(url_for('index'))

# Automation System routes
@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    """Jira webhook endpoint"""
    try:
        payload = request.get_json()
        result = automation_system.process_jira_webhook(payload)
        return result, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    """GitHub webhook endpoint"""  
    try:
        payload = request.get_json()
        result = automation_system.process_github_webhook(payload)
        return result, 200
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/automation/status')
def automation_status():
    """Automation system status"""
    from datetime import datetime
    return {
        'status': 'running',
        'services': {
            'todo_app': 'active',
            'jira_webhook': '/jira-webhook',
            'github_webhook': '/github-webhook',
            'ai_enabled': automation_system.openai_client is not None,
            'code_modifier': 'active'
        },
        'endpoints': {
            'main_app': '/',
            'jira_webhook_url': f"{os.getenv('REPL_URL', 'your-repl-url')}/jira-webhook",
            'github_webhook_url': f"{os.getenv('REPL_URL', 'your-repl-url')}/github-webhook"
        },
        'timestamp': datetime.now().isoformat()
    }

@app.route('/test/jira', methods=['POST'])
def test_jira():
    """Test Jira automation"""
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
    return result

@app.route('/health')
def health():
    """Health check endpoint"""
    from datetime import datetime
    return {
        'status': 'healthy',
        'automation_system': 'running',
        'todo_count': len(todo_manager.todos),
        'timestamp': datetime.now().isoformat()
    }

# Add Cache-Control headers for development
@app.after_request
def after_request(response):
    """Add no-cache headers to prevent caching issues"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache" 
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    print("🚀 Starting Production Unified Application...")
    print("📝 Todo App: http://localhost:5000")
    print("🎫 Jira webhook: http://localhost:5000/jira-webhook")
    print("🔗 GitHub webhook: http://localhost:5000/github-webhook")
    print("📊 Status: http://localhost:5000/automation/status")
    
    # For development, use Flask dev server
    app.run(host='0.0.0.0', port=5000, debug=True)