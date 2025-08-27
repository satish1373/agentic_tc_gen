
import re
import json
import csv
import os
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, asdict
from enum import Enum
import operator
import gradio as gr
import pandas as pd

# LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

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
        try:
            self.llm = ChatOpenAI(
                model=llm_model,
                api_key=api_key or os.getenv("OPENAI_API_KEY"),
                temperature=0.1
            )
            self.use_llm = True
        except Exception as e:
            print(f"⚠️ LLM initialization failed: {e}")
            print("📝 Falling back to template-based generation")
            self.use_llm = False
            
        self.graph = self._build_graph()
        
        # Analysis prompts (only used if LLM is available)
        if self.use_llm:
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
    
    def process_uploaded_file(self, file_path: str) -> List[tuple]:
        """Process uploaded file and extract requirements"""
        requirements = []
        
        if not file_path or not os.path.exists(file_path):
            return requirements
            
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
                # Look for common column names
                id_col = None
                text_col = None
                
                for col in df.columns:
                    col_lower = col.lower()
                    if 'id' in col_lower:
                        id_col = col
                    elif any(keyword in col_lower for keyword in ['requirement', 'description', 'text', 'story']):
                        text_col = col
                
                if text_col:
                    for idx, row in df.iterrows():
                        req_id = str(row[id_col]) if id_col else f"REQ{idx+1:03d}"
                        req_text = str(row[text_col])
                        requirements.append((req_id, req_text))
                        
            elif file_extension == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    for idx, item in enumerate(data):
                        if isinstance(item, dict):
                            req_id = item.get('id', f"REQ{idx+1:03d}")
                            req_text = item.get('requirement') or item.get('text') or item.get('description', '')
                            requirements.append((req_id, req_text))
                elif isinstance(data, dict):
                    if 'requirements' in data:
                        for idx, item in enumerate(data['requirements']):
                            req_id = item.get('id', f"REQ{idx+1:03d}")
                            req_text = item.get('requirement') or item.get('text') or item.get('description', '')
                            requirements.append((req_id, req_text))
                            
            elif file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                req_counter = 1
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Try to extract ID from line
                        match = re.match(r'(REQ\d+|R\d+|\d+)[:.\s]+(.+)', line)
                        if match:
                            req_id = match.group(1)
                            req_text = match.group(2).strip()
                        else:
                            req_id = f"REQ{req_counter:03d}"
                            req_text = line
                        requirements.append((req_id, req_text))
                        req_counter += 1
                        
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            
        return requirements
    
    def _analyze_requirements(self, state: AgentState) -> AgentState:
        """Analyze requirements using LLM or fallback"""
        print("🔍 Analyzing requirements...")
        
        parsed_requirements = []
        
        for req in state["requirements"]:
            if self.use_llm:
                try:
                    analysis_chain = self.requirement_analysis_prompt | self.llm
                    response = analysis_chain.invoke({
                        "req_id": req["id"],
                        "requirement": req["text"]
                    })
                    analysis_text = response.content
                    analysis = self._parse_requirement_analysis(analysis_text, req)
                    parsed_requirements.append(analysis)
                except Exception as e:
                    print(f"Error analyzing requirement {req['id']}: {e}")
                    analysis = self._basic_requirement_analysis(req)
                    parsed_requirements.append(analysis)
            else:
                analysis = self._basic_requirement_analysis(req)
                parsed_requirements.append(analysis)
        
        state["parsed_requirements"] = parsed_requirements
        state["analysis_complete"] = True
        state["messages"].append(AIMessage(content=f"Analyzed {len(parsed_requirements)} requirements"))
        
        return state
    
    def _generate_test_cases(self, state: AgentState) -> AgentState:
        """Generate test cases using LLM or templates"""
        print("🚀 Generating test cases...")
        
        all_test_cases = []
        
        for req_analysis in state["parsed_requirements"]:
            if self.use_llm:
                try:
                    generation_chain = self.test_case_generation_prompt | self.llm
                    response = generation_chain.invoke({
                        "analysis": json.dumps(req_analysis, indent=2),
                        "requirement": req_analysis["original_text"]
                    })
                    test_cases = self._parse_test_cases_from_llm(response.content, req_analysis)
                    all_test_cases.extend(test_cases)
                except Exception as e:
                    print(f"Error generating test cases for {req_analysis['id']}: {e}")
                    fallback_cases = self._generate_template_test_cases(req_analysis)
                    all_test_cases.extend(fallback_cases)
            else:
                template_cases = self._generate_template_test_cases(req_analysis)
                all_test_cases.extend(template_cases)
        
        state["test_cases"] = all_test_cases
        state["generation_complete"] = True
        state["messages"].append(AIMessage(content=f"Generated {len(all_test_cases)} test cases"))
        
        return state
    
    def _validate_test_cases(self, state: AgentState) -> AgentState:
        """Validate and improve test cases"""
        print("✅ Validating test cases...")
        
        validated_cases = []
        
        for test_case in state["test_cases"]:
            validation_issues = self._validate_single_test_case(test_case)
            
            if validation_issues:
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
        
        unique_cases = self._remove_duplicate_test_cases(state["test_cases"])
        prioritized_cases = self._prioritize_test_cases(unique_cases)
        traceable_cases = self._add_traceability(prioritized_cases, state["parsed_requirements"])
        
        state["test_cases"] = traceable_cases
        state["messages"].append(AIMessage(content=f"Optimized test suite: {len(traceable_cases)} test cases"))
        
        return state
    
    def _finalize_output(self, state: AgentState) -> AgentState:
        """Finalize the output"""
        print("🎯 Finalizing output...")
        
        summary = self._generate_test_suite_summary(state["test_cases"])
        state["messages"].append(AIMessage(content=f"Test suite complete: {summary}"))
        
        return state
    
    # Helper methods (keeping the same implementations from the original code)
    def _parse_requirement_analysis(self, analysis_text: str, req: Dict[str, str]) -> Dict[str, Any]:
        """Parse LLM analysis response"""
        try:
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                analysis_data = {}
        except:
            analysis_data = {}
        
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
            req_id = case.id.split("_")[0]
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
        req_list = [{"id": req_id, "text": req_text} for req_id, req_text in requirements]
        
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
        
        final_state = self.graph.invoke(initial_state)
        return final_state["test_cases"]
    
    def export_to_json(self, test_cases: List[TestCase], filename: str = "test_cases.json"):
        """Export test cases to JSON"""
        cases_dict = [asdict(case) for case in test_cases]
        for case in cases_dict:
            case["test_type"] = case["test_type"].value if hasattr(case["test_type"], 'value') else case["test_type"]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cases_dict, f, indent=2, ensure_ascii=False)
        
        return filename

