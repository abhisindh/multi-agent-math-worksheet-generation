"""
LaTeXWriter: Handles incremental writing of LaTeX file using worksheet template.
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
    
    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape LaTeX special characters in text for use inside command arguments."""
        if not text:
            return text
        
        # Escape special LaTeX characters
        # Use a character-by-character approach to avoid double-escaping issues
        text = str(text)
        result = []
        i = 0
        while i < len(text):
            char = text[i]
            if char == '\\':
                # Check if it's already part of a LaTeX command (like \textbackslash)
                # For simplicity, just escape it as textbackslash
                result.append('\\textbackslash{}')
            elif char == '{':
                result.append('\\{')
            elif char == '}':
                result.append('\\}')
            elif char == '$':
                result.append('\\$')
            elif char == '&':
                result.append('\\&')
            elif char == '%':
                result.append('\\%')
            elif char == '#':
                result.append('\\#')
            elif char == '^':
                result.append('\\textasciicircum{}')
            elif char == '_':
                result.append('\\_')
            elif char == '~':
                result.append('\\textasciitilde{}')
            else:
                result.append(char)
            i += 1
        
        return ''.join(result)
        
    def initialize(self):
        """Initialize the LaTeX file with header and preamble using worksheet.sty package."""
        self.file_handle = open(self.output_path, 'w', encoding='utf-8')
        
        # Write header using worksheet.sty package
        # Note: worksheet.sty must be in the same directory as the generated .tex file
        header = f"""\\documentclass[a4paper,12pt]{{article}}

\\usepackage{{worksheet}}  % Custom worksheet package (worksheet.sty must be in same directory)

% Metadata - set via worksheet.sty commands
\\setsubject{{Mathematics}}
\\setclass{{{self.class_level}}}
\\setworksheettitle{{{self.topic_name}}}

\\begin{{document}}

\\makeworksheetheader

\\begin{{enumerate}}

"""
        self.file_handle.write(header)
        self.file_handle.flush()
    
    def write_question(self, question: Dict[str, Any]):
        """Write a single question to the LaTeX file immediately."""
        if self.file_handle is None:
            raise RuntimeError("LaTeX file not initialized. Call initialize() first.")
        
        self.question_count += 1
        question_text = question.get("question_text", "")
        options = question.get("options", [])
        correct_option = question.get("correct_option", "A")
        
        # Clean options - remove labels and handle edge cases
        cleaned_options = []
        for opt in options:
            if not opt or opt.strip() == "":
                cleaned_options.append("\\ldots (incomplete)")
                continue
            opt_str = str(opt).strip()
            # Remove leading labels like "A.", "A)", "A:", "A ", etc.
            opt_str = re.sub(r'^[\(]?[A-D]\)?[\)\.\:\s]+', '', opt_str, flags=re.IGNORECASE)
            # If after cleaning it's empty or just ":", use placeholder
            if not opt_str or opt_str == ":" or opt_str.startswith(": "):
                cleaned_options.append("\\ldots (incomplete)")
            else:
                cleaned_options.append(opt_str)
        
        # Ensure exactly 4 options
        while len(cleaned_options) < 4:
            cleaned_options.append("\\ldots (incomplete)")
        cleaned_options = cleaned_options[:4]
        
        # Check if question text contains embedded options (like Q07)
        # If options are empty or all placeholders, try to extract from question text
        embedded_options_found = False
        if all(opt == "\\ldots (incomplete)" or opt == "" for opt in cleaned_options):
            # Try to extract options from question text if they're embedded
            embedded_options = re.findall(r'([A-D]\.\s+[^\n]+)', question_text, re.IGNORECASE)
            if len(embedded_options) >= 4:
                # Extract the option text (remove the label)
                for i, emb_opt in enumerate(embedded_options[:4]):
                    cleaned_options[i] = re.sub(r'^[A-D]\.\s+', '', emb_opt, flags=re.IGNORECASE).strip()
                embedded_options_found = True
        
        # Remove embedded options from question text if they were found
        if embedded_options_found:
            # Remove the embedded options section from question text
            question_text = re.sub(r'\n[A-D]\.\s+[^\n]+(\n[A-D]\.\s+[^\n]+){3}', '', question_text, flags=re.IGNORECASE)
            question_text = question_text.strip()
        
        # Write question
        self.file_handle.write(f"  % Question {self.question_count}\n")
        self.file_handle.write(f"  \\item {question_text}\n")
        
        # Add diagram/image
        if question.get("diagram_code"):
            self.file_handle.write(f"  \\begin{{center}}\n  {question['diagram_code']}\n  \\end{{center}}\n")
        elif question.get("image_path"):
            # Convert absolute path to relative path from .tex file location
            image_path = Path(question["image_path"])
            # If image is in question_paper/images/, use relative path
            if "images" in str(image_path):
                # Extract just the images/filename.png part
                image_path_str = str(image_path).replace("\\", "/")
                if "images/" in image_path_str:
                    image_path_str = "images/" + image_path_str.split("images/")[-1]
                else:
                    image_path_str = image_path.name
            else:
                image_path_str = image_path.name
            self.file_handle.write(f"  \\begin{{center}}\n  \\includegraphics[width=0.8\\textwidth]{{{image_path_str}}}\n  \\end{{center}}\n")
        
        # Escape LaTeX special characters in options
        escaped_options = [self.escape_latex(opt) for opt in cleaned_options]
        
        # Write options using \equidistantoptions from worksheet.sty
        # This command automatically formats options in a table layout
        # Use string formatting instead of f-strings to avoid brace conflicts
        if len(escaped_options) == 4:
            # Use .format() to avoid issues with braces in the options
            option_line = "  \\equidistantoptions{{{}}}{{{}}}{{{}}}{{{}}}\n\n".format(
                escaped_options[0],
                escaped_options[1],
                escaped_options[2],
                escaped_options[3]
            )
            self.file_handle.write(option_line)
        else:
            # Fallback to enumerate if not exactly 4 options
            self.file_handle.write("  \\begin{{enumerate}}[label=\\Alph*)]\n")
            for i, opt in enumerate(escaped_options, 1):
                self.file_handle.write(f"    \\item {opt}\n")
            self.file_handle.write("  \\end{{enumerate}}\n\n")
        
        # Store answer key
        self.answer_key.append((self.question_count, correct_option))
        
        self.file_handle.flush()
    
    def finalize(self):
        """Close the LaTeX file and write answer key if needed."""
        if self.file_handle is None:
            return
        
        # Close enumerate and document
        footer = """\\end{enumerate}

% Answer Key (optional, commented out)
% \\section*{Answer Key}
% """
        for q_num, opt in self.answer_key:
            footer += f"Q{q_num}: {opt} \\\\ \n"
        footer += """

\\end{document}
"""
        self.file_handle.write(footer)
        self.file_handle.close()
        self.file_handle = None