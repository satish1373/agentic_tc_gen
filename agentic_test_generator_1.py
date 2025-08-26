import re
import json
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
import operator

# LangGraph imports
from langgraph.graph import StateGraph, END
#from langgraph.prebuilt import ToolExecutor
#from langgraph.graph import ToolExecutor
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI  # Replace with your preferred LLM

import langgraph.prebuilt
#print(dir(langgraph.prebuilt))

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
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], operator.add]
    requirements: List[Dict[str, str]]
    parsed_requirements: List[Dict[str, Any]]
    test_cases: List[TestCase]
    current_requirement: Optional[Dict[str, Any]]
    analysis_complete: bool
    generation_complete: bool
    validation_complete: bool
    next_action: str

class AgenticTestCaseGenerator:
    """Agentic test case generator using LangGraph"""
    
    def __init__(self, llm_model: str = "gpt-4o", api_key: Optional[str] = None):
        self.llm = ChatOpenAI(
            model=llm_model,
            api_key=api_key,
            temperature=0.1
        )
        self.graph = self._build_graph()
        
        # Analysis prompts
        self.requirement_analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert test analyst. Analyze the given requirement and extract:
            1. Functional aspects (what the system should do)
            2. Non-functional aspects (performance, security, usability)
            3. Input/output specifications
            4. Business rules and constraints
            5. Error conditions and edge cases
            6. Dependencies on other requirements
            7. Risk assessment (High/Medium/Low)
            8. Testability assessment
            
            Return your analysis as a structured JSON object."""),
            ("human", "Requirement ID: {req_id}\nRequirement: {requirement}")
        ])
        
        self.test_case_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert test case designer. Based on the requirement analysis, 
            generate comprehensive test cases that cover:
            
            1. Happy path scenarios (positive testing)
            2. Error scenarios (negative testing)
            3. Boundary value testing
            4. Edge cases and corner cases
            5. Security considerations
            6. Integration points
            
            For each test case, provide:
            - Clear test steps
            - Expected results
            - Preconditions
            - Test data requirements
            - Priority level
            - Risk assessment
            
            Generate test cases in JSON format matching the TestCase structure."""),
            ("human", "Requirement Analysis: {analysis}\nGenerate test cases for requirement: {requirement}")
        ])
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Define the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_requirements", self._analyze_requirements)
        workflow.add_node("generate_test_cases", self._generate_test_cases)
        workflow.add_node("validate_test_cases", self._validate_test_cases)
        workflow.add_node("optimize_test_suite", self._optimize_test_suite)
        workflow.add_node("finalize_output", self._finalize_output)
        
        # Define edges and conditions
        workflow.add_edge("analyze_requirements", "generate_test_cases")
        workflow.add_edge("generate_test_cases", "validate_test_cases")
        workflow.add_edge("validate_test_cases", "optimize_test_suite")
        workflow.add_edge("optimize_test_suite", "finalize_output")
        workflow.add_edge("finalize_output", END)
        
        # Set entry point
        workflow.set_entry_point("analyze_requirements")
        
        return workflow.compile()
    
    def _analyze_requirements(self, state: AgentState) -> AgentState:
        """Analyze requirements using LLM"""
        print("🔍 Analyzing requirements...")
        
        parsed_requirements = []
        
        for req in state["requirements"]:
            # Use LLM to analyze the requirement
            analysis_chain = self.requirement_analysis_prompt | self.llm
            
            try:
                response = analysis_chain.invoke({
                    "req_id": req["id"],
                    "requirement": req["text"]
                })
                
                # Parse the LLM response
                analysis_text = response.content
                
                # Extract structured information (simplified parsing)
                analysis = self._parse_requirement_analysis(analysis_text, req)
                parsed_requirements.append(analysis)
                
            except Exception as e:
                print(f"Error analyzing requirement {req['id']}: {e}")
                # Fallback to basic analysis
                analysis = self._basic_requirement_analysis(req)
                parsed_requirements.append(analysis)
        
        state["parsed_requirements"] = parsed_requirements
        state["analysis_complete"] = True
        state["messages"].append(AIMessage(content=f"Analyzed {len(parsed_requirements)} requirements"))
        
        return state
    
    def _generate_test_cases(self, state: AgentState) -> AgentState:
        """Generate test cases using LLM"""
        print("🚀 Generating test cases...")
        
        all_test_cases = []
        
        for req_analysis in state["parsed_requirements"]:
            try:
                # Use LLM to generate test cases
                generation_chain = self.test_case_generation_prompt | self.llm
                
                response = generation_chain.invoke({
                    "analysis": json.dumps(req_analysis, indent=2),
                    "requirement": req_analysis["original_text"]
                })
                
                # Parse test cases from LLM response
                test_cases = self._parse_test_cases_from_llm(response.content, req_analysis)
                all_test_cases.extend(test_cases)
                
            except Exception as e:
                print(f"Error generating test cases for {req_analysis['id']}: {e}")
                # Fallback to template-based generation
                fallback_cases = self._generate_template_test_cases(req_analysis)
                all_test_cases.extend(fallback_cases)
        
        state["test_cases"] = all_test_cases
        state["generation_complete"] = True
        state["messages"].append(AIMessage(content=f"Generated {len(all_test_cases)} test cases"))
        
        return state
    
    def _validate_test_cases(self, state: AgentState) -> AgentState:
        """Validate and improve test cases"""
        print("✅ Validating test cases...")
        
        validated_cases = []
        
        for test_case in state["test_cases"]:
            # Perform validation checks
            validation_issues = self._validate_single_test_case(test_case)
            
            if validation_issues:
                # Fix issues or mark for manual review
                fixed_case = self._fix_test_case_issues(test_case, validation_issues)
                validated_cases.append(fixed_case)
            else:
                validated_cases.append(test_case)
        
        state["test_cases"] = validated_cases
        state["validation_complete"] = True
        state["messages"].append(AIMessage(content=f"Validated {len(validated_cases)} test cases"))
        
        return state
    
    def _optimize_test_suite(self, state: AgentState) -> AgentState:
        """Optimize the test suite for coverage and efficiency"""
        print("⚡ Optimizing test suite...")
        
        # Remove duplicates
        unique_cases = self._remove_duplicate_test_cases(state["test_cases"])
        
        # Prioritize test cases
        prioritized_cases = self._prioritize_test_cases(unique_cases)
        
        # Add traceability
        traceable_cases = self._add_traceability(prioritized_cases, state["parsed_requirements"])
        
        state["test_cases"] = traceable_cases
        state["messages"].append(AIMessage(content=f"Optimized test suite: {len(traceable_cases)} test cases"))
        
        return state
    
    def _finalize_output(self, state: AgentState) -> AgentState:
        """Finalize the output"""
        print("🎯 Finalizing output...")
        
        # Generate summary statistics
        summary = self._generate_test_suite_summary(state["test_cases"])
        
        state["messages"].append(AIMessage(content=f"Test suite complete: {summary}"))
        
        return state
    
    def _parse_requirement_analysis(self, analysis_text: str, req: Dict[str, str]) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                analysis_data = {}
        except:
            analysis_data = {}
        
        # Ensure required fields
        return {
            "id": req["id"],
            "original_text": req["text"],
            "functional_aspects": analysis_data.get("functional_aspects", []),
            "non_functional_aspects": analysis_data.get("non_functional_aspects", []),
            "business_rules": analysis_data.get("business_rules", []),
            "error_conditions": analysis_data.get("error_conditions", []),
            "risk_level": analysis_data.get("risk_level", "Medium"),
            "testability": analysis_data.get("testability", "High"),
            "dependencies": analysis_data.get("dependencies", [])
        }
    
    def _basic_requirement_analysis(self, req: Dict[str, str]) -> Dict[str, Any]:
        """Fallback basic analysis when LLM fails"""
        return {
            "id": req["id"],
            "original_text": req["text"],
            "functional_aspects": ["Core functionality"],
            "non_functional_aspects": [],
            "business_rules": [],
            "error_conditions": ["Invalid input"],
            "risk_level": "Medium",
            "testability": "High",
            "dependencies": []
        }
    
    def _parse_test_cases_from_llm(self, llm_response: str, req_analysis: Dict[str, Any]) -> List[TestCase]:
        """Parse test cases from LLM response"""
        test_cases = []
        
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
            if json_match:
                cases_data = json.loads(json_match.group())
                
                for i, case_data in enumerate(cases_data):
                    test_case = TestCase(
                        id=f"{req_analysis['id']}_TC_{i+1:03d}",
                        title=case_data.get("title", f"Test case {i+1}"),
                        description=case_data.get("description", ""),
                        test_type=TestType(case_data.get("test_type", "positive")),
                        preconditions=case_data.get("preconditions", []),
                        test_steps=case_data.get("test_steps", []),
                        expected_result=case_data.get("expected_result", ""),
                        priority=case_data.get("priority", "Medium"),
                        tags=case_data.get("tags", []),
                        risk_level=case_data.get("risk_level", "Medium")
                    )
                    test_cases.append(test_case)
        except:
            # Fallback to template generation
            test_cases = self._generate_template_test_cases(req_analysis)
        
        return test_cases
    
    def _generate_template_test_cases(self, req_analysis: Dict[str, Any]) -> List[TestCase]:
        """Generate basic template test cases as fallback"""
        test_cases = []
        req_id = req_analysis["id"]
        
        # Positive test case
        positive_case = TestCase(
            id=f"{req_id}_POSITIVE_001",
            title=f"Verify {req_id} - Valid scenario",
            description=f"Test valid scenario for requirement {req_id}",
            test_type=TestType.POSITIVE,
            preconditions=["System is ready", "Valid test data available"],
            test_steps=[
                "Prepare valid test data",
                "Execute the required functionality",
                "Verify expected behavior"
            ],
            expected_result="System behaves as specified",
            priority="High",
            tags=["functional", "positive"]
        )
        test_cases.append(positive_case)
        
        # Negative test case
        negative_case = TestCase(
            id=f"{req_id}_NEGATIVE_001",
            title=f"Verify {req_id} - Invalid scenario",
            description=f"Test invalid scenario for requirement {req_id}",
            test_type=TestType.NEGATIVE,
            preconditions=["System is ready"],
            test_steps=[
                "Prepare invalid test data",
                "Attempt to execute functionality",
                "Verify error handling"
            ],
            expected_result="System handles error appropriately",
            priority="Medium",
            tags=["functional", "negative"]
        )
        test_cases.append(negative_case)
        
        return test_cases
    
    def _validate_single_test_case(self, test_case: TestCase) -> List[str]:
        """Validate a single test case and return issues"""
        issues = []
        
        if not test_case.test_steps:
            issues.append("Missing test steps")
        
        if not test_case.expected_result:
            issues.append("Missing expected result")
        
        if len(test_case.title) < 10:
            issues.append("Title too short")
        
        return issues
    
    def _fix_test_case_issues(self, test_case: TestCase, issues: List[str]) -> TestCase:
        """Fix identified issues in test case"""
        # Simple fixes for common issues
        if "Missing test steps" in issues:
            test_case.test_steps = ["Execute test scenario", "Verify results"]
        
        if "Missing expected result" in issues:
            test_case.expected_result = "System behaves as expected"
        
        if "Title too short" in issues:
            test_case.title = f"Test Case: {test_case.title}"
        
        return test_case
    
    def _remove_duplicate_test_cases(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Remove duplicate test cases"""
        seen_titles = set()
        unique_cases = []
        
        for case in test_cases:
            if case.title not in seen_titles:
                seen_titles.add(case.title)
                unique_cases.append(case)
        
        return unique_cases
    
    def _prioritize_test_cases(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Prioritize test cases based on risk and type"""
        priority_order = {"High": 1, "Medium": 2, "Low": 3}
        type_order = {
            TestType.POSITIVE: 1,
            TestType.SECURITY: 2,
            TestType.NEGATIVE: 3,
            TestType.BOUNDARY: 4,
            TestType.EDGE_CASE: 5,
            TestType.INTEGRATION: 6
        }
        
        return sorted(test_cases, key=lambda x: (
            priority_order.get(x.priority, 2),
            type_order.get(x.test_type, 5)
        ))
    
    def _add_traceability(self, test_cases: List[TestCase], requirements: List[Dict[str, Any]]) -> List[TestCase]:
        """Add traceability links between test cases and requirements"""
        req_map = {req["id"]: req for req in requirements}
        
        for case in test_cases:
            req_id = case.id.split("_")[0]  # Extract requirement ID from test case ID
            if req_id in req_map:
                case.tags.append(f"traces_to_{req_id}")
        
        return test_cases
    
    def _generate_test_suite_summary(self, test_cases: List[TestCase]) -> str:
        """Generate summary of the test suite"""
        total = len(test_cases)
        by_type = {}
        by_priority = {}
        
        for case in test_cases:
            by_type[case.test_type.value] = by_type.get(case.test_type.value, 0) + 1
            by_priority[case.priority] = by_priority.get(case.priority, 0) + 1
        
        return f"{total} total test cases. Types: {by_type}. Priorities: {by_priority}"
    
    def generate_test_cases(self, requirements: List[tuple]) -> List[TestCase]:
        """Main method to generate test cases from requirements"""
        # Convert requirements to expected format
        req_list = [{"id": req_id, "text": req_text} for req_id, req_text in requirements]
        
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content="Starting test case generation")],
            "requirements": req_list,
            "parsed_requirements": [],
            "test_cases": [],
            "current_requirement": None,
            "analysis_complete": False,
            "generation_complete": False,
            "validation_complete": False,
            "next_action": "analyze"
        }
        
        # Run the agent workflow
        final_state = self.graph.invoke(initial_state)
        
        return final_state["test_cases"]
    
    def export_to_json(self, test_cases: List[TestCase], filename: str = "test_cases.json"):
        """Export test cases to JSON"""
        cases_dict = [asdict(case) for case in test_cases]
        # Convert enums to strings
        for case in cases_dict:
            case["test_type"] = case["test_type"].value if hasattr(case["test_type"], 'value') else case["test_type"]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases_dict, f, indent=2, ensure_ascii=False)
    
    def print_test_cases(self, test_cases: List[TestCase]):
        """Print test cases in a readable format"""
        for tc in test_cases:
            print(f"\n{'='*60}")
            print(f"Test ID: {tc.id}")
            print(f"Title: {tc.title}")
            print(f"Type: {tc.test_type.value.upper()}")
            print(f"Priority: {tc.priority}")
            print(f"Risk Level: {tc.risk_level}")
            print(f"Description: {tc.description}")
            print(f"\nPreconditions:")
            for i, precond in enumerate(tc.preconditions, 1):
                print(f"  {i}. {precond}")
            print(f"\nTest Steps:")
            for i, step in enumerate(tc.test_steps, 1):
                print(f"  {i}. {step}")
            print(f"\nExpected Result: {tc.expected_result}")
            print(f"Tags: {', '.join(tc.tags)}")
            print(f"Automation Feasible: {tc.automation_feasible}")

