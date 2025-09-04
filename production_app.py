#!/usr/bin/env python3
"""
Production Application Entry Point
Combines both Todo App and Automation System for deployment on port 5000
"""

import os
from flask import Flask, request, redirect, url_for
from todo_app import app as todo_app, todo_manager
from unified_automation import app as automation_app, automation_system

# Create a combined Flask application
app = Flask(__name__)

# Register Todo App routes
@app.route('/')
def index():
    """Main todo interface"""
    return todo_app.view_functions['index']()

@app.route('/add', methods=['POST'])
def add_todo():
    """Add todo endpoint"""
    return todo_app.view_functions['add_todo']()

@app.route('/complete/<todo_id>')
def complete_todo(todo_id):
    """Complete todo endpoint"""
    return todo_app.view_functions['complete_todo'](todo_id)

@app.route('/uncomplete/<todo_id>')
def uncomplete_todo(todo_id):
    """Uncomplete todo endpoint"""
    return todo_app.view_functions['uncomplete_todo'](todo_id)

@app.route('/edit/<todo_id>')
def edit_todo(todo_id):
    """Edit todo endpoint"""
    return todo_app.view_functions['edit_todo'](todo_id)

@app.route('/update/<todo_id>', methods=['POST'])
def update_todo(todo_id):
    """Update todo endpoint"""
    return todo_app.view_functions['update_todo'](todo_id)

@app.route('/delete/<todo_id>')
def delete_todo(todo_id):
    """Delete todo endpoint"""
    return todo_app.view_functions['delete_todo'](todo_id)

@app.route('/stats')
def stats():
    """Stats endpoint"""
    return todo_app.view_functions['stats']()

# Register Automation System routes
@app.route('/jira-webhook', methods=['POST'])
def jira_webhook():
    """Jira webhook endpoint"""
    return automation_app.view_functions['jira_webhook']()

@app.route('/github-webhook', methods=['POST'])
def github_webhook():
    """GitHub webhook endpoint"""  
    return automation_app.view_functions['github_webhook']()

@app.route('/automation/status')
def automation_status():
    """Automation system status"""
    return automation_app.view_functions['automation_status']()

@app.route('/test/jira', methods=['POST'])
def test_jira():
    """Test Jira automation"""
    return automation_app.view_functions['test_jira']()

@app.route('/health')
def health():
    """Health check endpoint"""
    return automation_app.view_functions['health']()

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