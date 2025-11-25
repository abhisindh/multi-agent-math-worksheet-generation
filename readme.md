# Autonomous Multi-Agent System for Automatic Math Worksheet Generation

## Overview
This project implements a sophisticated multi-agent system powered by Google's Gemini API (gemini-2.5-flash-lite) to automatically generate LaTeX-formatted question papers with 25 validated multiple-choice questions (MCQs) on any given mathematics topic. The system uses an autonomous loop-based architecture where specialized agents collaborate to research, frame, validate, enhance with diagrams, and incrementally write questions to LaTeX format.

**Key Features:**
- **Intelligent Research**: Generates 40-50 creative question ideas using AI-powered brainstorming focused on higher-order thinking, application-based problems, and conceptual understanding
- **Structured Question Framing**: Converts ideas into well-formatted MCQs with exactly 4 options, LaTeX math notation support, and controlled difficulty distribution (32% basic, 40% intermediate, 28% advanced)
- **Rigorous Validation**: Validates each question for mathematical correctness, clarity, and appropriateness with up to 5 retry attempts and automatic corrections
- **Visual Enhancement**: Automatically detects when diagrams are needed and generates either TikZ/PGFPlots code for simple diagrams or Python/Matplotlib-generated PNG images for complex visualizations
- **Incremental Output**: Writes questions to LaTeX file in real-time as they are validated, ensuring progress is saved throughout the generation process
- **Dual Output Formats**: Produces both a compilable `.tex` file and a structured `question_data.json` file with complete question metadata and answer keys

## Architecture

**Architecture Diagram** (Text-based):
```
┌─────────────────────────────────────────────────────────────────┐
│                    User Input: Topic, Class Level               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             v
                    ┌─────────────────┐
                    │ ResearchAgent   │
                    │ (40-50 ideas)   │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │ QuestionFramer  │
                    │ Agent (MCQs)    │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │ ValidatorAgent  │◄──┐
                    │ (5 retries max) │   │ Loop-back on failure
                    └────────┬────────┘   │
                             │            │
                    ┌────────┴────────┐   │
                    │  Valid?         │───┘
                    └────────┬────────┘
                             │ Yes
                             v
                    ┌─────────────────┐
                    │ DiagramAgent    │
                    │ (TikZ/PGFPlots) │
                    └────────┬────────┘
                             │
                             v (if complex)
                    ┌─────────────────┐
                    │ PythonDiagram   │
                    │ Agent (PNG)     │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │ LaTeXWriter     │
                    │ (Incremental)   │
                    └────────┬────────┘
                             │
                             v
            ┌────────────────┴────────────────┐
            │  .tex file + question_data.json │
            └─────────────────────────────────┘
```

**Workflow:**
1. **Research Phase**: `ResearchAgent` generates 40-50 question ideas for the topic
2. **Framing Phase**: `QuestionFramerAgent` converts each idea into a structured MCQ
3. **Validation Loop**: `ValidatorAgent` checks correctness; if invalid, the question is corrected and re-validated (up to 5 attempts)
4. **Diagram Generation**: If needed, `DiagramAgent` creates TikZ code; complex diagrams trigger `PythonDiagramAgent` to generate PNG images
5. **Incremental Writing**: Each validated question is immediately written to the LaTeX file by `LaTeXWriter`
6. **Completion**: Process continues until 25 validated questions are generated, then finalizes the LaTeX file and saves JSON metadata

## Agents Explained

### ResearchAgent
- **Purpose**: Generates 40-50 creative and thought-provoking question ideas for the given topic and class level
- **Method**: Uses Gemini API to brainstorm ideas focused on higher-order thinking, application-based problems, and conceptual understanding
- **Output**: JSON object containing an array of question idea strings
- **Fallback**: If API fails, generates minimal placeholder ideas to ensure the pipeline continues
- **Location**: `agents/research_agent.py`

### QuestionFramerAgent
- **Purpose**: Converts question ideas into fully-framed MCQs with proper structure
- **Features**:
  - Creates questions with LaTeX math notation support (`$...$` or `$$...$$`)
  - Generates exactly 4 options labeled A, B, C, D
  - Assigns appropriate difficulty level (basic/intermediate/advanced)
  - Detects if a diagram is needed and sets `needs_diagram` flag
- **Output**: JSON object with question text, options, correct answer, difficulty, and metadata
- **Location**: `agents/question_framer_agent.py`

### ValidatorAgent
- **Purpose**: Ensures mathematical correctness and quality of generated questions
- **Validation Checks**:
  1. Mathematical correctness
  2. Exactly one correct option
  3. Clear and unambiguous phrasing
  4. Grammatical accuracy
  5. Appropriate difficulty level for class
