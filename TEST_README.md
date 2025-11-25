# Test Suite Documentation

## Overview
This test suite provides comprehensive testing for all agents in the question paper generation system, including individual agent tests, full pipeline tests, and corner case handling.

## Running the Tests

### Prerequisites
1. Ensure you have set up your `.env` file with `GOOGLE_API_KEY`
2. Install all dependencies: `pip install -r requirements.txt`

### Basic Usage
```bash
python test_agents.py
```

This will run all test suites and generate a detailed report.

## Test Coverage

### 1. ResearchAgent Tests
- ✅ Basic topic research (40+ ideas)
- ✅ Complex topics with special characters
- ✅ Edge cases (empty topics, very long topics)

### 2. QuestionFramerAgent Tests
- ✅ Basic question framing
- ✅ Questions with math notation
- ✅ Different difficulty levels (basic, intermediate, advanced)
- ✅ Diagram detection

### 3. ValidatorAgent Tests
- ✅ Valid question validation
- ✅ Rejection of sample/fallback questions
- ✅ Handling of incomplete questions

### 4. DiagramAgent Tests
- ✅ TikZ diagram generation for questions needing diagrams
- ✅ Skipping when diagrams not needed

### 5. PythonDiagramAgent Tests
- ✅ PNG diagram generation for complex diagrams
- ✅ Skipping when not needed

### 6. LaTeXWriter Tests
- ✅ Basic question writing
- ✅ Questions with TikZ diagrams
- ✅ Questions with PNG images
- ✅ Special character escaping
- ✅ Embedded options handling (edge case)

### 7. Full Pipeline Tests
- ✅ 25 questions generation (default)
- ✅ 30 questions generation (custom count)
- ✅ File creation verification
- ✅ Difficulty distribution
- ✅ Diagram distribution

### 8. Corner Cases
- ✅ Empty topic names
- ✅ Very long topic names
- ✅ Special characters in topics
- ✅ Empty options handling
- ✅ Very long question text

## Test Output

### Console Output
The test runner provides real-time feedback:
- ✅ PASS: Test passed
- ❌ FAIL: Test failed (with error message)

### Test Results File
After running, results are saved to:
```
test_output/test_results.json
```

This file contains:
- Summary statistics (total, passed, failed, success rate)
- Detailed results for each test
- Error messages for failed tests

## Test Output Directories

All test outputs are saved in the `test_output/` directory:
- `test_output/pipeline_25/` - Full pipeline test with 25 questions
- `test_output/pipeline_30/` - Full pipeline test with 30 questions
- `test_output/images/` - Generated diagram images
- `test_output/test_questions.tex` - LaTeX file from LaTeXWriter tests

## Expected Test Results

### Success Criteria
- **ResearchAgent**: Should generate 40+ ideas for valid topics
- **QuestionFramerAgent**: Should create valid questions with 4 options
- **ValidatorAgent**: Should accept valid questions and reject invalid ones
- **DiagramAgent**: Should generate TikZ code when needed
- **PythonDiagramAgent**: Should create PNG files when needed
- **LaTeXWriter**: Should create valid LaTeX files
- **Full Pipeline**: Should generate target number of questions with proper distribution

### Common Issues

1. **API Key Missing**
   - Error: `GOOGLE_API_KEY not found`
   - Solution: Set your API key in `.env` file

2. **API Rate Limits**
   - Some tests may fail if you hit rate limits
   - Solution: Wait and retry, or use a different API key

3. **Network Issues**
   - Tests requiring API calls may timeout
   - Solution: Check your internet connection

## Customizing Tests

### Adding New Tests
To add a new test case, add a method to the `TestRunner` class:

```python
def test_my_new_feature(self):
    """Test description."""
    print("\n" + "="*60)
    print("TESTING My New Feature")
    print("="*60)
    
    try:
        # Your test code here
        passed = True  # Your validation
        self.log_test("My Test: Description", passed, "Details")
    except Exception as e:
        self.log_test("My Test: Description", False, str(e))
```

Then add it to `run_all_tests()`:

```python
self.test_my_new_feature()
```

### Testing Specific Agents
You can run individual test methods:

```python
runner = TestRunner()
runner.test_research_agent()  # Test only ResearchAgent
runner.test_question_framer_agent()  # Test only QuestionFramerAgent
```

## Integration with CI/CD

The test suite can be integrated into CI/CD pipelines:

```bash
# Run tests and check exit code
python test_agents.py
if [ $? -eq 0 ]; then
    echo "All tests passed"
else
    echo "Some tests failed"
    exit 1
fi
```

## Performance Notes

- Full pipeline tests may take several minutes (API calls)
- Individual agent tests are faster
- Consider running specific test suites during development
- Full suite recommended before deployment

## Troubleshooting

### Tests Failing Due to API Issues
- Check your API key is valid
- Verify you have API quota remaining
- Check network connectivity

### LaTeX Compilation Errors
- Ensure `worksheet.sty` is in the output directory
- Check for special characters in questions
- Verify image paths are correct

### File Permission Errors
- Ensure write permissions in `test_output/` directory
- Check disk space availability

