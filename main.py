"""
Autonomous Loop-Based Multi-Agent Architecture for Mathematical Question Paper Generation
Orchestrates agents to generate LaTeX-formatted question papers with 25 validated MCQs.
"""

import sys
import argparse
import json  # NEW: For loading JSON
from pathlib import Path
from dotenv import load_dotenv

from agents.research_agent import ResearchAgent
from agents.question_framer_agent import QuestionFramerAgent
from agents.validator_agent import ValidatorAgent
from agents.diagram_agent import DiagramAgent
from agents.python_diagram_agent import PythonDiagramAgent
from writers.latex_writer import LaTeXWriter

load_dotenv()  # Load environment variables from .env file


class QuestionPaperGenerator:
    """Main orchestrator for the loop-based multi-agent system."""
    
    def __init__(self, output_dir: str = "question_paper"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        
        self.research_agent = ResearchAgent()
        self.question_framer = QuestionFramerAgent()
        self.validator = ValidatorAgent()
        self.diagram_agent = DiagramAgent()
        self.python_diagram_agent = PythonDiagramAgent(str(self.output_dir / "images"))
        
        self.validated_questions = []
        self.question_ideas = []
        self.latex_writer = None
    
    def generate(self, topic_name: str, class_level: str, target_question_count: int = 25) -> dict:
        """Main generation loop that continues until target_question_count validated questions are produced."""
        
        print(f"🚀 Starting question paper generation for: {topic_name} - {class_level}")
        
        # Initialize LaTeX file for incremental writing
        # Generate base filename (without extension) for both .tex and .json files
        base_filename = f"{topic_name.replace(' ', '_').replace(',', '').replace('-', '_').lower()}_{class_level.lower().replace(' ', '_')}"
        main_tex_path = self.output_dir / f"{base_filename}.tex"
        self.latex_writer = LaTeXWriter(main_tex_path, topic_name, class_level)
        self.latex_writer.initialize()
        print(f"📝 Initialized LaTeX file: {main_tex_path}")
        
        # Step 1: Research and Idea Generation
        print("\n📚 Step 1: Researching question ideas...")
        research_result = self.research_agent.generate_ideas(topic_name, class_level)
        self.question_ideas = research_result.get("ideas", [])
        print(f"✅ Generated {len(self.question_ideas)} question ideas")
        
        # Step 2-4: Loop until we have 25 validated questions
        print("\n🔄 Starting question generation and validation loop...")
        print("   (Questions will be written to LaTeX file as they are created)\n")
        
        idea_index = 0
        question_counter = 0
        max_iterations = 200  # Safety limit
        iteration = 0
        
        # Calculate difficulty distribution based on target count
        basic_count = int(target_question_count * 0.32)
        intermediate_count = int(target_question_count * 0.40)
        advanced_count = target_question_count - basic_count - intermediate_count
        difficulty_distribution = (["basic"] * basic_count + 
                                  ["intermediate"] * intermediate_count + 
                                  ["advanced"] * advanced_count)
        difficulty_index = 0
        
        while len(self.validated_questions) < target_question_count and iteration < max_iterations:
            iteration += 1
            
            if idea_index >= len(self.question_ideas):
                # Regenerate ideas if we run out
                print("   ⚠️  Running low on ideas, generating more...")
                research_result = self.research_agent.generate_ideas(topic_name, class_level)
                self.question_ideas.extend(research_result.get("ideas", []))
                idea_index = 0  # Reset to use new ideas
            
            # Get next idea
            idea = self.question_ideas[idea_index]
            idea_index = (idea_index + 1) % len(self.question_ideas)  # Cycle if needed
            question_counter += 1
            question_id = f"Q{question_counter:02d}"
            
            # Get difficulty
            difficulty = difficulty_distribution[difficulty_index % len(difficulty_distribution)]
            difficulty_index += 1
            
            print(f"   🔨 Generating question {question_counter} (attempt {iteration})...")
            
            # Step 2: Question Framing
            try:
                question = self.question_framer.frame_question(
                    idea, topic_name, class_level, question_id, difficulty
                )
            except Exception as e:
                print(f"      ❌ Failed to frame question: {e}")
                continue  # Skip this question and try the next idea
            
            # Step 3: Validation (with loop-back)
            max_validation_attempts = 5
            validation_attempt = 0
            is_valid = False
            
            while not is_valid and validation_attempt < max_validation_attempts:
                validation_attempt += 1
                is_valid, feedback, corrected_question = self.validator.validate(
                    question, topic_name, class_level
                )
                
                if not is_valid:
                    print(f"      ⚠️  Validation failed (attempt {validation_attempt}): {feedback[:50]}...")
                    if corrected_question:
                        question = corrected_question
                    else:
                        # Regenerate question with feedback
                        try:
                            question = self.question_framer.frame_question(
                                f"{idea} [Feedback: {feedback}]", 
                                topic_name, class_level, question_id, difficulty
                            )
                        except Exception as e:
                            print(f"      ❌ Failed to regenerate question: {e}")
                            is_valid = False
                            break  # Exit validation loop
                else:
                    print(f"      ✅ Question validated!")
            
            if not is_valid:
                print(f"      ❌ Question {question_counter} failed validation after {max_validation_attempts} attempts, skipping...")
                continue
            
            # Step 4: Diagram Generation
            question["needs_diagram"] = question.get("needs_diagram", False)  # Ensure key exists
            if question["needs_diagram"]:
                print(f"      🎨 Generating diagram...")
                question = self.diagram_agent.generate_diagram(question, topic_name)
                
                if question.get("needs_python_diagram", False):
                    question = self.python_diagram_agent.generate_diagram(question, topic_name)
            
            # Add to validated questions
            self.validated_questions.append(question)
            
            # Step 5: Write question to LaTeX file immediately
            print(f"      📝 Writing question to LaTeX file...")
            self.latex_writer.write_question(question)
            
            print(f"   ✅ Question {len(self.validated_questions)}/{target_question_count} completed and written to file")
        
        if len(self.validated_questions) < target_question_count:
            print(f"\n⚠️  Warning: Only generated {len(self.validated_questions)} questions (target: {target_question_count})")
        
        # Finalize LaTeX file
        print("\n✨ Finalizing LaTeX file...")
        self.latex_writer.finalize()
        
        # Save question data as JSON (includes answer key via correct_options)
        # Use the same base filename as the LaTeX file
        question_data_path = self.output_dir / f"{base_filename}.json"
        with open(question_data_path, 'w', encoding='utf-8') as f:
            json.dump({
                "topic": topic_name,
                "class_level": class_level,
                "questions": self.validated_questions,
                "total_questions": len(self.validated_questions),
                "answer_key": [(q["question_id"], q["correct_option"]) for q in self.validated_questions]
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Question paper generation complete!")
        print(f"   📄 LaTeX file: {main_tex_path}")
        print(f"   📊 Question data: {question_data_path}")
        print(f"   🖼️  Images: {self.output_dir / 'images'}")
        print(f"\n💡 To compile: pdflatex {main_tex_path}")
        
        return {
            "latex_file": str(main_tex_path),
            "question_data": str(question_data_path),
            "images_dir": str(self.output_dir / "images"),
            "total_questions": len(self.validated_questions)
        }

    # NEW: Method to run only LaTeX writer from existing JSON
    def generate_from_json(self, json_path: str, topic_name: str, class_level: str) -> dict:
        """Load validated questions from JSON and write only to LaTeX."""
        print(f"📂 Loading questions from JSON: {json_path}")
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.validated_questions = data.get("questions", [])
            print(f"✅ Loaded {len(self.validated_questions)} questions")
            
            if len(self.validated_questions) == 0:
                raise ValueError("No questions found in JSON file.")
            
            # Use provided topic/class or fallback to JSON metadata
            topic_name = topic_name or data.get("topic", "Unknown Topic")
            class_level = class_level or data.get("class_level", "Unknown Class")
            
            # Initialize and write
            # Generate base filename (without extension) for both .tex and .json files
            base_filename = f"{topic_name.replace(' ', '_').replace(',', '').replace('-', '_').lower()}_{class_level.lower().replace(' ', '_')}"
            main_tex_path = self.output_dir / f"{base_filename}.tex"
            self.latex_writer = LaTeXWriter(main_tex_path, topic_name, class_level)
            self.latex_writer.initialize()
            print(f"📝 Initialized LaTeX file: {main_tex_path}")
            
            for i, question in enumerate(self.validated_questions, 1):
                print(f"📝 Writing question {i}/{len(self.validated_questions)}...")
                # Handle potential missing keys gracefully
                question.setdefault("needs_diagram", False)
                if question.get("needs_diagram"):
                    # Skip diagram gen if from JSON (assume already handled; or re-run if needed)
                    print("   ⚠️  Skipping diagram generation (pre-generated assumed).")
                self.latex_writer.write_question(question)
            
            self.latex_writer.finalize()
            print(f"\n✨ LaTeX generation from JSON complete!")
            print(f"   📄 LaTeX file: {main_tex_path}")
            print(f"\n💡 To compile: pdflatex {main_tex_path}")
            
            return {
                "latex_file": str(main_tex_path),
                "total_questions": len(self.validated_questions)
            }
        except Exception as e:
            print(f"❌ Error loading/generating from JSON: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Generate math question paper using multi-agents.")
    parser.add_argument("topic", nargs="?", default="Congruence of Triangles, AREA AND PERIMETER", help="Topic name")
    parser.add_argument("class_level", nargs="?", default="Class 7", help="Class level")
    parser.add_argument("--from-json", type=str, help="Path to existing question_data.json (skips generation, runs only LaTeX writer)")
    parser.add_argument("--count", type=int, default=25, help="Target number of questions to generate (default: 25)")
    args = parser.parse_args()
    
    generator = QuestionPaperGenerator()
    
    if args.from_json:
        # Run only LaTeX writer
        result = generator.generate_from_json(args.from_json, args.topic, args.class_level)
    else:
        # Full generation
        result = generator.generate(args.topic, args.class_level, args.count)
    
    print(f"\n🎉 Success! Processed {result['total_questions']} questions.")


if __name__ == "__main__":
    main()