- **Retry Logic**: Up to 5 validation attempts per question with automatic corrections
- **Output**: Validation status, feedback, and optionally a corrected question object
- **Location**: `agents/validator_agent.py`

### DiagramAgent
- **Purpose**: Generates LaTeX TikZ or PGFPlots code for visual questions
- **Strategy**: 
  - Attempts TikZ/PGFPlots for simple diagrams (graphs, basic geometry)
  - Flags complex diagrams for Python generation via `needs_python_diagram` flag
- **Output**: Adds `diagram_code` field to question object with LaTeX code
- **Location**: `agents/diagram_agent.py`

### PythonDiagramAgent
- **Purpose**: Creates complex diagrams using Matplotlib when TikZ is insufficient
- **Method**: Generates Python code to create diagrams, saves as PNG images
- **Output**: Adds `image_path` field to question object pointing to saved PNG file
- **Location**: Images saved in `question_paper/images/` directory
- **Location**: `agents/python_diagram_agent.py`

### LaTeXWriter
- **Purpose**: Incrementally writes validated questions to LaTeX file in real-time
- **Features**:
  - Uses custom `worksheet.sty` package for professional formatting
  - Handles both TikZ code and image inclusions
  - Formats options using enumerate with alphabetic labels
  - Maintains answer key for later reference
- **Output**: Complete `.tex` file ready for compilation with `pdflatex`
- **Location**: `writers/latex_writer.py`

## Project Structure

```
QP agent/
├── main.py                      # Main orchestrator and entry point
├── utils.py                     # Utility functions
├── requirements.txt             # Python dependencies
├── readme.md                    # This file
├── agents/
│   ├── __init__.py
│   ├── research_agent.py        # ResearchAgent implementation
│   ├── question_framer_agent.py # QuestionFramerAgent implementation
│   ├── validator_agent.py       # ValidatorAgent implementation
│   ├── diagram_agent.py         # DiagramAgent implementation
│   └── python_diagram_agent.py  # PythonDiagramAgent implementation
├── writers/
│   ├── __init__.py
│   └── latex_writer.py          # LaTeXWriter implementation
└── question_paper/
    ├── worksheet.sty            # Custom LaTeX package for formatting
    ├── school_header.png        # Optional header image
    ├── images/                  # Generated diagram images (PNG)
    └── question_data.json       # Output: Question metadata and answer key
```

## Setup Instructions

