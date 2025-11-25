"""
LaTeXWriter: Handles incremental writing of LaTeX file using the provided worksheet package template.
Assumes 'worksheet.sty' is available in the same directory as the generated .tex file.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any


class LaTeXWriter:
    """Handles incremental writing of LaTeX file using worksheet template."""
    
    def __init__(self, output_path: Path, topic_name: str, class_level: str):
        self.output_path = output_path
        self.topic_name = topic_name
        self.class_level = class_level
        self.question_count = 0
        self.answer_key = []
        self.file_handle = None
        
    def initialize(self):
        """Initialize the LaTeX file with header and preamble, using the worksheet package."""
        self.file_handle = open(self.output_path, 'w', encoding='utf-8')
        
        # Write full document preamble assuming worksheet.sty exists
        header = f"""\\documentclass[a4paper,12pt]{{article}}

\\usepackage{{worksheet}}  % Custom package for worksheet formatting (see worksheet.sty)

% Additional packages if needed (already included in worksheet.sty)
\\usepackage{{amsmath}}  % For enhanced math support

% Metadata - set via worksheet commands
\\setsubject{{Mathematics}}
\\setclass{{{self.class_level}}}
\\setworksheettitle{{{self.topic_name}}}

\\begin{{document}}

\\makeworksheetheader

\\begin{{enumerate}}[label=\\textbf{{\\Alph*}}., leftmargin=*, itemsep=6pt]

"""
        self.file_handle.write(header)
        self.file_handle.flush()
    
    def write_question(self, question: Dict[str, Any]):
        """Write a single question to the LaTeX file immediately, using \\equidistantoptions."""
        if self.file_handle is None:
            raise RuntimeError("LaTeX file not initialized. Call initialize() first.")
        
        self.question_count += 1
        question_text = question.get("question_text", "")
        options = question.get("options", [])
        correct_option = question.get("correct_option", "A")
        
        # Clean options - remove any existing labels like "A)", "B)", etc.
        cleaned_options = []
        for opt in options:
            # Remove patterns like "A) ", "B) ", "(A) ", etc.
            cleaned = re.sub(r'^[\(]?[A-D]\)?[\)\.]?\s*', '', str(opt).strip())
            # Basic LaTeX escaping for special chars (simplified)
            cleaned = cleaned.replace('&', '\\&').replace('%', '\\%').replace('$', '\\$').replace('#', '\\#').replace('_', '\\_').replace('{', '\\{').replace('}', '\\}')
            cleaned_options.append(cleaned)
        
        # Ensure exactly 4 options
        while len(cleaned_options) < 4:
            cleaned_options.append('\\ldots (incomplete option)')
        cleaned_options = cleaned_options[:4]
        
        # Write question
        self.file_handle.write(f"  % Question {self.question_count}\n")
        self.file_handle.write(f"  \\item {question_text}\n")
        
        # Add diagram if present (TikZ code)
        if question.get("diagram_code"):
            self.file_handle.write(f"  \\begin{{center}}\n  {question['diagram_code']}\n  \\end{{center}}\n\n")
        # Add image if present (Python-generated PNG)
        elif question.get("image_path"):
            image_path = question["image_path"].replace("\\", "/")  # Normalize for LaTeX
            self.file_handle.write(f"  \\begin{{center}}\n  \\includegraphics[width=0.8\\textwidth]{{{image_path}}}\n  \\end{{center}}\n\n")
        
        # Write options using \\equidistantoptions from worksheet package
        self.file_handle.write(f"  \\equidistantoptions{{{cleaned_options[0]}}}{{{cleaned_options[1]}}}{{{cleaned_options[2]}}}{{{cleaned_options[3]}}}\n\n")
        
        # Store answer key entry
        self.answer_key.append((self.question_count, correct_option))
        
        # Flush to disk immediately
        self.file_handle.flush()
    
    def finalize(self):
        """Close the LaTeX file and optionally add an answer key section."""
        if self.file_handle is None:
            return
        
        # Close enumerate and document
        footer = """\\end{enumerate}

% Optional Answer Key Section (uncomment to include)
% \\newpage
% \\section*{Answer Key}
"""
        for q_num, opt in self.answer_key:
            footer += f"\\textbf{{Q{q_num}:}} {opt}\\\\ \n"
        footer += """

\\end{document}
"""
        self.file_handle.write(footer)
        self.file_handle.close()
        self.file_handle = None