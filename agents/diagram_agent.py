"""
DiagramAgent: Detects and generates diagrams for questions.
"""

import json
import re
import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class DiagramAgent:
    """Generates TikZ/PGFPlots diagrams for questions."""
    
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    def generate_diagram(self, question: Dict[str, Any], topic_name: str) -> Dict[str, Any]:
        """Generate diagram code for a question if needed."""
        if not question.get("needs_diagram", False):
            return question
        
        prompt = f"""
        Generate a LaTeX TikZ or PGFPlots diagram for this question:
        
        {question.get("question_text", "")}
        Topic: {topic_name}
        
        If the diagram is simple (graphs, basic geometry), provide TikZ code.
        If complex (data visualization, network graphs), set needs_python_diagram: true.
        
        Return JSON:
        {{
            "diagram_code": "\\begin{{tikzpicture}}...\\end{{tikzpicture}}",
            "needs_python_diagram": false,
            "insert_position": "below question"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                diagram_info = json.loads(json_match.group())
                question["diagram_code"] = diagram_info.get("diagram_code", "")
                question["needs_python_diagram"] = diagram_info.get("needs_python_diagram", False)
                question["insert_position"] = diagram_info.get("insert_position", "below question")
                return question
        except Exception as e:
            print(f"DiagramAgent error: {e}")
        
        # Default: no diagram
        question["diagram_code"] = ""
        question["needs_python_diagram"] = False
        return question