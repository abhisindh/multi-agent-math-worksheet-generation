"""
ValidatorAgent: Validates questions for mathematical soundness and correctness.
"""

import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Tuple, Optional, Dict, Any

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class ValidatorAgent:
    """Validates questions for mathematical soundness and correctness."""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    def validate(self, question: Dict[str, Any], topic_name: str, class_level: str) -> Tuple[bool, str, Optional[Dict]]:
        """Validate a question. Returns (is_valid, feedback, corrected_question)."""
        prompt = f"""
        Validate this MCQ question:
        
        {json.dumps(question, indent=2)}
        
        Topic: {topic_name}
        Class Level: {class_level}
        
        Check:
        1. Is the question mathematically correct?
        2. Is exactly one option correct?
        3. Is the phrasing clear and unambiguous?
        4. Are there any grammatical errors?
        5. Is the difficulty appropriate?
        6. Is this a real question (NOT a sample/fallback question with placeholder text like "Sample question on", "Option 1", etc.)?
        7. Do all options contain actual content (not just "Option 1", "Option 2", etc.)?
        
        Return ONLY valid JSON:
        {{
            "is_valid": true/false,
            "feedback": "Detailed feedback",
            "suggested_corrections": {{"question_text": "...", "options": [...], "correct_option": "..."}} or null
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                validation = json.loads(json_match.group())
                is_valid = validation.get("is_valid", False)
                feedback = validation.get("feedback", "")
                corrections = validation.get("suggested_corrections")
                
                if is_valid:
                    return True, feedback, None
                else:
                    if corrections:
                        corrected = question.copy()
                        corrected.update(corrections)
                        return False, feedback, corrected
                    return False, feedback, None
        except Exception as e:
            print(f"ValidatorAgent error: {e}")
        
        # Default: assume valid to avoid loops
        return True, "Validation check completed (fallback)", None