# Example usage
def main():
    """Example usage of the Agentic Test Case Generator"""
    
    # Initialize the agent (you'll need to provide your OpenAI API key)
    generator = AgenticTestCaseGenerator(
        llm_model="gpt-4o",
        api_key="OPENAI_API_KEY"  # Replace with your actual API key
    )
    
    # Sample requirements
    requirements = [
        ("REQ001", "The system shall validate user email addresses using RFC 5322 standard and reject invalid formats with appropriate error messages"),
        ("REQ002", "User passwords must be between 8 and 128 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character"),
        ("REQ003", "The system shall implement rate limiting to prevent brute force attacks, allowing maximum 5 login attempts per IP address within 15 minutes"),
        ("REQ004", "When a user enters invalid credentials 3 consecutive times, the account shall be temporarily locked for 30 minutes"),
        ("REQ005", "The system shall log all authentication events including successful logins, failed attempts, and account lockouts for security audit purposes")
    ]
    
    try:
        # Generate test cases using the agent
        print("🤖 Starting Agentic Test Case Generation...")
        test_cases = generator.generate_test_cases(requirements)
        
        # Display results
        print(f"\n🎉 Generated {len(test_cases)} test cases using AI-powered analysis!")
        generator.print_test_cases(test_cases)
        
        # Export results
        generator.export_to_json(test_cases, "agentic_test_cases.json")
        print(f"\n💾 Test cases exported to agentic_test_cases.json")
        
    except Exception as e:
        print(f"❌ Error during test case generation: {e}")
        print("This might be due to missing API key or LangGraph dependencies.")
        print("Please ensure you have installed: pip install langchain langgraph openai")

if __name__ == "__main__":
    main()