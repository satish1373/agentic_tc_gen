
import os

print(f"Repl ID: {os.environ.get('REPL_ID', 'Not available')}")
print(f"Repl Owner: {os.environ.get('REPL_OWNER', 'Not available')}")
print(f"Home Directory: {os.environ.get('HOME', 'Not available')}")

# The Repl URL can be constructed, but the exact format depends on your specific setup
# Check your browser's address bar for the exact URL format
print("\nTo find your exact Repl URL:")
print("1. Look at your browser's address bar")
print("2. The format is: https://[repl-name].[username].replit.dev")
print("3. Your Jira webhook URL will be: [that-url]/jira-webhook")
