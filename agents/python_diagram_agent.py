"""
PythonDiagramAgent: Generates complex diagrams using Python (matplotlib, etc.).
"""

import json
import re
import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import numpy as np

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


class PythonDiagramAgent:
    """Generates complex diagrams using Python (matplotlib, etc.)."""
    
    def __init__(self, output_dir: str = "question_paper/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    def generate_diagram(self, question: Dict[str, Any], topic_name: str) -> Dict[str, Any]:
        """Generate a Python-based diagram and save it."""
        if not question.get("needs_python_diagram", False):
            return question
        
        question_id = question.get("question_id", "Q00")
        question_text = question.get("question_text", "")
        
        prompt = f"""
        Generate Python code using matplotlib to create a diagram for:
        
        Question: {question_text}
        Topic: {topic_name}
        
        The code should:
        1. Create a clear, publication-quality figure
        2. Save it as PNG with high DPI (300)
        3. Use appropriate styling for academic papers
        4. Include labels, titles if needed
        
        Return ONLY the Python code (no markdown, no explanations).
        Assume plt, np are imported.
        """
        
        try:
            response = self.model.generate_content(prompt)
            code = response.text.strip()
            
            # Extract code block
            code_match = re.search(r'```python\n(.*?)\n```', code, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            
            # Execute code safely
            image_path = self.output_dir / f"diagram_{question_id.lower()}.png"
            
            exec_globals = {'plt': plt, 'np': np}
            # Append save if missing
            if 'plt.savefig' not in code:
                code += f'\nplt.savefig(r"{image_path}", dpi=300, bbox_inches="tight")\nplt.close()'
            
            exec(code, exec_globals)
            
            question["image_path"] = str(image_path)
            return question
            
        except Exception as e:
            print(f"PythonDiagramAgent error: {e}")
            # Placeholder image
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, f'Diagram for {question_id}', ha='center', va='center', fontsize=14)
            ax.axis('off')
            image_path = self.output_dir / f"diagram_{question_id.lower()}.png"
            plt.savefig(str(image_path), dpi=300, bbox_inches='tight')
            plt.close()
            question["image_path"] = str(image_path)
            return question