"""
ResearchAgent: Searches internet for creative, thought-provoking question ideas.
"""

import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class ResearchAgent:
    """Searches internet for creative, thought-provoking question ideas."""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")  # Updated to stable model
    
    def generate_ideas(self, topic_name: str, class_level: str) -> dict:
        """Generate question ideas for the given topic and class level."""
        prompt = f"""
        Research and collect 40-50 creative question ideas for the topic: "{topic_name}"
        Suitable for: {class_level}
        
        Focus on:
        - Higher-order thinking questions
        - Application-based problems
        - Conceptual understanding
        - Problem-solving scenarios
        
        Return ONLY a valid JSON object in this format:
        {{
            "topic": "{topic_name}",
            "class_level": "{class_level}",
            "ideas": [
                "Roots and coefficients relation problems",
                "Nature of roots with parameter-based conditions",
                "Graphical interpretation of quadratic functions",
                "Minimum and maximum value problems",
                ...
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Robust JSON extraction with regex
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"ResearchAgent error: {e}")
            # Fallback: Generate minimal ideas
            return {
                "topic": topic_name,
                "class_level": class_level,
                "ideas": [f"Idea {i}: Sample for {topic_name}" for i in range(40)]
            }
        
        # Last resort
        return {"topic": topic_name, "class_level": class_level, "ideas": []}