
from flask import Flask, request, jsonify
import requests
import json
import os
from dotenv import load_dotenv
from jira import JIRA
from agentic_test_generator_1 import AgenticTestCaseGenerator
import subprocess
import tempfile
import pandas as pd

# Initialize the enhanced generator
enhanced_generator = AgenticTestCaseGenerator()

class ReplitAIIntegration:
    """Integration with Replit AI Assistant for intelligent actions"""
    
    def __init__(self):
        self.action_handlers = {
            "Bug": self.handle_bug_ticket,
            "Story": self.handle_story_ticket, 
            "Task": self.handle_task_ticket,
            "Epic": self.handle_epic_ticket,
            "Feature": self.handle_feature_ticket,
            "New Feature": self.handle_feature_ticket,
            "Improvement": self.handle_improvement_ticket
        }
    
    def analyze_ticket_and_take_action(self, issue_key: str, summary: str, issue_type: str, description: str = "") -> dict:
        """Analyze Jira ticket and determine appropriate action using Replit AI"""
        
        # Create intelligent prompt for Replit AI
        ai_prompt = self.create_ai_prompt(issue_key, summary, issue_type, description)
        
        # Get action recommendations from AI
        action_plan = self.get_ai_recommendations(ai_prompt, issue_key, issue_type)
        
        # Execute the recommended actions
        results = self.execute_action_plan(action_plan, issue_key, summary, issue_type, description)
        
        return {
            "issue_key": issue_key,
            "ai_prompt": ai_prompt,
            "action_plan": action_plan,
            "results": results,
            "status": "completed"
        }
    
    def create_ai_prompt(self, issue_key: str, summary: str, issue_type: str, description: str) -> str:
        """Create intelligent prompt for Replit AI Assistant"""
        
        base_prompt = f"""
🤖 **Replit AI Assistant - Jira Integration Analysis**

**Ticket Details:**
- **Issue Key**: {issue_key}
- **Type**: {issue_type}
- **Summary**: {summary}
- **Description**: {description[:500]}{'...' if len(description) > 500 else ''}

**Analysis Request:**
Based on this Jira ticket, please analyze and recommend appropriate actions:

1. **Primary Action**: What should be the main development/testing action?
2. **Code Generation**: Should we generate any code files? If yes, what type?
3. **Test Strategy**: What testing approach is most suitable?
4. **Documentation**: What documentation should be created or updated?
5. **Dependencies**: Are there any dependencies or prerequisites to consider?

**Context-Specific Analysis:**
"""
        
        if issue_type == "Bug":
            base_prompt += """
- Focus on root cause analysis and regression testing
- Consider debugging steps and error reproduction
- Identify affected components and potential side effects
"""
        elif issue_type == "Story":
            base_prompt += """
- Focus on acceptance criteria and user journey
- Consider end-to-end testing scenarios
- Identify integration points and user experience aspects
"""
        elif issue_type == "Task":
            base_prompt += """
- Focus on implementation steps and technical requirements
- Consider code structure and architectural decisions
- Identify testing and validation approaches
"""
        elif issue_type in ["Feature", "New Feature"]:
            base_prompt += """
- Focus on feature specification and implementation plan
- Consider API design and user interface requirements
- Identify comprehensive testing scenarios including edge cases
"""
        
        base_prompt += f"""

**Expected Output Format:**
Please provide structured recommendations in this format:
1. **Action Type**: [code_generation|test_creation|documentation|analysis]
2. **Priority**: [High|Medium|Low]
3. **Estimated Effort**: [Small|Medium|Large]
4. **Recommended Files**: List of files to create/modify
5. **Implementation Steps**: Step-by-step action plan
6. **Testing Requirements**: Specific test scenarios needed

**Current Project Context**: Python Flask application with Jira integration and AI-powered test generation capabilities.
"""
        
        return base_prompt
    
    def get_ai_recommendations(self, prompt: str, issue_key: str, issue_type: str) -> dict:
        """Get recommendations from Replit AI (simulated for now)"""
        
        # In a real implementation, this would call Replit's AI API
        # For now, we'll provide intelligent defaults based on issue type
        
        default_actions = {
            "Bug": {
                "action_type": "test_creation",
                "priority": "High",
                "estimated_effort": "Medium",
                "recommended_files": [
                    f"bug_reproduction_{issue_key.lower()}.py",
                    f"regression_tests_{issue_key.lower()}.json"
                ],
                "implementation_steps": [
                    "Generate comprehensive test cases for bug reproduction",
                    "Create regression test suite",
                    "Document bug analysis and fix verification steps"
                ],
                "testing_requirements": [
                    "Reproduce the reported bug",
                    "Test edge cases around the bug",
                    "Verify fix doesn't break existing functionality"
                ]
            },
            "Story": {
                "action_type": "test_creation",
                "priority": "High", 
                "estimated_effort": "Large",
                "recommended_files": [
                    f"acceptance_tests_{issue_key.lower()}.json",
                    f"user_journey_{issue_key.lower()}.py"
                ],
                "implementation_steps": [
                    "Generate acceptance criteria test cases",
                    "Create user journey test scenarios",
                    "Document feature requirements and validation steps"
                ],
                "testing_requirements": [
                    "Test happy path user scenarios",
                    "Validate acceptance criteria",
                    "Test integration with existing features"
                ]
            },
            "Task": {
                "action_type": "code_generation",
                "priority": "Medium",
                "estimated_effort": "Medium", 
                "recommended_files": [
                    f"implementation_{issue_key.lower()}.py",
                    f"unit_tests_{issue_key.lower()}.json"
                ],
                "implementation_steps": [
                    "Generate implementation scaffolding",
                    "Create unit test cases",
                    "Document technical approach and considerations"
                ],
                "testing_requirements": [
                    "Unit test individual components",
                    "Integration test with existing system",
                    "Validate technical requirements"
                ]
            },
            "Feature": {
                "action_type": "code_generation",
                "priority": "High",
                "estimated_effort": "Large",
                "recommended_files": [
                    f"feature_{issue_key.lower()}.py",
                    f"feature_tests_{issue_key.lower()}.json",
                    f"api_spec_{issue_key.lower()}.json"
                ],
                "implementation_steps": [
                    "Generate feature implementation code",
                    "Create comprehensive test suite",
                    "Document API specifications and usage examples"
                ],
                "testing_requirements": [
                    "Test all feature functionality",
                    "Test API endpoints and responses", 
                    "Test feature integration and performance"
                ]
            }
        }
        
        return default_actions.get(issue_type, default_actions["Task"])
    
    def execute_action_plan(self, action_plan: dict, issue_key: str, summary: str, issue_type: str, description: str) -> dict:
        """Execute the AI-recommended action plan"""
        
        results = {
            "files_created": [],
            "actions_completed": [],
            "errors": []
        }
        
        try:
            # Execute based on action type
            if action_plan["action_type"] == "test_creation":
                test_results = self.generate_intelligent_test_cases(issue_key, summary, issue_type, description)
                results["files_created"].extend(test_results.get("files", []))
                results["actions_completed"].append("Generated intelligent test cases")
                
            elif action_plan["action_type"] == "code_generation":
                code_results = self.generate_code_scaffolding(issue_key, summary, issue_type, action_plan)
                results["files_created"].extend(code_results.get("files", []))
                results["actions_completed"].append("Generated code scaffolding")
                
            # Always generate documentation
            doc_results = self.generate_documentation(issue_key, summary, issue_type, action_plan)
            results["files_created"].extend(doc_results.get("files", []))
            results["actions_completed"].append("Generated documentation")
            
        except Exception as e:
            results["errors"].append(f"Error executing action plan: {str(e)}")
        
        return results
    
    def generate_intelligent_test_cases(self, issue_key: str, summary: str, issue_type: str, description: str) -> dict:
        """Generate test cases using the enhanced generator"""
        
        try:
            # Use existing test case generator with enhanced context
            enhanced_generator = AgenticTestCaseGenerator()
            requirements = [(issue_key, f"{summary} - {description}")]
            test_cases = enhanced_generator.generate_test_cases(requirements)
            
            filename = f"ai_generated_tests_{issue_key.lower()}.json"
            enhanced_generator.export_to_json(test_cases, filename)
            
            return {
                "files": [filename],
                "test_count": len(test_cases),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "files": [],
                "test_count": 0,
                "status": "error",
                "error": str(e)
            }
    
    def generate_code_scaffolding(self, issue_key: str, summary: str, issue_type: str, action_plan: dict) -> dict:
        """Generate code scaffolding based on ticket analysis"""
        
        files_created = []
        
        try:
            # Generate Python implementation file
            impl_filename = f"implementation_{issue_key.lower()}.py"
            impl_content = self.create_implementation_template(issue_key, summary, issue_type)
            
            with open(impl_filename, 'w', encoding='utf-8') as f:
                f.write(impl_content)
            files_created.append(impl_filename)
            
            # Generate API specification if it's a feature
            if issue_type in ["Feature", "New Feature", "Story"]:
                api_filename = f"api_spec_{issue_key.lower()}.json"
                api_content = self.create_api_specification(issue_key, summary)
                
                with open(api_filename, 'w', encoding='utf-8') as f:
                    f.write(api_content)
                files_created.append(api_filename)
            
            return {
                "files": files_created,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "files": files_created,
                "status": "error", 
                "error": str(e)
            }
    
    def generate_documentation(self, issue_key: str, summary: str, issue_type: str, action_plan: dict) -> dict:
        """Generate comprehensive documentation"""
        
        try:
            doc_filename = f"ai_analysis_{issue_key.lower()}.md"
            doc_content = f"""# AI Analysis Report - {issue_key}

## Ticket Information
- **Issue Key**: {issue_key}
- **Type**: {issue_type}
- **Summary**: {summary}
- **Analysis Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## AI Recommendations
- **Action Type**: {action_plan['action_type']}
- **Priority**: {action_plan['priority']}
- **Estimated Effort**: {action_plan['estimated_effort']}

## Recommended Files
{chr(10).join(f'- {file}' for file in action_plan['recommended_files'])}

## Implementation Steps
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(action_plan['implementation_steps']))}

## Testing Requirements
{chr(10).join(f'- {req}' for req in action_plan['testing_requirements'])}

## Next Actions
Based on this analysis, the following actions have been automatically initiated:
1. Test case generation using AI-powered analysis
2. Code scaffolding creation (if applicable)
3. Documentation generation
4. Jira ticket update with findings

---
*Generated automatically by Replit AI Integration*
"""
            
            with open(doc_filename, 'w', encoding='utf-8') as f:
                f.write(doc_content)
                
            return {
                "files": [doc_filename],
                "status": "success"
            }
            
        except Exception as e:
            return {
                "files": [],
                "status": "error",
                "error": str(e)
            }
    
    def create_implementation_template(self, issue_key: str, summary: str, issue_type: str) -> str:
        """Create implementation template based on issue type"""
        
        template = f'''"""
Implementation for {issue_key}: {summary}
Generated automatically by Replit AI Integration
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class {issue_key.replace("-", "_")}Implementation:
    """
    Implementation class for {issue_key}
    
    Issue Type: {issue_type}
    Summary: {summary}
    """
    
    def __init__(self):
        self.issue_key = "{issue_key}"
        self.created_at = datetime.now()
        logger.info(f"Initialized implementation for {{self.issue_key}}")
    
    def execute(self) -> Dict[str, Any]:
        """
        Main execution method for {issue_key}
        
        Returns:
            Dict containing execution results
        """
        try:
            logger.info(f"Starting execution for {{self.issue_key}}")
            
            # TODO: Implement actual functionality based on ticket requirements
            result = {{
                "status": "completed",
                "issue_key": self.issue_key,
                "execution_time": datetime.now(),
                "message": "Implementation placeholder - customize based on requirements"
            }}
            
            logger.info(f"Successfully executed {{self.issue_key}}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing {{self.issue_key}}: {{str(e)}}")
            raise
    
    def validate(self) -> bool:
        """
        Validate implementation meets requirements
        
        Returns:
            bool: True if validation passes
        """
        # TODO: Add validation logic based on acceptance criteria
        return True

# Usage example
if __name__ == "__main__":
    implementation = {issue_key.replace("-", "_")}Implementation()
    
    if implementation.validate():
        result = implementation.execute()
        print(f"Implementation result: {{result}}")
    else:
        print("Validation failed")
'''
        
        return template
    
    def create_api_specification(self, issue_key: str, summary: str) -> str:
        """Create API specification for feature tickets"""
        
        api_spec = {
            "issue_key": issue_key,
            "summary": summary,
            "api_version": "1.0",
            "generated_at": pd.Timestamp.now().isoformat(),
            "endpoints": [
                {
                    "path": f"/api/v1/{issue_key.lower()}",
                    "method": "GET",
                    "description": f"Get information for {summary}",
                    "parameters": [],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "data": {"type": "object"},
                                    "message": {"type": "string"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad Request",
                            "schema": {
                                "type": "object", 
                                "properties": {
                                    "error": {"type": "string"},
                                    "message": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                {
                    "path": f"/api/v1/{issue_key.lower()}",
                    "method": "POST",
                    "description": f"Create or update {summary}",
                    "parameters": [
                        {
                            "name": "data",
                            "in": "body",
                            "required": True,
                            "schema": {"type": "object"}
                        }
                    ],
                    "responses": {
                        "201": {"description": "Created successfully"},
                        "400": {"description": "Invalid input"},
                        "500": {"description": "Server error"}
                    }
                }
            ]
        }
        
        return json.dumps(api_spec, indent=2)
    
    def handle_bug_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle bug-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Bug", description)
    
    def handle_story_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle story-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Story", description)
    
    def handle_task_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle task-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Task", description)
    
    def handle_epic_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle epic-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Epic", description)
    
    def handle_feature_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle feature-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Feature", description)
    
    def handle_improvement_ticket(self, issue_key: str, summary: str, description: str) -> dict:
        """Handle improvement-specific actions"""
        return self.analyze_ticket_and_take_action(issue_key, summary, "Improvement", description)

# Initialize the AI integration
replit_ai = ReplitAIIntegration()

def generate_test_cases_for_jira_issue(issue_key: str, summary: str, issue_type: str) -> str:
    """Generate test cases for Jira issue using enhanced generator"""
    try:
        # Create a requirement from the Jira issue
        requirements = [(issue_key, f"{summary} - Type: {issue_type}")]
        
        # Generate test cases
        test_cases = enhanced_generator.generate_test_cases(requirements)
        
        # Export to JSON file
        filename = f"jira_generated_test_cases_{issue_key}.json"
        enhanced_generator.export_to_json(test_cases, filename)
        
        # Create summary for Jira comment
        summary_text = f"Generated {len(test_cases)} test cases for {issue_key}:\n\n"
        
        for i, tc in enumerate(test_cases[:5]):  # Show first 5
            summary_text += f"{i+1}. **{tc.title}** ({tc.test_type.value})\n"
            summary_text += f"   - Priority: {tc.priority}\n"
            summary_text += f"   - Expected: {tc.expected_result[:100]}...\n\n"
        
        if len(test_cases) > 5:
            summary_text += f"... and {len(test_cases) - 5} more test cases in {filename}"
        
        return summary_text
        
    except Exception as e:
        return f"Error generating test cases: {str(e)}"

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
            if issue_type in ['Bug', 'Task', 'Story', 'Feature', 'New Feature', 'Epic', 'Improvement']:
                print(f"🚀 Triggering AI-powered analysis for {issue_type}")
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
    """Trigger AI-powered analysis and action taking"""
    try:
        print(f"🤖 Triggering Replit AI integration for {issue_key}")
        print(f"📋 Issue: {summary}")
        print(f"🏷️ Type: {issue_type}")
        
        # Get additional issue details if Jira client is available
        description = ""
        if jira:
            try:
                issue = jira.issue(issue_key)
                description = issue.fields.description or ""
                print(f"📄 Retrieved issue description: {len(description)} characters")
            except Exception as e:
                print(f"⚠️ Could not retrieve issue details: {e}")
        
        # Use Replit AI integration for intelligent action taking
        ai_results = replit_ai.analyze_ticket_and_take_action(
            issue_key, summary, issue_type, description
        )
        
        print(f"🎯 AI Analysis completed for {issue_key}")
        print(f"📊 Actions completed: {len(ai_results['results']['actions_completed'])}")
        print(f"📁 Files created: {len(ai_results['results']['files_created'])}")
        
        # Also generate traditional test cases
        test_filename = generate_test_cases_for_jira_issue(issue_key, summary, issue_type)
        
        # Update Jira issue with comprehensive results
        update_jira_issue_with_ai_results(issue_key, ai_results, test_filename)
        
        return ai_results
        
    except Exception as e:
        error_msg = f"Error in AI integration: {str(e)}"
        print(f"❌ {error_msg}")
        # Try to update Jira with error information
        try:
            update_jira_issue(issue_key, None)
        except:
            pass
        return {"error": error_msg}

# Old test case generation functions removed - now using LangGraph AI generator

def update_jira_issue_with_ai_results(issue_key, ai_results, test_filename=None):
    """Update Jira issue with AI analysis and action results"""
    try:
        if not jira:
            print("⚠️ Jira client not available - skipping issue update")
            return
            
        issue = jira.issue(issue_key)
        
        # Create comprehensive comment with AI analysis
        comment_text = f"""
🤖 **Replit AI Assistant - Automatic Analysis & Action Report**

### 📊 Analysis Summary
**Issue**: {issue_key} ({ai_results.get('action_plan', {}).get('action_type', 'Unknown').title()})
**Priority**: {ai_results.get('action_plan', {}).get('priority', 'Medium')}
**Estimated Effort**: {ai_results.get('action_plan', {}).get('estimated_effort', 'Medium')}

### 🚀 Actions Completed
{chr(10).join(f'✅ {action}' for action in ai_results['results']['actions_completed'])}

### 📁 Files Generated
{chr(10).join(f'📄 `{file}`' for file in ai_results['results']['files_created'])}
"""

        if test_filename:
            comment_text += f"""
### 🧪 Test Cases Generated
📄 **Traditional Test Cases**: `{test_filename}`
🤖 **AI-Enhanced Test Scenarios**: Included in generated files
"""

        if ai_results['results'].get('errors'):
            comment_text += f"""
### ⚠️ Errors Encountered
{chr(10).join(f'❌ {error}' for error in ai_results['results']['errors'])}
"""

        comment_text += f"""
### 🔍 AI Analysis Insights
The AI Assistant analyzed this ticket and recommended:
{chr(10).join(f'• {step}' for step in ai_results.get('action_plan', {}).get('implementation_steps', []))}

### 🧪 Testing Strategy
{chr(10).join(f'• {req}' for req in ai_results.get('action_plan', {}).get('testing_requirements', []))}

---
*Automatically generated by Replit AI Integration at {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        jira.add_comment(issue, comment_text)
        print(f"✅ Updated Jira issue {issue_key} with comprehensive AI analysis")
        
        # Add labels based on AI analysis
        try:
            action_type = ai_results.get('action_plan', {}).get('action_type', '')
            priority = ai_results.get('action_plan', {}).get('priority', '')
            
            labels = issue.fields.labels or []
            new_labels = [f"ai-{action_type}", f"priority-{priority.lower()}", "replit-automated"]
            
            for label in new_labels:
                if label not in labels:
                    labels.append(label)
            
            issue.update(fields={"labels": labels})
            print(f"✅ Added AI analysis labels to {issue_key}")
            
        except Exception as e:
            print(f"⚠️ Could not update labels: {e}")
        
    except Exception as e:
        print(f"❌ Error updating Jira issue with AI results: {str(e)}")

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
    <head>
        <title>Replit AI-Powered Jira Integration</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            .endpoint { background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 5px; }
            .feature { background: #e8f4fd; padding: 10px; margin: 5px 0; border-radius: 5px; }
            code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🤖 Replit AI-Powered Jira Integration Server</h1>
        <p><strong>Status:</strong> ✅ Running with AI Assistant Integration</p>
        
        <h2>🔗 Available Endpoints</h2>
        <div class="endpoint">
            <strong>POST /jira-webhook</strong><br>
            Main webhook endpoint for Jira integration with AI analysis
        </div>
        <div class="endpoint">
            <strong>GET /health</strong><br>
            Health check endpoint
        </div>
        <div class="endpoint">
            <strong>GET /test-webhook</strong><br>
            Test endpoint to simulate Jira webhook with AI processing
        </div>
        <div class="endpoint">
            <strong>GET/POST /ai-analyze/&lt;issue_key&gt;</strong><br>
            Manual AI analysis for specific Jira issues
        </div>
        <div class="endpoint">
            <strong>POST /ai-prompt-preview</strong><br>
            Preview AI prompts that would be generated for tickets
        </div>
        
        <h2>🚀 AI-Powered Features</h2>
        <div class="feature">
            <strong>🧠 Intelligent Ticket Analysis</strong><br>
            Automatically analyzes Jira tickets and determines appropriate actions based on issue type and content
        </div>
        <div class="feature">
            <strong>🏗️ Smart Code Generation</strong><br>
            Generates implementation scaffolding, API specifications, and code templates based on ticket requirements
        </div>
        <div class="feature">
            <strong>🧪 Comprehensive Test Creation</strong><br>
            Creates both traditional and AI-enhanced test cases tailored to the specific issue type and requirements
        </div>
        <div class="feature">
            <strong>📚 Automatic Documentation</strong><br>
            Generates analysis reports, implementation guides, and API documentation automatically
        </div>
        <div class="feature">
            <strong>🏷️ Smart Labeling</strong><br>
            Automatically tags Jira issues with AI-generated labels based on analysis results
        </div>
        
        <h2>⚙️ Configuration</h2>
        <p><strong>Webhook URL:</strong> <code>https://workspace.satish73learnin.replit.dev/jira-webhook</code></p>
        <p><strong>Supported Issue Types:</strong> Bug, Story, Task, Epic, Feature, Improvement</p>
        
        <h2>🔑 Required Environment Variables</h2>
        <ul>
            <li><code>OPENAI_API_KEY</code> - For AI-powered analysis</li>
            <li><code>JIRA_URL</code> - Your Jira instance URL</li>
            <li><code>JIRA_USERNAME</code> - Jira username/email</li>
            <li><code>JIRA_API_TOKEN</code> - Jira API token</li>
        </ul>
        
        <h2>📖 Usage Examples</h2>
        <p><strong>Manual Analysis:</strong> GET <code>/ai-analyze/BUG-123</code></p>
        <p><strong>Prompt Preview:</strong> POST <code>/ai-prompt-preview</code> with issue details</p>
        <p><strong>Test Integration:</strong> GET <code>/test-webhook</code></p>
        
        <hr>
        <p><em>Powered by Replit AI Assistant & LangGraph • Last updated: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """</em></p>
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

@app.route('/ai-analyze/<issue_key>', methods=['GET', 'POST'])
def ai_analyze_issue(issue_key):
    """Manual AI analysis endpoint for specific Jira issues"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            summary = data.get('summary', '')
            issue_type = data.get('issue_type', 'Task')
            description = data.get('description', '')
        else:
            # Try to fetch from Jira if available
            if jira:
                try:
                    issue = jira.issue(issue_key)
                    summary = issue.fields.summary
                    issue_type = issue.fields.issuetype.name
                    description = issue.fields.description or ""
                except Exception as e:
                    return jsonify({"error": f"Could not fetch issue from Jira: {str(e)}"}), 400
            else:
                return jsonify({"error": "No issue data provided and Jira client not available"}), 400
        
        print(f"🤖 Manual AI analysis requested for {issue_key}")
        
        # Perform AI analysis
        ai_results = replit_ai.analyze_ticket_and_take_action(
            issue_key, summary, issue_type, description
        )
        
        # Generate test cases too
        test_filename = generate_test_cases_for_jira_issue(issue_key, summary, issue_type)
        ai_results['test_filename'] = test_filename
        
        return jsonify({
            "status": "success",
            "issue_key": issue_key,
            "ai_analysis": ai_results,
            "message": f"AI analysis completed for {issue_key}"
        }), 200
        
    except Exception as e:
        error_msg = f"Error in manual AI analysis: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/ai-prompt-preview', methods=['POST'])
def preview_ai_prompt():
    """Preview the AI prompt that would be generated for a ticket"""
    try:
        data = request.get_json()
        issue_key = data.get('issue_key', 'PREVIEW-001')
        summary = data.get('summary', 'Sample issue summary')
        issue_type = data.get('issue_type', 'Task')
        description = data.get('description', '')
        
        # Generate AI prompt
        ai_prompt = replit_ai.create_ai_prompt(issue_key, summary, issue_type, description)
        
        return jsonify({
            "status": "success",
            "issue_key": issue_key,
            "ai_prompt": ai_prompt,
            "message": "AI prompt preview generated"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Jira LangGraph Webhook Server...")
    print("🔗 Configure your Jira webhook to point to: https://workspace.satish73learnin.replit.dev/jira-webhook")
    print("🤖 LangGraph AI-powered test case generation enabled")
    print("⚠️  Make sure OPENAI_API_KEY is set in Secrets for full AI capabilities")
    
    # Use production-ready settings with proper port configuration
    import os
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 Starting server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
