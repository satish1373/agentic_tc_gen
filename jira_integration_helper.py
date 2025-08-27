
import subprocess
import json
import os

def trigger_existing_generators(issue_key, summary):
    """Trigger existing test case generators when Jira issue is created"""
    
    # Create a temporary requirements file based on Jira issue
    jira_requirement = {
        "id": issue_key,
        "text": summary,
        "priority": "High",
        "category": "Jira Integration"
    }
    
    temp_requirements_file = f"jira_requirement_{issue_key}.json"
    with open(temp_requirements_file, 'w') as f:
        json.dump({"requirements": [jira_requirement]}, f, indent=2)
    
    # Run your existing test generator
    try:
        result = subprocess.run([
            'python', 'fixed_test_generator.py', 
            '--input', temp_requirements_file,
            '--output', f'jira_test_cases_{issue_key}.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Successfully generated test cases for {issue_key}")
        else:
            print(f"Error running test generator: {result.stderr}")
            
    except Exception as e:
        print(f"Error triggering test generator: {str(e)}")
    
    # Clean up temporary file
    if os.path.exists(temp_requirements_file):
        os.remove(temp_requirements_file)
