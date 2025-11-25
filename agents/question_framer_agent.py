"""
QuestionFramerAgent: Converts question ideas into fully framed MCQs with 4 options.
"""

import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class QuestionFramerAgent:
    """Converts question ideas into fully framed MCQs with 4 options."""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    def frame_question(self, idea: str, topic_name: str, class_level: str, question_id: str, 
                      difficulty_target: str = "intermediate") -> Dict[str, Any]:
        """Frame a single MCQ from an idea. Retries up to 3 times on failure."""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                prompt = f"""
                Convert this question idea into a complete MCQ:
                
                Idea: {idea}
                Topic: {topic_name}
                Class Level: {class_level}
                Difficulty: {difficulty_target}
                Question ID: {question_id}
                
                Create a well-framed MCQ with:
                1. Clear question statement (use LaTeX for math: $...$ or $$...$$)
                2. Exactly 4 options WITHOUT labels (just the option text, no "A:", "B:", etc.)
                3. One correct option (specify as "A", "B", "C", or "D")
                4. Options should be plausible but only one is correct
                5. Do NOT include options in the question_text - keep them separate
                
                Return ONLY valid JSON (no markdown, no code blocks):
                {{
                    "question_id": "{question_id}",
                    "question_text": "If α and β are the roots of x² + px + q = 0, then the value of α² + β² is:",
                    "options": ["p² - 2q", "p² + 2q", "2q - p²", "p² / q"],
                    "correct_option": "A",
                    "difficulty": "{difficulty_target}",
                    "needs_diagram": false
                }}
                """
                
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                
                # Remove markdown code blocks if present
                result_text = re.sub(r'```json\s*', '', result_text)
                result_text = re.sub(r'```\s*', '', result_text)
                
                # Extract JSON - try multiple patterns
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if not json_match:
                    # Try more aggressive pattern
                    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                
                if json_match:
                    try:
                        question = json.loads(json_match.group())
                        
                        # Validate the question structure
                        if not isinstance(question, dict):
                            raise ValueError("Question is not a dictionary")
                        
                        # Check for required fields
                        if "question_text" not in question or not question["question_text"]:
                            raise ValueError("Missing or empty question_text")
                        
                        if "options" not in question or not isinstance(question["options"], list):
                            raise ValueError("Missing or invalid options")
                        
                        # Check if it's a fallback/sample question
                        question_text_lower = question.get("question_text", "").lower()
                        if "sample question" in question_text_lower or "option 1" in question_text_lower:
                            raise ValueError("Detected fallback/sample question")
                        
                        # Ensure exactly 4 options
                        options = question.get("options", [])
                        if len(options) < 4:
                            # Pad with placeholder if needed
                            while len(options) < 4:
                                options.append("N/A")
                            question["options"] = options
                        elif len(options) > 4:
                            question["options"] = options[:4]
                        
                        # Clean options - remove labels if present
                        cleaned_options = []
                        for opt in question["options"]:
                            opt_str = str(opt).strip()
                            # Remove leading labels like "A.", "A)", "A:", etc.
                            opt_str = re.sub(r'^[A-D][\.\)\:\s]+', '', opt_str, flags=re.IGNORECASE)
                            cleaned_options.append(opt_str)
                        question["options"] = cleaned_options
                        
                        # Ensure correct_option is valid
                        if "correct_option" not in question or question["correct_option"] not in ["A", "B", "C", "D"]:
                            question["correct_option"] = "A"
                        
                        question["question_id"] = question_id
                        question["difficulty"] = difficulty_target
                        question.setdefault("needs_diagram", False)
                        
                        return question
                    except json.JSONDecodeError as e:
                        print(f"QuestionFramerAgent JSON decode error (attempt {attempt + 1}/{max_attempts}): {e}")
                        if attempt < max_attempts - 1:
                            continue
                    except ValueError as e:
                        print(f"QuestionFramerAgent validation error (attempt {attempt + 1}/{max_attempts}): {e}")
                        if attempt < max_attempts - 1:
                            continue
                
            except Exception as e:
                print(f"QuestionFramerAgent error (attempt {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    continue
        
        # If all attempts failed, raise an exception instead of returning fallback
        raise ValueError(f"Failed to generate question after {max_attempts} attempts for idea: {idea[:50]}...")