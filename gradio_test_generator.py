import gradio as gr
import json
import csv
import os
import sys
from datetime import datetime

# Import the test generator
from agentic_test_generator_1 import AgenticTestCaseGenerator

class SimpleGradioTestApp:
    def __init__(self):
        self.generator = AgenticTestCaseGenerator()

    def process_file(self, file):
        """Process uploaded file and generate test cases"""
        if file is None:
            return "❌ Please upload a file first.", "No test cases generated yet.", None

        try:
            print(f"📁 Processing file: {file.name}")

            # Process the uploaded file
            requirements = self.generator.process_uploaded_file(file.name)

            if not requirements:
                return "❌ No requirements found. Check file format.", "No test cases generated yet.", None

            print(f"📋 Found {len(requirements)} requirements")

            # Generate test cases
            print("🚀 Generating test cases...")
            test_cases = self.generator.generate_test_cases(requirements)

            print(f"✅ Generated {len(test_cases)} test cases")

            # Create summary
            summary = f"""## ✅ Success!

**Generated:** {len(test_cases)} test cases from {len(requirements)} requirements

**File processed:** {os.path.basename(file.name)}  
**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            # Format test cases for display
            detailed_results = self.format_test_cases(test_cases)

            # Export to JSON
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_filename = f"test_cases_{timestamp}.json"
            self.generator.export_to_json(test_cases, json_filename)

            return summary, detailed_results, json_filename

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            print(error_msg)
            return error_msg, "Error occurred during processing.", None

    def format_test_cases(self, test_cases):
        """Format test cases for display"""
        if not test_cases:
            return "No test cases generated."

        results = f"## 📋 Generated {len(test_cases)} Test Cases\n\n"

        # Show first few test cases
        for i, tc in enumerate(test_cases[:6]):  # Show first 6
            results += f"""
### {tc.id}: {tc.title}
**Type:** {tc.test_type.value.upper()} | **Priority:** {tc.priority}

**Description:** {tc.description}

**Steps:**
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(tc.test_steps))}

**Expected:** {tc.expected_result}

---
"""

        if len(test_cases) > 6:
            results += f"\n*📎 {len(test_cases) - 6} more test cases in the downloadable file.*\n"

        return results

    def create_sample(self):
        """Create sample requirements file"""
        sample_data = [
            ["REQ001", "User must enter valid email address", "High"],
            ["REQ002", "Password must be 8+ characters", "High"],
            ["REQ003", "System logs all login attempts", "Medium"]
        ]

        filename = f"sample_requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Requirement", "Priority"])
            writer.writerows(sample_data)

        return filename

def create_interface():
    """Create the Gradio interface"""
    app = SimpleGradioTestApp()

    with gr.Blocks(title="AI Test Case Generator", theme=gr.themes.Soft()) as interface:

        gr.Markdown("""
        # 🤖 AI Test Case Generator

        Upload requirements (CSV, JSON, TXT) and generate comprehensive test cases automatically!
        """)

        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📁 Upload File")

                file_input = gr.File(
                    label="Requirements File",
                    file_types=[".csv", ".json", ".txt"]
                )

                with gr.Row():
                    generate_btn = gr.Button("🚀 Generate", variant="primary")
                    sample_btn = gr.Button("📋 Sample", variant="secondary")

        with gr.Row():
            status_output = gr.Markdown("Ready to process files...")

        with gr.Row():
            results_output = gr.Markdown("Upload a file to see results here...")

        with gr.Row():
            download_output = gr.File(label="📥 Download JSON", visible=False)

        # Event handlers
        generate_btn.click(
            fn=app.process_file,
            inputs=[file_input],
            outputs=[status_output, results_output, download_output]
        )

        sample_btn.click(
            fn=app.create_sample,
            outputs=[download_output]
        )

        # Show download when file is ready
        download_output.change(
            fn=lambda x: gr.update(visible=x is not None),
            inputs=[download_output],
            outputs=[download_output]
        )

    return interface

def main():
    """Launch the application"""
    interface = create_interface()

    print("🚀 Starting AI Test Case Generator...")
    print("🌐 Access at: http://0.0.0.0:7860")

    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_api=False
    )

if __name__ == "__main__":
    main()