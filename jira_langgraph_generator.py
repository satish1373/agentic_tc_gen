
import re
import json
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
import operator
import os
from dotenv import load_dotenv

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

class TestType(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    EDGE_CASE = "edge_case"
    INTEGRATION = "integration"
    SECURITY = "security"

@dataclass
class TestCase:
    """Represents a single test case"""
    id: str
    title: str
    description: str
    test_type: TestType
    preconditions: List[str]
    test_steps: List[str]
    expected_result: str
    priority: str = "Medium"
    tags: List[str] = None
    risk_level: str = "Medium"
    automation_feasible: bool = True
    jira_issue: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], operator.add]
    jira_issue_key: str
    jira_summary: str
    jira_issue_type: str
    requirements: List[Dict[str, str]]
    parsed_requirements: List[Dict[str, Any]]
    test_cases: List[TestCase]
    analysis_complete: bool
    generation_complete: bool
    validation_complete: bool

class JiraLangGraphGenerator:
    """LangGraph-based test case generator for Jira integration"""
    
    def __init__(self, llm_model: str = "gpt-4o"):
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
            
        self.llm = ChatOpenAI(
            model=llm_model,
            api_key=api_key,
            temperature=0.1
        )
        self.graph = self._build_graph()
        
        # Analysis prompts
        self.jira_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert test analyst. Analyze the given Jira issue and extract:
            1. Core functionality to be tested
            2. Acceptance criteria (inferred from description)
            3. Potential edge cases and error conditions
            4. Risk assessment based on issue type and description
            5. Integration points that need testing
            6. Security considerations if applicable
            
            Issue Type Context:
            - Bug: Focus on regression testing and error scenarios
            - Story: Focus on functional testing and user acceptance
            - Task: Focus on implementation verification and integration
            
            Return your analysis as a structured JSON object with detailed test scenarios."""),
            ("human", "Jira Issue: {issue_key}\nType: {issue_type}\nSummary: {summary}")
        ])
        
        self.test_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert test case designer. Based on the Jira issue analysis, 
            generate comprehensive test cases that cover:
            
            1. Primary functionality testing (positive scenarios)
            2. Error handling and edge cases (negative scenarios)
            3. Boundary value testing
            4. Integration testing if applicable
            5. Security testing if relevant
            
            For each test case, provide:
            - Clear, actionable test steps
            - Specific expected results
            - Realistic preconditions
            - Appropriate priority based on risk
            - Tags for easy categorization
            
            Generate 3-5 test cases per requirement in JSON array format."""),
            ("human", "Analysis: {analysis}\nJira Issue: {issue_key} - {summary}")
        ])
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_jira_issue", self._analyze_jira_issue)
        workflow.add_node("generate_test_cases", self._generate_test_cases)
        workflow.add_node("validate_and_enhance", self._validate_and_enhance)
        workflow.add_node("finalize_output", self._finalize_output)
        
        # Define edges
        workflow.add_edge("analyze_jira_issue", "generate_test_cases")
        workflow.add_edge("generate_test_cases", "validate_and_enhance")
        workflow.add_edge("validate_and_enhance", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_jira_issue")
        
        return workflow.compile()
    
    def _analyze_jira_issue(self, state: AgentState) -> AgentState:
        """Analyze Jira issue using LLM"""
        print(f"🔍 Analyzing Jira issue {state['jira_issue_key']}...")
        
        try:
            analysis_chain = self.jira_analysis_prompt | self.llm
            response = analysis_chain.invoke({
                "issue_key": state["jira_issue_key"],
                "issue_type": state["jira_issue_type"],
                "summary": state["jira_summary"]
            })
            
            # Parse the analysis
            analysis = self._parse_jira_analysis(response.content, state)
            state["parsed_requirements"] = [analysis]
            state["analysis_complete"] = True
            
            state["messages"].append(AIMessage(
                content=f"Analyzed Jira issue {state['jira_issue_key']} - {state['jira_issue_type']}"
            ))
            
        except Exception as e:
            print(f"Error analyzing Jira issue: {e}")
            # Fallback to basic analysis
            analysis = self._basic_jira_analysis(state)
            state["parsed_requirements"] = [analysis]
            state["analysis_complete"] = True
        
        return state
    
    def _generate_test_cases(self, state: AgentState) -> AgentState:
        """Generate test cases using LLM"""
        print("🚀 Generating test cases from Jira issue...")
        
        analysis = state["parsed_requirements"][0]
        all_test_cases = []
        
        try:
            generation_chain = self.test_generation_prompt | self.llm
            response = generation_chain.invoke({
                "analysis": json.dumps(analysis, indent=2),
                "issue_key": state["jira_issue_key"],
                "summary": state["jira_summary"]
            })
            
            # Parse test cases from LLM response
            test_cases = self._parse_test_cases_from_llm(response.content, state)
            all_test_cases.extend(test_cases)
            
        except Exception as e:
            print(f"Error generating test cases: {e}")
            # Fallback to template generation
            test_cases = self._generate_template_test_cases(state)
            all_test_cases.extend(test_cases)
        
        state["test_cases"] = all_test_cases
        state["generation_complete"] = True
        state["messages"].append(AIMessage(content=f"Generated {len(all_test_cases)} test cases"))
        
        return state
    
    def _validate_and_enhance(self, state: AgentState) -> AgentState:
        """Validate and enhance test cases"""
        print("✅ Validating and enhancing test cases...")
        
        enhanced_cases = []
        for test_case in state["test_cases"]:
            # Add Jira traceability
            test_case.jira_issue = state["jira_issue_key"]
            test_case.tags.append(f"jira_{state['jira_issue_key'].lower()}")
            test_case.tags.append(f"{state['jira_issue_type'].lower()}_testing")
            
            # Validate completeness
            if not test_case.test_steps:
                test_case.test_steps = ["Execute test scenario", "Verify expected behavior"]
            
            if not test_case.expected_result:
                test_case.expected_result = f"Jira issue {state['jira_issue_key']} requirements are satisfied"
            
            enhanced_cases.append(test_case)
        
        state["test_cases"] = enhanced_cases
        state["validation_complete"] = True
        state["messages"].append(AIMessage(content="Test cases validated and enhanced"))
        
        return state
    
    def _finalize_output(self, state: AgentState) -> AgentState:
        """Finalize the output"""
        print("🎯 Finalizing test case generation...")
        
        # Sort by priority and type
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        state["test_cases"].sort(key=lambda x: priority_order.get(x.priority, 2))
        
        summary = f"Generated {len(state['test_cases'])} test cases for {state['jira_issue_key']}"
        state["messages"].append(AIMessage(content=summary))
        
        return state
    
    def _parse_jira_analysis(self, analysis_text: str, state: AgentState) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                analysis_data = {}
        except:
            analysis_data = {}
        
        return {
            "id": state["jira_issue_key"],
            "original_text": state["jira_summary"],
            "issue_type": state["jira_issue_type"],
            "functional_aspects": analysis_data.get("functional_aspects", [state["jira_summary"]]),
            "acceptance_criteria": analysis_data.get("acceptance_criteria", []),
            "edge_cases": analysis_data.get("edge_cases", []),
            "risk_level": analysis_data.get("risk_level", "Medium"),
            "integration_points": analysis_data.get("integration_points", []),
            "security_considerations": analysis_data.get("security_considerations", [])
        }
    
    def _basic_jira_analysis(self, state: AgentState) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        return {
            "id": state["jira_issue_key"],
            "original_text": state["jira_summary"],
            "issue_type": state["jira_issue_type"],
            "functional_aspects": [state["jira_summary"]],
            "acceptance_criteria": ["Core functionality works as described"],
            "edge_cases": ["Invalid input scenarios", "Boundary conditions"],
            "risk_level": "Medium",
            "integration_points": [],
            "security_considerations": []
        }
    
    def _parse_test_cases_from_llm(self, llm_response: str, state: AgentState) -> List[TestCase]:
        """Parse test cases from LLM response"""
        test_cases = []
        
        try:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                cases_data = json.loads(json_match.group())
                
                for i, case_data in enumerate(cases_data):
                    test_case = TestCase(
                        id=f"{state['jira_issue_key']}_TC_{i+1:03d}",
                        title=case_data.get("title", f"Test case for {state['jira_issue_key']}"),
                        description=case_data.get("description", ""),
                        test_type=TestType(case_data.get("test_type", "positive")),
                        preconditions=case_data.get("preconditions", ["System is operational"]),
                        test_steps=case_data.get("test_steps", []),
                        expected_result=case_data.get("expected_result", ""),
                        priority=case_data.get("priority", "Medium"),
                        tags=case_data.get("tags", []),
                        risk_level=case_data.get("risk_level", "Medium"),
                        jira_issue=state["jira_issue_key"]
                    )
                    test_cases.append(test_case)
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            # Fallback to template generation
            test_cases = self._generate_template_test_cases(state)
        
        return test_cases
    
    def _generate_template_test_cases(self, state: AgentState) -> List[TestCase]:
        """Generate template test cases based on issue type"""
        test_cases = []
        issue_key = state["jira_issue_key"]
        summary = state["jira_summary"]
        issue_type = state["jira_issue_type"]
        
        if issue_type.lower() == "bug":
            # Bug-specific test cases
            test_cases.extend([
                TestCase(
                    id=f"{issue_key}_BUG_REGRESSION_001",
                    title=f"Verify bug fix for {issue_key}",
                    description=f"Regression test to verify bug fix: {summary}",
                    test_type=TestType.NEGATIVE,
                    preconditions=["System is operational", "Bug reproduction steps available"],
                    test_steps=[
                        "Set up test environment",
                        "Reproduce original bug scenario",
                        "Verify bug is fixed",
                        "Test related functionality"
                    ],
                    expected_result="Bug is fixed and system behaves correctly",
                    priority="High",
                    tags=["bug_fix", "regression"],
                    jira_issue=issue_key
                ),
                TestCase(
                    id=f"{issue_key}_BUG_EDGE_002",
                    title=f"Test edge cases for {issue_key} fix",
                    description=f"Test edge cases related to bug fix: {summary}",
                    test_type=TestType.EDGE_CASE,
                    preconditions=["System is operational"],
                    test_steps=[
                        "Identify edge cases related to the bug",
                        "Test boundary conditions",
                        "Verify error handling",
                        "Test with invalid inputs"
                    ],
                    expected_result="System handles edge cases appropriately",
                    priority="Medium",
                    tags=["bug_fix", "edge_case"],
                    jira_issue=issue_key
                )
            ])
        
        elif issue_type.lower() == "story":
            # Story-specific test cases
            test_cases.extend([
                TestCase(
                    id=f"{issue_key}_STORY_POSITIVE_001",
                    title=f"Verify {issue_key} happy path",
                    description=f"Test successful execution of user story: {summary}",
                    test_type=TestType.POSITIVE,
                    preconditions=["System is operational", "User has required permissions"],
                    test_steps=[
                        "Navigate to feature",
                        "Execute user story scenario",
                        "Verify expected behavior",
                        "Validate user interface"
                    ],
                    expected_result="User story functionality works as specified",
                    priority="High",
                    tags=["story", "functional"],
                    jira_issue=issue_key
                ),
                TestCase(
                    id=f"{issue_key}_STORY_NEGATIVE_002",
                    title=f"Verify {issue_key} error handling",
                    description=f"Test error scenarios for user story: {summary}",
                    test_type=TestType.NEGATIVE,
                    preconditions=["System is operational"],
                    test_steps=[
                        "Attempt invalid operations",
                        "Test with missing permissions",
                        "Verify error messages",
                        "Test recovery scenarios"
                    ],
                    expected_result="System handles errors gracefully with clear messages",
                    priority="Medium",
                    tags=["story", "error_handling"],
                    jira_issue=issue_key
                )
            ])
        
        else:  # Task or other types
            test_cases.extend([
                TestCase(
                    id=f"{issue_key}_TASK_FUNCTIONAL_001",
                    title=f"Verify {issue_key} implementation",
                    description=f"Test task completion: {summary}",
                    test_type=TestType.POSITIVE,
                    preconditions=["System is operational", "Prerequisites met"],
                    test_steps=[
                        "Verify task implementation",
                        "Test new functionality",
                        "Validate integration points",
                        "Check performance impact"
                    ],
                    expected_result="Task is completed successfully without issues",
                    priority="Medium",
                    tags=["task", "implementation"],
                    jira_issue=issue_key
                )
            ])
        
        return test_cases
    
    def generate_from_jira_issue(self, issue_key: str, summary: str, issue_type: str) -> List[TestCase]:
        """Generate test cases from Jira issue information"""
        initial_state = {
            "messages": [HumanMessage(content=f"Processing Jira issue {issue_key}")],
            "jira_issue_key": issue_key,
            "jira_summary": summary,
            "jira_issue_type": issue_type,
            "requirements": [],
            "parsed_requirements": [],
            "test_cases": [],
            "analysis_complete": False,
            "generation_complete": False,
            "validation_complete": False
        }
        
        # Run the LangGraph workflow
        final_state = self.graph.invoke(initial_state)
        return final_state["test_cases"]
    
    def export_to_json(self, test_cases: List[TestCase], filename: str):
        """Export test cases to JSON"""
        cases_dict = []
        for case in test_cases:
            case_dict = asdict(case)
            case_dict["test_type"] = case.test_type.value
            cases_dict.append(case_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Test cases exported to {filename}")

# Function to be called from Jira webhook
def generate_test_cases_for_jira_issue(issue_key: str, summary: str, issue_type: str) -> str:
    """Generate test cases for a Jira issue and return the filename"""
    try:
        generator = JiraLangGraphGenerator()
        test_cases = generator.generate_from_jira_issue(issue_key, summary, issue_type)
        
        filename = f"jira_generated_test_cases_{issue_key}.json"
        generator.export_to_json(test_cases, filename)
        
        print(f"🎉 Generated {len(test_cases)} test cases for Jira issue {issue_key}")
        return filename
        
    except Exception as e:
        print(f"❌ Error generating test cases for {issue_key}: {e}")
        return None

if __name__ == "__main__":
    # Test with sample Jira issue
    print("🧪 Testing Jira LangGraph Generator...")
    
    # Sample issues for testing
    test_issues = [
        ("BUG-123", "Login form accepts invalid email formats", "Bug"),
        ("STORY-456", "As a user, I want to reset my password via email", "Story"),
        ("TASK-789", "Implement JWT token validation middleware", "Task")
    ]
    
    for issue_key, summary, issue_type in test_issues:
        print(f"\n{'='*60}")
        print(f"Processing: {issue_key} ({issue_type})")
        print(f"Summary: {summary}")
        filename = generate_test_cases_for_jira_issue(issue_key, summary, issue_type)
        if filename:
            print(f"✅ Test cases saved to: {filename}")
        else:
            print("❌ Failed to generate test cases")
