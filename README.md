This README.md provides an overview of the Online Report Writer System based on the architecture and logic found in the source code. It details the autonomous research pipeline and how to set up the environment for testing.
📝 Online Report Writer System
An autonomous research and report generation pipeline that transforms a single topic into a comprehensive, academic-grade research report. The system utilizes a multi-agent approach to handle everything from initial topic analysis to final refinement and PDF/HTML export.
🚀 The Autonomous Pipeline
The system executes a six-stage sequential workflow:
 * Topic Analysis: Decomposes the topic into 5-7 research dimensions and generates 15 diverse search queries.
 * Parallel Web Research: Executes queries and filters results through a credibility scoring system.
 * Draft Generation: Synthesizes gathered data into a formal academic report (approx. 3000-4000 words) with inline citations.
 * Critique: A secondary agent reviews the draft for fact consistency, bias, and structural issues.
 * Refinement: Applies editorial improvements, improves academic tone, and adds an executive summary.
 * Export: Generates a professional document with a cover page and a structured reference list.
🛠️ Features
 * Trusted Source Verification: Prioritizes domains like .edu, .gov, .org, and major scientific journals.
 * Credibility Scoring: Automatically assigns quality scores to sources to ensure academic integrity.
 * Quality Metrics: Provides an "Overall Quality Score" and research statistics (Avg Quality, Source Count).
 * Academic Formatting: Outputs reports in a standard format including Abstract, Literature Review, and Data Analysis.
🔧 Installation & Setup
To run this system (Streamlit version), follow these steps:
1. Clone the Repository
git clone <your-repository-url>
cd online-report-writer

2. Install Dependencies
Ensure you have Python installed, then run:
pip install -r requirements.txt

3. Set Up API Keys
The system requires an Anthropic API key to access the claude-sonnet-4-20250514 model. Create a .env file or provide the key in the application sidebar:
ANTHROPIC_API_KEY=your_api_key_here

4. Run the Application
streamlit run app.py

📊 Technical Stack
 * Frontend: React (original source) / Streamlit (for testing).
 * AI Model: Anthropic Claude Sonnet 3.5 (2025-05-14 variant).
 * Tools: Web Search Tool web_search_20250305.
 * Icons: Lucide-React.
Would you like me to help you configure the GitHub Actions for automated deployment to Streamlit Cloud?