# Global generator instance
generator = AgenticTestCaseGenerator()

def process_requirements_file(file):
    """Process uploaded requirements file and generate test cases"""
    if file is None:
        return "Please upload a file first.", None, None
    
    try:
        # Process the uploaded file
        requirements = generator.process_uploaded_file(file.name)
        
        if not requirements:
            return "No requirements found in the uploaded file. Please check the file format.", None, None
        
        # Generate test cases
        test_cases = generator.generate_test_cases(requirements)
        
        # Create summary
        summary = f"""
        📊 **Test Case Generation Complete!**
        
        **Summary:**
        - Requirements processed: {len(requirements)}
        - Test cases generated: {len(test_cases)}
        
        **Requirements found:**
        """
        
        for req_id, req_text in requirements[:5]:  # Show first 5 requirements
            summary += f"\n- **{req_id}**: {req_text[:100]}{'...' if len(req_text) > 100 else ''}"
        
        if len(requirements) > 5:
            summary += f"\n... and {len(requirements) - 5} more requirements"
        
        # Export to JSON
        json_filename = f"generated_test_cases_{len(test_cases)}cases.json"
        generator.export_to_json(test_cases, json_filename)
        
        # Create detailed results
        detailed_results = "## Generated Test Cases\n\n"
        
        for i, tc in enumerate(test_cases[:10]):  # Show first 10 test cases
            detailed_results += f"""
### {tc.id}: {tc.title}
**Type**: {tc.test_type.value.upper()} | **Priority**: {tc.priority} | **Risk**: {tc.risk_level}

**Description**: {tc.description}

**Preconditions**:
{chr(10).join(f'- {precond}' for precond in tc.preconditions)}

**Test Steps**:
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(tc.test_steps))}

**Expected Result**: {tc.expected_result}

**Tags**: {', '.join(tc.tags)}

---
"""
        
        if len(test_cases) > 10:
            detailed_results += f"\n*... and {len(test_cases) - 10} more test cases in the JSON file*"
        
        return summary, detailed_results, json_filename
        
    except Exception as e:
        return f"Error processing file: {str(e)}", None, None

