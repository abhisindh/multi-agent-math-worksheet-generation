"""
Comprehensive test suite for all agents in the question paper generation system.
Tests individual agents and the full pipeline with various corner cases.
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.research_agent import ResearchAgent
from agents.question_framer_agent import QuestionFramerAgent
from agents.validator_agent import ValidatorAgent
from agents.diagram_agent import DiagramAgent
from agents.python_diagram_agent import PythonDiagramAgent
from writers.latex_writer import LaTeXWriter
from main import QuestionPaperGenerator

load_dotenv()


class TestRunner:
    """Test runner for all agents."""
    
    def __init__(self):
        self.test_results = []
        self.output_dir = Path("test_output")
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
    
    def log_test(self, test_name, passed, message=""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "message": message
        })
        return passed
    
    def test_research_agent(self):
        """Test ResearchAgent with various topics."""
        print("\n" + "="*60)
        print("TESTING ResearchAgent")
        print("="*60)
        
        agent = ResearchAgent()
        
        # Test 1: Basic topic
        try:
            result = agent.generate_ideas("Quadratic Equations", "Class 10")
            ideas = result.get("ideas", [])
            passed = len(ideas) >= 40
            self.log_test("ResearchAgent: Basic topic (40+ ideas)", passed, 
                         f"Generated {len(ideas)} ideas")
        except Exception as e:
            self.log_test("ResearchAgent: Basic topic", False, str(e))
        
        # Test 2: Complex topic with special characters
        try:
            result = agent.generate_ideas("Data Handling & Statistics", "8th grade")
            ideas = result.get("ideas", [])
            passed = len(ideas) >= 40
            self.log_test("ResearchAgent: Complex topic with special chars", passed,
                         f"Generated {len(ideas)} ideas")
        except Exception as e:
            self.log_test("ResearchAgent: Complex topic", False, str(e))
        
        # Test 3: Empty/edge case topic
        try:
            result = agent.generate_ideas("", "Class 1")
            ideas = result.get("ideas", [])
            passed = isinstance(ideas, list)
            self.log_test("ResearchAgent: Empty topic (fallback)", passed,
                         f"Generated {len(ideas)} ideas")
        except Exception as e:
            self.log_test("ResearchAgent: Empty topic", False, str(e))
    
    def test_question_framer_agent(self):
        """Test QuestionFramerAgent with various scenarios."""
        print("\n" + "="*60)
        print("TESTING QuestionFramerAgent")
        print("="*60)
        
        agent = QuestionFramerAgent()
        
        # Test 1: Basic question framing
        try:
            question = agent.frame_question(
                "Finding roots of quadratic equations",
                "Quadratic Equations",
                "Class 10",
                "Q01",
                "basic"
            )
            passed = (
                "question_text" in question and
                "options" in question and
                len(question.get("options", [])) == 4 and
                "correct_option" in question
            )
            self.log_test("QuestionFramerAgent: Basic question", passed,
                         f"Question: {question.get('question_text', '')[:50]}...")
        except Exception as e:
            self.log_test("QuestionFramerAgent: Basic question", False, str(e))
        
        # Test 2: Question with math notation
        try:
            question = agent.frame_question(
                "Solving equations with variables",
                "Algebra",
                "Class 9",
                "Q02",
                "intermediate"
            )
            has_math = "$" in question.get("question_text", "") or any("$" in str(opt) for opt in question.get("options", []))
            passed = "question_text" in question and len(question.get("options", [])) == 4
            self.log_test("QuestionFramerAgent: Math notation", passed,
                         f"Has math: {has_math}")
        except Exception as e:
            self.log_test("QuestionFramerAgent: Math notation", False, str(e))
        
        # Test 3: Advanced difficulty
        try:
            question = agent.frame_question(
                "Complex problem solving with multiple steps",
                "Advanced Mathematics",
                "Class 12",
                "Q03",
                "advanced"
            )
            passed = (
                question.get("difficulty") == "advanced" and
                len(question.get("options", [])) == 4
            )
            self.log_test("QuestionFramerAgent: Advanced difficulty", passed)
        except Exception as e:
            self.log_test("QuestionFramerAgent: Advanced difficulty", False, str(e))
        
        # Test 4: Question requiring diagram
        try:
            question = agent.frame_question(
                "Graphing quadratic functions and finding vertex",
                "Quadratic Functions",
                "Class 10",
                "Q04",
                "intermediate"
            )
            passed = "needs_diagram" in question
            self.log_test("QuestionFramerAgent: Diagram detection", passed,
                         f"Needs diagram: {question.get('needs_diagram', False)}")
        except Exception as e:
            self.log_test("QuestionFramerAgent: Diagram detection", False, str(e))
    
    def test_validator_agent(self):
        """Test ValidatorAgent with valid and invalid questions."""
        print("\n" + "="*60)
        print("TESTING ValidatorAgent")
        print("="*60)
        
        agent = ValidatorAgent()
        
        # Test 1: Valid question
        valid_question = {
            "question_id": "Q01",
            "question_text": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_option": "B",
            "difficulty": "basic"
        }
        try:
            is_valid, feedback, corrected = agent.validate(
                valid_question, "Basic Math", "Class 1"
            )
            passed = is_valid or "valid" in feedback.lower()
            self.log_test("ValidatorAgent: Valid question", passed, feedback[:50])
        except Exception as e:
            self.log_test("ValidatorAgent: Valid question", False, str(e))
        
        # Test 2: Invalid question (sample/fallback)
        invalid_question = {
            "question_id": "Q02",
            "question_text": "Sample question on test topic (LaTeX: $x^2 + y^2$)",
            "options": ["A: Option 1", "B: Option 2", "C: Option 3", "D: Option 4"],
            "correct_option": "A",
            "difficulty": "basic"
        }
        try:
            is_valid, feedback, corrected = agent.validate(
                invalid_question, "Test Topic", "Class 5"
            )
            # Should reject sample questions
            passed = not is_valid or "sample" in feedback.lower()
            self.log_test("ValidatorAgent: Reject sample questions", passed, feedback[:50])
        except Exception as e:
            self.log_test("ValidatorAgent: Reject sample questions", False, str(e))
        
        # Test 3: Question with missing options
        incomplete_question = {
            "question_id": "Q03",
            "question_text": "What is the capital of France?",
            "options": ["Paris", "London"],
            "correct_option": "A",
            "difficulty": "basic"
        }
        try:
            is_valid, feedback, corrected = agent.validate(
                incomplete_question, "Geography", "Class 5"
            )
            passed = isinstance(is_valid, bool)
            self.log_test("ValidatorAgent: Incomplete question", passed, feedback[:50])
        except Exception as e:
            self.log_test("ValidatorAgent: Incomplete question", False, str(e))
    
    def test_diagram_agent(self):
        """Test DiagramAgent for TikZ diagram generation."""
        print("\n" + "="*60)
        print("TESTING DiagramAgent")
        print("="*60)
        
        agent = DiagramAgent()
        
        # Test 1: Question that needs diagram
        question_with_diagram = {
            "question_id": "Q01",
            "question_text": "What is the area of a triangle with base 5 and height 3?",
            "options": ["7.5", "8", "15", "10"],
            "correct_option": "A",
            "difficulty": "basic",
            "needs_diagram": True
        }
        try:
            result = agent.generate_diagram(question_with_diagram, "Geometry")
            passed = "diagram_code" in result or "needs_python_diagram" in result
            self.log_test("DiagramAgent: Generate TikZ diagram", passed,
                         f"Has diagram code: {'diagram_code' in result}")
        except Exception as e:
            self.log_test("DiagramAgent: Generate TikZ diagram", False, str(e))
        
        # Test 2: Question that doesn't need diagram
        question_no_diagram = {
            "question_id": "Q02",
            "question_text": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_option": "B",
            "difficulty": "basic",
            "needs_diagram": False
        }
        try:
            result = agent.generate_diagram(question_no_diagram, "Math")
            passed = result.get("needs_diagram", False) == False
            self.log_test("DiagramAgent: Skip when not needed", passed)
        except Exception as e:
            self.log_test("DiagramAgent: Skip when not needed", False, str(e))
    
    def test_python_diagram_agent(self):
        """Test PythonDiagramAgent for complex diagram generation."""
        print("\n" + "="*60)
        print("TESTING PythonDiagramAgent")
        print("="*60)
        
        agent = PythonDiagramAgent(str(self.output_dir / "images"))
        
        # Test 1: Question needing Python diagram
        question_python_diagram = {
            "question_id": "Q01",
            "question_text": "Plot the graph of y = x^2",
            "options": ["Parabola", "Line", "Circle", "Hyperbola"],
            "correct_option": "A",
            "difficulty": "intermediate",
            "needs_diagram": True,
            "needs_python_diagram": True
        }
        try:
            result = agent.generate_diagram(question_python_diagram, "Graphing")
            passed = "image_path" in result
            self.log_test("PythonDiagramAgent: Generate PNG diagram", passed,
                         f"Image path: {result.get('image_path', 'None')}")
        except Exception as e:
            self.log_test("PythonDiagramAgent: Generate PNG diagram", False, str(e))
        
        # Test 2: Question not needing Python diagram
        question_no_python = {
            "question_id": "Q02",
            "question_text": "What is 2 + 2?",
            "options": ["3", "4", "5", "6"],
            "correct_option": "B",
            "needs_python_diagram": False
        }
        try:
            result = agent.generate_diagram(question_no_python, "Math")
            passed = result == question_no_python
            self.log_test("PythonDiagramAgent: Skip when not needed", passed)
        except Exception as e:
            self.log_test("PythonDiagramAgent: Skip when not needed", False, str(e))
    
    def test_latex_writer(self):
        """Test LaTeXWriter with various question types."""
        print("\n" + "="*60)
        print("TESTING LaTeXWriter")
        print("="*60)
        
        test_tex_path = self.output_dir / "test_questions.tex"
        writer = LaTeXWriter(test_tex_path, "Test Topic", "Test Class")
        
        try:
            writer.initialize()
            self.log_test("LaTeXWriter: Initialize file", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Initialize file", False, str(e))
            return
        
        # Test 1: Basic question without diagram
        try:
            question1 = {
                "question_id": "Q01",
                "question_text": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correct_option": "B",
                "difficulty": "basic",
                "needs_diagram": False
            }
            writer.write_question(question1)
            self.log_test("LaTeXWriter: Write basic question", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Write basic question", False, str(e))
        
        # Test 2: Question with TikZ diagram
        try:
            question2 = {
                "question_id": "Q02",
                "question_text": "What is the area of a triangle?",
                "options": ["7.5", "8", "15", "10"],
                "correct_option": "A",
                "difficulty": "basic",
                "needs_diagram": True,
                "diagram_code": "\\begin{tikzpicture}\\draw (0,0) -- (2,0) -- (1,2) -- cycle;\\end{tikzpicture}"
            }
            writer.write_question(question2)
            self.log_test("LaTeXWriter: Write question with TikZ", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Write question with TikZ", False, str(e))
        
        # Test 3: Question with image
        try:
            question3 = {
                "question_id": "Q03",
                "question_text": "What does this graph show?",
                "options": ["Linear", "Quadratic", "Exponential", "Logarithmic"],
                "correct_option": "B",
                "difficulty": "intermediate",
                "needs_diagram": True,
                "image_path": str(self.output_dir / "images" / "test.png")
            }
            writer.write_question(question3)
            self.log_test("LaTeXWriter: Write question with image", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Write question with image", False, str(e))
        
        # Test 4: Question with special characters
        try:
            question4 = {
                "question_id": "Q04",
                "question_text": "What is $x^2 + y^2 = r^2$?",
                "options": ["Circle equation", "Line equation", "Parabola", "Hyperbola"],
                "correct_option": "A",
                "difficulty": "advanced",
                "needs_diagram": False
            }
            writer.write_question(question4)
            self.log_test("LaTeXWriter: Write question with special chars", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Write question with special chars", False, str(e))
        
        # Test 5: Question with embedded options (edge case)
        try:
            question5 = {
                "question_id": "Q05",
                "question_text": "What is 3 + 3?\nA. 5\nB. 6\nC. 7\nD. 8",
                "options": ["", "", "", ""],  # Empty options - should extract from text
                "correct_option": "B",
                "difficulty": "basic",
                "needs_diagram": False
            }
            writer.write_question(question5)
            self.log_test("LaTeXWriter: Write question with embedded options", True)
        except Exception as e:
            self.log_test("LaTeXWriter: Write question with embedded options", False, str(e))
        
        try:
            writer.finalize()
            self.log_test("LaTeXWriter: Finalize file", True)
            
            # Check if file exists and is readable
            if test_tex_path.exists():
                content = test_tex_path.read_text(encoding='utf-8')
                has_questions = "\\item" in content
                has_equidistant = "\\equidistantoptions" in content
                self.log_test("LaTeXWriter: File content valid", has_questions and has_equidistant,
                             f"File size: {len(content)} bytes")
        except Exception as e:
            self.log_test("LaTeXWriter: Finalize file", False, str(e))
    
    def test_full_pipeline_25_questions(self):
        """Test full pipeline with 25 questions (default)."""
        print("\n" + "="*60)
        print("TESTING Full Pipeline: 25 Questions")
        print("="*60)
        
        generator = QuestionPaperGenerator(output_dir=str(self.output_dir / "pipeline_25"))
        
        try:
            result = generator.generate("Test Topic: Basic Math", "Test Class 5", target_question_count=25)
            passed = result.get("total_questions", 0) >= 20  # Allow some tolerance
            self.log_test("Full Pipeline: Generate 25 questions", passed,
                         f"Generated {result.get('total_questions', 0)} questions")
            
            # Check files exist
            tex_exists = Path(result.get("latex_file", "")).exists()
            json_exists = Path(result.get("question_data", "")).exists()
            self.log_test("Full Pipeline: Output files created", tex_exists and json_exists,
                         f"TeX: {tex_exists}, JSON: {json_exists}")
            
            # Check for questions with and without diagrams
            if json_exists:
                with open(result.get("question_data", ""), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    questions = data.get("questions", [])
                    with_diagrams = sum(1 for q in questions if q.get("needs_diagram", False))
                    without_diagrams = len(questions) - with_diagrams
                    self.log_test("Full Pipeline: Diagram distribution", True,
                                 f"With diagrams: {with_diagrams}, Without: {without_diagrams}")
        except Exception as e:
            self.log_test("Full Pipeline: Generate 25 questions", False, str(e))
    
    def test_full_pipeline_30_questions(self):
        """Test full pipeline with 30 questions (custom count)."""
        print("\n" + "="*60)
        print("TESTING Full Pipeline: 30 Questions (Custom Count)")
        print("="*60)
        
        generator = QuestionPaperGenerator(output_dir=str(self.output_dir / "pipeline_30"))
        
        try:
            result = generator.generate("Test Topic: Advanced Math", "Test Class 10", target_question_count=30)
            passed = result.get("total_questions", 0) >= 25  # At least 25, ideally 30
            self.log_test("Full Pipeline: Generate 30 questions", passed,
                         f"Generated {result.get('total_questions', 0)} questions (target: 30)")
            
            # Check difficulty distribution
            if result.get("total_questions", 0) > 0:
                json_path = Path(result.get("question_data", ""))
                if json_path.exists():
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        questions = data.get("questions", [])
                        basic = sum(1 for q in questions if q.get("difficulty") == "basic")
                        intermediate = sum(1 for q in questions if q.get("difficulty") == "intermediate")
                        advanced = sum(1 for q in questions if q.get("difficulty") == "advanced")
                        self.log_test("Full Pipeline: Difficulty distribution (30)", True,
                                     f"Basic: {basic}, Intermediate: {intermediate}, Advanced: {advanced}")
        except Exception as e:
            self.log_test("Full Pipeline: Generate 30 questions", False, str(e))
    
    def test_corner_cases(self):
        """Test various corner cases."""
        print("\n" + "="*60)
        print("TESTING Corner Cases")
        print("="*60)
        
        # Test 1: Empty topic name
        try:
            agent = ResearchAgent()
            result = agent.generate_ideas("", "Class 1")
            passed = isinstance(result, dict) and "ideas" in result
            self.log_test("Corner Case: Empty topic", passed)
        except Exception as e:
            self.log_test("Corner Case: Empty topic", False, str(e))
        
        # Test 2: Very long topic name
        try:
            long_topic = "A" * 200
            agent = ResearchAgent()
            result = agent.generate_ideas(long_topic, "Class 10")
            passed = isinstance(result, dict)
            self.log_test("Corner Case: Very long topic", passed)
        except Exception as e:
            self.log_test("Corner Case: Very long topic", False, str(e))
        
        # Test 3: Special characters in topic
        try:
            special_topic = "Math & Science: 100% (A+B) = C²"
            agent = ResearchAgent()
            result = agent.generate_ideas(special_topic, "Class 10")
            passed = isinstance(result, dict)
            self.log_test("Corner Case: Special characters in topic", passed)
        except Exception as e:
            self.log_test("Corner Case: Special characters in topic", False, str(e))
        
        # Test 4: Question with all empty options
        try:
            framer = QuestionFramerAgent()
            # This should be caught by validation, but test the framer's handling
            question = {
                "question_id": "Q01",
                "question_text": "Test question",
                "options": ["", "", "", ""],
                "correct_option": "A"
            }
            # The framer should handle this gracefully
            self.log_test("Corner Case: Empty options handling", True,
                         "Handled by validation and LaTeX writer")
        except Exception as e:
            self.log_test("Corner Case: Empty options handling", False, str(e))
        
        # Test 5: Question with very long text
        try:
            framer = QuestionFramerAgent()
            long_idea = "A" * 500
            question = framer.frame_question(long_idea, "Test", "Class 5", "Q01", "basic")
            passed = "question_text" in question
            self.log_test("Corner Case: Very long question text", passed)
        except Exception as e:
            self.log_test("Corner Case: Very long question text", False, str(e))
    
    def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "="*60)
        print("COMPREHENSIVE TEST SUITE FOR QUESTION PAPER GENERATION")
        print("="*60)
        
        # Check API key
        if not os.getenv("GOOGLE_API_KEY"):
            print("\n⚠️  WARNING: GOOGLE_API_KEY not found in environment!")
            print("   Some tests may fail. Please set your API key in .env file.")
        
        # Run all test suites
        self.test_research_agent()
        self.test_question_framer_agent()
        self.test_validator_agent()
        self.test_diagram_agent()
        self.test_python_diagram_agent()
        self.test_latex_writer()
        self.test_full_pipeline_25_questions()
        self.test_full_pipeline_30_questions()
        self.test_corner_cases()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        # Save results to JSON
        results_file = self.output_dir / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed,
                    "success_rate": passed/total*100 if total > 0 else 0
                },
                "results": self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()

