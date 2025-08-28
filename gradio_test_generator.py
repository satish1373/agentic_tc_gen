
import gradio as gr
import json
import csv
import os
import sys
from datetime import datetime

# Import the test generator
from agentic_test_generator_1 import AgenticTestCaseGenerator

class GradioTestCaseApp:
    def __init__(self):
        self.generator = AgenticTestCaseGenerator()
        self.setup_ui()
    
    def process_requirements_file(self, file):
        """Process uploaded requirements file and generate test cases"""
        if file is None:
            return "❌ Please upload a file first.", "", None
        
        try:
            print(f"📁 Processing file: {file.name}")
            
            # Process the uploaded file
            requirements = self.generator.process_uploaded_file(file.name)
            
            if not requirements:
                return "❌ No requirements found. Check file format and content.", "", None
            
            print(f"📋 Found {len(requirements)} requirements")
            
            # Generate test cases
            print("🚀 Generating test cases...")
            test_cases = self.generator.generate_test_cases(requirements)
            
            print(f"✅ Generated {len(test_cases)} test cases")
            
            # Create summary
            summary = f"""## 🎉 Test Case Generation Complete!

**📊 Summary:**
- **Requirements processed:** {len(requirements)}
- **Test cases generated:** {len(test_cases)}
- **Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**📋 Requirements processed:**"""
            
            for req_id, req_text in requirements:
                summary += f"\n- **{req_id}**: {req_text[:80]}{'...' if len(req_text) > 80 else ''}"
            
            # Export to JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_filename = f"test_cases_{timestamp}.json"
            self.generator.export_to_json(test_cases, json_filename)
            
            # Create detailed results
            detailed_results = self.format_test_cases(test_cases)
            
            return summary, detailed_results, json_filename
            
        except Exception as e:
            error_msg = f"❌ Error processing file: {str(e)}"
            print(error_msg)
            return error_msg, "", None
    
    def format_test_cases(self, test_cases):
        """Format test cases for display"""
        if not test_cases:
            return "No test cases generated."
        
        results = "## 📋 Generated Test Cases\n\n"
        
        # Group by test type
        by_type = {}
        for tc in test_cases:
            test_type = tc.test_type.value
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(tc)
        
        # Show statistics
        results += "### 📊 Test Case Statistics\n\n"
        for test_type, cases in by_type.items():
            results += f"- **{test_type.title()}**: {len(cases)} test cases\n"
        results += "\n---\n\n"
        
        # Show first few test cases in detail
        results += "### 🔍 Detailed Test Cases (Preview)\n\n"
        
        for i, tc in enumerate(test_cases[:8]):  # Show first 8 test cases
            priority_emoji = "🔴" if tc.priority == "High" else "🟡" if tc.priority == "Medium" else "🟢"
            type_emoji = {
                "positive": "✅",
                "negative": "❌", 
                "boundary": "⚖️",
                "security": "🔒",
                "performance": "⚡",
                "integration": "🔗"
            }.get(tc.test_type.value, "📝")
            
            results += f"""
#### {type_emoji} {tc.id}: {tc.title}
{priority_emoji} **Priority:** {tc.priority} | **Risk:** {tc.risk_level} | **Type:** {tc.test_type.value.upper()}

**Description:** {tc.description}

**Preconditions:**
{chr(10).join(f'- {precond}' for precond in tc.preconditions)}

**Test Steps:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(tc.test_steps))}

**Expected Result:** {tc.expected_result}

**Tags:** `{' | '.join(tc.tags)}`

---
"""
        
        if len(test_cases) > 8:
            results += f"\n*📎 {len(test_cases) - 8} more test cases are available in the downloadable JSON file.*\n"
        
        return results
    
    def create_sample_file(self):
        """Create a sample requirements file"""
        sample_data = [
            ["REQ001", "The system shall validate user email addresses using RFC 5322 standard", "High", "Authentication"],
            ["REQ002", "User passwords must be 8-128 characters with mixed case, digits, and special chars", "High", "Security"],
            ["REQ003", "System shall implement rate limiting: max 5 login attempts per IP in 15 minutes", "Medium", "Security"],
            ["REQ004", "Account locks for 30 minutes after 3 consecutive invalid login attempts", "High", "Security"],
            ["REQ005", "Log all authentication events for security audit purposes", "Medium", "Logging"]
        ]
        
        filename = f"sample_requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Requirement", "Priority", "Category"])
            writer.writerows(sample_data)
        
        return filename
    
    def setup_ui(self):
        """Setup the Gradio interface"""
        with gr.Blocks(
            title="AI Test Case Generator",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container { max-width: 1400px !important; }
            .priority-high { border-left: 4px solid #dc3545; }
            .priority-medium { border-left: 4px solid #ffc107; }
            .priority-low { border-left: 4px solid #28a745; }
            """
        ) as self.interface:
            
            # Header
            gr.Markdown("""
            # 🤖 AI-Powered Test Case Generator
            
            Transform your requirements into comprehensive test cases using advanced AI analysis.
            Upload your requirements file and get professionally structured test cases in seconds!
            
            ## 📚 Supported File Formats:
            - **CSV**: Columns like 'ID', 'Requirement', 'Description'
            - **JSON**: Objects with 'id' and 'requirement'/'text' fields  
            - **TXT**: Plain text, one requirement per line
            """)
            
            with gr.Row():
                # Left Column - Upload and Controls
                with gr.Column(scale=2):
                    gr.Markdown("### 📁 Upload Requirements")
                    
                    file_input = gr.File(
                        label="Choose Requirements File",
                        file_types=[".csv", ".json", ".txt"],
                        file_count="single",
                        height=100
                    )
                    
                    with gr.Row():
                        generate_btn = gr.Button(
                            "🚀 Generate Test Cases", 
                            variant="primary",
                            size="lg",
                            scale=3
                        )
                        
                        sample_btn = gr.Button(
                            "📋 Get Sample File", 
                            variant="secondary",
                            scale=1
                        )
                    
                    # Tips and Info
                    with gr.Accordion("💡 Tips & Guidelines", open=False):
                        gr.Markdown("""
                        ### File Format Guidelines:
                        
                        **CSV Files:**
                        - Must have header row
                        - Required columns: 'ID' and 'Requirement' (or similar)
                        - Optional: 'Priority', 'Category', 'Description'
                        
                        **JSON Files:**
                        - Array of requirement objects
                        - Required fields: 'id' and 'requirement' or 'text'
                        - Example: `[{"id": "REQ001", "text": "System shall..."}]`
                        
                        **TXT Files:**  
                        - One requirement per line
                        - Optional format: `REQ001: Description here`
                        - Empty lines and comments (#) are ignored
                        
                        ### Best Practices:
                        - Write clear, specific requirements
                        - Include acceptance criteria when possible
                        - Use consistent requirement IDs
                        - Specify priority levels if available
                        """)
                
                # Right Column - Status and Download
                with gr.Column(scale=1):
                    gr.Markdown("### 📊 Generation Status")
                    
                    status_output = gr.Markdown(
                        value="📤 **Ready to process**\n\nUpload a file and click 'Generate Test Cases'",
                        show_label=False
                    )
                    
                    download_output = gr.File(
                        label="📥 Download Test Cases (JSON)",
                        visible=False,
                        height=100
                    )
                    
                    # Progress and stats will appear here
                    with gr.Group(visible=False) as stats_group:
                        gr.Markdown("### 📈 Quick Stats")
                        stats_output = gr.JSON(label="Statistics", show_label=False)
            
            # Results Area
            gr.Markdown("---")
            
            with gr.Row():
                detailed_output = gr.Markdown(
                    label="Generated Test Cases",
                    value="🔄 **Awaiting file upload...**\n\nYour generated test cases will appear here with full details.",
                    show_label=False,
                    height=600,
                    elem_classes=["results-area"]
                )
            
            # Event Handlers
            generate_btn.click(
                fn=self.process_requirements_file,
                inputs=[file_input],
                outputs=[status_output, detailed_output, download_output],
                show_progress="full"
            )
            
            sample_btn.click(
                fn=self.create_sample_file,
                outputs=[download_output],
                show_progress="minimal"
            )
            
            # Auto-show download when file is ready
            download_output.change(
                fn=lambda x: gr.update(visible=x is not None),
                inputs=[download_output],
                outputs=[download_output]
            )
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        default_kwargs = {
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "share": True,
            "show_api": False,
            "debug": False,
            "max_threads": 10
        }
        default_kwargs.update(kwargs)
        
        print("🚀 Launching AI Test Case Generator...")
        print(f"🌐 Gradio UI will be available at: http://0.0.0.0:{default_kwargs['server_port']}")
        print(f"🔗 Access via: https://workspace.satish73learnin.replit.dev:{default_kwargs['server_port']}")
        
        return self.interface.launch(**default_kwargs)

def main():
    """Main function to run the Gradio app"""
    app = GradioTestCaseApp()
    app.launch()

if __name__ == "__main__":
    main()
