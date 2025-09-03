#!/usr/bin/env python3
"""
Simple Todo Application
A clean foundation for managing tasks and todo items
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

app = Flask(__name__)

class TodoItem:
    """Represents a single todo item"""
    
    def __init__(self, id: str, title: str, description: str = "", completed: bool = False, 
                 priority: str = "Medium", created_at: Optional[str] = None):
        self.id = id
        self.title = title
        self.description = description
        self.completed = completed
        self.priority = priority
        self.created_at = created_at if created_at is not None else datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'priority': self.priority,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data.get('description', ''),
            completed=data.get('completed', False),
            priority=data.get('priority', 'Medium'),
            created_at=data.get('created_at')
        )

class TodoManager:
    """Manages todo items and persistence"""
    
    def __init__(self, data_file: str = "todos.json"):
        self.data_file = data_file
        self.todos: List[TodoItem] = []
        self.load_todos()
    
    def load_todos(self):
        """Load todos from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.todos = [TodoItem.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error loading todos: {e}")
            self.todos = []
    
    def save_todos(self):
        """Save todos to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump([todo.to_dict() for todo in self.todos], f, indent=2)
        except Exception as e:
            print(f"Error saving todos: {e}")
    
    def add_todo(self, title: str, description: str = "", priority: str = "Medium") -> TodoItem:
        """Add a new todo item"""
        todo_id = str(len(self.todos) + 1).zfill(3)
        todo = TodoItem(todo_id, title, description, priority=priority)
        self.todos.append(todo)
        self.save_todos()
        return todo
    
    def get_todo(self, todo_id: str) -> Optional[TodoItem]:
        """Get a todo by ID"""
        for todo in self.todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def update_todo(self, todo_id: str, **kwargs) -> Optional[TodoItem]:
        """Update a todo item"""
        todo = self.get_todo(todo_id)
        if todo:
            for key, value in kwargs.items():
                if hasattr(todo, key):
                    setattr(todo, key, value)
            todo.updated_at = datetime.now().isoformat()
            self.save_todos()
        return todo
    
    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo item"""
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                del self.todos[i]
                self.save_todos()
                return True
        return False
    
    def get_all_todos(self, filter_completed: Optional[bool] = None) -> List[TodoItem]:
        """Get all todos, optionally filtered by completion status"""
        if filter_completed is None:
            return self.todos
        return [todo for todo in self.todos if todo.completed == filter_completed]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get todo statistics"""
        total = len(self.todos)
        completed = len([t for t in self.todos if t.completed])
        pending = total - completed
        
        return {
            'total': total,
            'completed': completed,
            'pending': pending,
            'completion_rate': round((completed / total * 100) if total > 0 else 0, 1)
        }

# Initialize todo manager
todo_manager = TodoManager()

# Routes
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🗒️ Todo App</h1>
            <p>Manage your tasks efficiently</p>
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

@app.route('/api/todos', methods=['GET'])
def api_get_todos():
    """API endpoint to get all todos"""
    todos = todo_manager.get_all_todos()
    return jsonify([todo.to_dict() for todo in todos])

@app.route('/api/todos', methods=['POST'])
def api_add_todo():
    """API endpoint to add a todo"""
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
    
    todo = todo_manager.add_todo(
        title=data['title'],
        description=data.get('description', ''),
        priority=data.get('priority', 'Medium')
    )
    
    return jsonify(todo.to_dict()), 201

@app.route('/api/stats')
def api_get_stats():
    """API endpoint to get todo statistics"""
    return jsonify(todo_manager.get_stats())

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'todos_count': len(todo_manager.todos)
    })

if __name__ == '__main__':
    print("🚀 Starting Todo App...")
    print("📝 Access your todos at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)