def create_sample_requirements():
    """Create a sample requirements file for demonstration"""
    sample_requirements = [
        ("REQ001", "The system shall validate user email addresses using RFC 5322 standard and reject invalid formats with appropriate error messages"),
        ("REQ002", "User passwords must be between 8 and 128 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character"),
        ("REQ003", "The system shall implement rate limiting to prevent brute force attacks, allowing maximum 5 login attempts per IP address within 15 minutes"),
        ("REQ004", "When a user enters invalid credentials 3 consecutive times, the account shall be temporarily locked for 30 minutes"),
        ("REQ005", "The system shall log all authentication events including successful logins, failed attempts, and account lockouts for security audit purposes")
    ]
    
    # Create CSV sample
    csv_filename = "sample_requirements.csv"
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Requirement", "Priority", "Category"])
        for req_id, req_text in sample_requirements:
            writer.writerow([req_id, req_text, "High", "Authentication"])
    
    return csv_filename

# Create Gradio Interface
def create_gradio_interface():
    """Create the Gradio web interface"""
    
    with gr.Blocks(
        title="AI-Powered Test Case Generator",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as interface:
        
        gr.Markdown("""
        # 🤖 AI-Powered Test Case Generator
        
        Upload your requirements file (CSV, JSON, or TXT) and let AI generate comprehensive test cases automatically!
        
        **Supported formats:**
        - **CSV**: Must have columns like 'ID', 'Requirement', 'Description', etc.
        - **JSON**: Array of objects with 'id' and 'requirement'/'text' fields
        - **TXT**: Plain text with one requirement per line (optionally prefixed with REQ001:, etc.)
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Upload Requirements")
                
                file_input = gr.File(
                    label="Upload Requirements File",
                    file_types=[".csv", ".json", ".txt"],
                    file_count="single"
                )
                
                with gr.Row():
                    generate_btn = gr.Button(
                        "🚀 Generate Test Cases", 
                        variant="primary",
                        scale=2
                    )
                    sample_btn = gr.Button(
                        "📝 Download Sample", 
                        variant="secondary",
                        scale=1
                    )
                
                gr.Markdown("""
                ### 💡 Tips:
                - Ensure your file has clear requirement descriptions
                - CSV files should have 'ID' and 'Requirement' columns
                - JSON files should have 'id' and 'text'/'requirement' fields
                - TXT files should have one requirement per line
                """)
            
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Results")
                
                summary_output = gr.Markdown(
                    label="Summary",
                    value="Upload a file and click 'Generate Test Cases' to see results here."
                )
                
                download_output = gr.File(
                    label="Download Generated Test Cases (JSON)",
                    visible=False
                )
        
        with gr.Row():
            detailed_output = gr.Markdown(
                label="Detailed Test Cases",
                value="Detailed test cases will appear here after generation."
            )
        
        # Event handlers
        generate_btn.click(
            fn=process_requirements_file,
            inputs=[file_input],
            outputs=[summary_output, detailed_output, download_output],
            show_progress=True
        )
        
        sample_btn.click(
            fn=create_sample_requirements,
            inputs=[],
            outputs=[download_output],
            show_progress=True
        )
        
        # Auto-update download visibility
        download_output.change(
            fn=lambda x: gr.update(visible=x is not None),
            inputs=[download_output],
            outputs=[download_output]
        )
    
    return interface

# Launch the application
if __name__ == "__main__":
    print("🚀 Starting AI-Powered Test Case Generator with Gradio UI...")
    
    # Create and launch the interface
    interface = create_gradio_interface()
    
    # Launch with public sharing enabled
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True if you want a public URL
        show_api=True,
        debug=True
    )
