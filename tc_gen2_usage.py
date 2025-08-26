#Import the Test Case Generator from the Test Case generation script
from fixed_test_generator_2 import TestCaseGenerator

# Initialize the generator
generator = TestCaseGenerator()

# Process multiple file types
test_cases, stats = generator.generate_test_cases_from_files([
    'product_requirements.csv',
    #'specs.xlsx', 
    'user_stories.json',
    'product_requirements.txt'
])

# Export results
generator.export_to_excel(test_cases, "test_suite.xlsx")
generator.generate_test_report(test_cases, stats, "report.html")