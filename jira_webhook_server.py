#!/usr/bin/env python3
"""
Jira Webhook Server - Entry Point
This file serves as the main entry point for the webhook server.
It imports and runs the unified automation system.
"""

if __name__ == "__main__":
    # Import and run the unified automation system
    from unified_automation import app
    import os
    
    print("🤖 Starting Jira Webhook Server...")
    print("🔗 Redirecting to Unified Automation System...")
    
    # Run the unified automation Flask app
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)