### Prerequisites
- Python 3.7 or higher
- LaTeX distribution (for compiling `.tex` files): [MiKTeX](https://miktex.org/) (Windows) or [TeX Live](https://www.tug.org/texlive/) (Linux/Mac)
- Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd "QP agent"
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   ```
   - **Windows**: `venv\Scripts\activate`
   - **Linux/Mac**: `source venv/bin/activate`

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **Dependencies include:**
   - `google-generativeai==0.8.3` - Google Gemini API client
   - `python-dotenv==1.0.1` - Environment variable management
   - `matplotlib==3.9.2` - Diagram generation
   - `numpy==2.1.1` - Numerical computations for diagrams
   - `pathlib` - Path handling
   - `regex` - Pattern matching

4. **Configure API Key**:
   - Create a `.env` file in the project root directory
   - Add your Google Gemini API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```
   - **Note**: The `.env` file is not tracked by git (should be in `.gitignore`)

## Usage

### Basic Usage

**Generate a question paper with default topic**:
```bash
python main.py
```
- Default topic: "Congruence of Triangles, AREA AND PERIMETER"
- Default class: "Class 7"

**Generate a question paper with custom topic and class**:
```bash
python main.py "Quadratic Equations" "Class 10"
```

**Generate LaTeX from existing JSON file**:
```bash
python main.py "Topic Name" "Class Level" --from-json question_paper/question_data.json
```
- Useful for regenerating LaTeX without re-running the full generation process
- Skips question generation and validation, only runs LaTeX writer

### Command-Line Arguments

- `topic` (optional): The mathematics topic for question generation (default: "Congruence of Triangles, AREA AND PERIMETER")
- `class_level` (optional): The class/grade level (default: "Class 7")
- `--from-json` (optional): Path to existing `question_data.json` file to regenerate LaTeX only

### Output Files

After running the generator, you'll find:

1. **LaTeX File**: `question_paper/<topic>_<class>.tex`
   - Compilable LaTeX document
   - Uses custom `worksheet.sty` package
   - Includes all 25 questions with proper formatting

2. **Question Data JSON**: `question_paper/question_data.json`
   - Complete question metadata
   - Answer key
   - Question structure for programmatic access

3. **Images Directory**: `question_paper/images/`
   - PNG images generated by `PythonDiagramAgent`
   - Referenced in LaTeX file via `\includegraphics`

### Compiling LaTeX

**Using pdflatex** (command line):
```bash
cd question_paper
pdflatex <topic>_<class>.tex
```

**Using Overleaf** (online):
1. Upload the `.tex` file to Overleaf
2. Upload the `worksheet.sty` file
3. Upload all images from the `images/` directory
4. Compile in Overleaf

**Note**: The LaTeX file uses the `worksheet.sty` package which provides:
- Professional page borders
- Custom header formatting with school logo support
- Equidistant option formatting for MCQs
- Proper spacing and typography

## Example Output

### LaTeX Sample (excerpt):
```latex
\begin{enumerate}
  \item If $\alpha$ and $\beta$ are the roots of $x^2 + px + q = 0$, then the value of $\alpha^2 + \beta^2$ is:
  \begin{enumerate}[label=\Alph*)]
    \item $p^2 - 2q$
    \item $p^2 + 2q$
    \item $2q - p^2$
    \item $p^2 / q$
  \end{enumerate}
\end{enumerate}
```

### JSON Structure:
```json
{
  "topic": "Quadratic Equations",
  "class_level": "Class 10",
  "total_questions": 25,
  "questions": [
    {
      "question_id": "Q01",
      "question_text": "If $\\alpha$ and $\\beta$ are the roots...",
      "options": ["$p^2 - 2q$", "$p^2 + 2q$", "$2q - p^2$", "$p^2 / q$"],
      "correct_option": "A",
      "difficulty": "intermediate",
      "needs_diagram": false
    }
  ],
  "answer_key": [
    ["Q01", "A"],
    ["Q02", "B"],
    ...
  ]
}
```

## Technical Details

### Difficulty Distribution
- **Basic**: 8 questions (32%)
- **Intermediate**: 10 questions (40%)
- **Advanced**: 7 questions (28%)

### Validation Retry Logic
- Maximum 5 validation attempts per question
- Automatic correction application when available
- Questions that fail after 5 attempts are skipped
- System continues until 25 validated questions are generated

### Diagram Generation Strategy
1. `QuestionFramerAgent` sets `needs_diagram: true` if visual aid is needed
2. `DiagramAgent` attempts TikZ/PGFPlots generation first
3. If diagram is too complex, sets `needs_python_diagram: true`
4. `PythonDiagramAgent` generates PNG image using Matplotlib
5. LaTeX writer includes either TikZ code or image reference

### File Naming Convention
- LaTeX files: `<topic>_<class>.tex` (spaces and special characters replaced with underscores, lowercase)
- Example: `congruence_of_triangles_area_and_perimeter_class_7.tex`

## Limitations & Future Improvements

### Current Limitations
- **API Dependency**: Relies on Google Gemini API (subject to rate limits and costs)
- **No Real Web Search**: Research phase uses AI brainstorming rather than actual web scraping
- **Basic Diagram Detection**: Diagram necessity is determined by AI, may miss some cases
- **Manual LaTeX Compilation**: Requires separate LaTeX installation and compilation step
- **Fixed Question Count**: Currently hardcoded to generate exactly 25 questions

### Planned Improvements
- ✅ **CLI with argparse**: Already implemented in `main.py`
- 🔄 **Streamlit UI**: Web interface for easier interaction
- 🔄 **Auto-PDF Generation**: Automatic PDF compilation via `latexmk` or similar
- 🔄 **Unit Tests**: pytest-based testing for JSON parsing, validation logic, etc.
- 🔄 **Real Search API Integration**: Integrate actual web search APIs (e.g., SerpAPI, Google Custom Search)
- 🔄 **Configurable Question Count**: Allow users to specify number of questions
- 🔄 **Multiple Output Formats**: Support for DOCX, HTML, or other formats
- 🔄 **Question Bank Management**: Database storage and retrieval of generated questions
- 🔄 **Batch Processing**: Generate multiple question papers in one run

## Troubleshooting

### Common Issues

**API Key Error**:
- Ensure `.env` file exists in project root
- Verify `GOOGLE_API_KEY` is set correctly
- Check for extra spaces or quotes in the `.env` file

**LaTeX Compilation Errors**:
- Ensure `worksheet.sty` is in the `question_paper/` directory
- Verify all required LaTeX packages are installed
- Check image paths if diagrams are included

**Import Errors**:
- Activate virtual environment before running
- Reinstall dependencies: `pip install -r requirements.txt`

**Validation Failures**:
- Some questions may fail validation after 5 attempts (this is normal)
- System will continue generating until 25 valid questions are created
- Check console output for specific error messages

## License
MIT License. Contributions welcome!

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request. Areas for contribution:
- Additional diagram generation strategies
- Enhanced validation logic
- Support for more question types (short answer, fill-in-the-blank, etc.)
- Performance optimizations
- Documentation improvements
