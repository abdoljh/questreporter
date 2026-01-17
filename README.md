# Academic Report Writer Pro

**Version 3.2 - Professional Research Report Generator**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B)](https://streamlit.io/)
[![Anthropic](https://img.shields.io/badge/Claude-Sonnet%204-purple)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An intelligent academic research report generator that autonomously researches topics, evaluates sources, and produces professional PDF-ready reports with proper citations in APA or IEEE format.

## 🎯 Overview

Academic Report Writer Pro leverages Claude AI to automate the entire research report writing process:

- **Autonomous Research**: Searches academic databases and trusted sources (.edu, .gov, IEEE, ACM, arXiv)
- **Source Validation**: Credibility scoring system filters high-quality academic sources
- **Professional Writing**: Generates comprehensive reports with proper structure and citations
- **Citation Management**: Automatic formatting in APA or IEEE styles with metadata extraction
- **Quality Assurance**: Built-in critique and refinement pipeline
- **PDF Export**: HTML output optimized for professional PDF conversion

## ✨ Features

### Core Capabilities

- ✅ **Intelligent Topic Analysis** - Generates research plan with subtopics and targeted queries
- ✅ **Web Research Integration** - Searches academic sources using Claude's web search tool
- ✅ **Credibility Scoring** - Prioritizes .edu, .gov, IEEE, Nature, Science, ACM, arXiv
- ✅ **Smart Metadata Extraction** - Extracts titles, authors, years, venues without excessive API calls
- ✅ **Multi-Section Reports** - Abstract, Introduction, Literature Review, Analysis, Challenges, Future Outlook, Conclusion
- ✅ **Citation Formatting** - APA and IEEE citation styles with proper bibliography
- ✅ **Phrase Variation** - Avoids repetitive writing through intelligent synonym usage
- ✅ **Progress Tracking** - Real-time updates with execution time monitoring
- ✅ **Error Recovery** - Robust retry logic with exponential backoff

### Version 3.2 Improvements

- 🔧 **Fixed Metadata Extraction** - Proper title cleaning and validation
- 🔧 **Batch Title Processing** - Single API call for multiple titles (significant optimization)
- 🔧 **Smart Title Cleaning** - Removes markdown artifacts and validates content
- 🔧 **Domain-Based Venues** - Automatic venue detection from URL domains
- 🔧 **Execution Time Tracking** - Precise timing with minutes and seconds display
- 🔧 **Enhanced Phrase Variation** - Stronger enforcement to avoid topic repetition

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Anthropic API key with Claude Sonnet 4 access
- Internet connection for web research

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/academic-report-writer.git
cd academic-report-writer
```

2. **Install dependencies**
```bash
pip install streamlit requests
```

3. **Configure API Key**

Create a `.streamlit/secrets.toml` file:
```toml
ANTHROPIC_API_KEY = "your-api-key-here"
```

Or set as environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

4. **Run the application**
```bash
streamlit run streamlit_app.py
```

5. **Access the interface**
```
Open your browser to: http://localhost:8501
```

## 📖 Usage Guide

### Step 1: Configure Report

Fill in the required fields:

- **Topic**: Research subject (e.g., "Quantum Computing", "Climate Change Mitigation")
- **Subject**: Academic discipline (e.g., "Computer Science", "Environmental Science")
- **Researcher**: Your name
- **Institution**: Your university/organization
- **Date**: Report date
- **Citation Style**: APA or IEEE

### Step 2: Generate Report

Click **"🚀 Generate Report"** and wait 6-8 minutes while the system:

1. **Analyzes Topic** (30 seconds) - Creates research plan with subtopics
2. **Conducts Research** (3-4 minutes) - Searches 5 academic queries
3. **Extracts Titles** (20 seconds) - Batch processes source metadata
4. **Writes Draft** (2 minutes) - Generates 8-section report
5. **Quality Check** (5 seconds) - Validates citations and content
6. **Final Refinement** (10 seconds) - Polishes and formats

### Step 3: Download & Convert

1. Download the HTML report
2. Open in any web browser
3. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (Mac)
4. Select "Save as PDF"
5. Adjust margins if needed
6. Save your professional PDF report

## 🏗️ Architecture

### System Layers

```
┌─────────────────────────────────────────────┐
│         PRESENTATION LAYER                  │
│  • Streamlit UI                             │
│  • Session State Management                 │
│  • Progress Tracking                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       ORCHESTRATION LAYER                   │
│  • Pipeline Executor                        │
│  • Progress Management                      │
│  • State Control                            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       BUSINESS LOGIC LAYER                  │
│  • Topic Analysis                           │
│  • Web Research                             │
│  • Source Processing                        │
│  • Draft Generation                         │
│  • Quality Assurance                        │
│  • Citation Management                      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        INTEGRATION LAYER                    │
│  • Anthropic API Client                     │
│  • Web Search Tool                          │
│  • Rate Limiting & Retry                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           DATA LAYER                        │
│  • Research Data                            │
│  • Report Structures                        │
│  • Source Metadata                          │
│  • HTML Output                              │
└─────────────────────────────────────────────┘
```

See `architecture.svg` for detailed visual architecture diagram.

## 🔧 Configuration

### Trusted Domains

The system prioritizes sources from:

| Domain Type | Credibility Score | Examples |
|-------------|-------------------|----------|
| Educational | 95% | .edu domains |
| Government | 95% | .gov domains |
| Academic Publishers | 90-95% | Nature, Science, IEEE, ACM |
| Preprint Servers | 90% | arXiv.org |
| Academic Databases | 85% | ScienceDirect, Wiley |

### Rejected Domains

The following domains are automatically filtered:

- ResearchGate.net
- Academia.edu
- Scribd.com
- Medium.com

### Rate Limiting

- **Minimum delay**: 5 seconds between API calls
- **429 handling**: Exponential backoff (20s, 40s, 60s)
- **Max retries**: 3 attempts per request
- **Timeout**: 120 seconds per API call

## 📊 Performance Metrics

### Typical Execution

- **Total Time**: 6-8 minutes
- **API Calls**: 8-12 calls total
  - 1 call: Topic analysis
  - 5 calls: Web research (one per query)
  - 1 call: Batch title extraction
  - 1 call: Draft generation
- **Sources Found**: 10-12 high-quality academic sources
- **Output Size**: 50-100 KB HTML (~8-12 pages PDF)

### Resource Usage

- **Memory**: ~200-300 MB
- **Network**: ~5-10 MB download (search results)
- **Storage**: ~100 KB per report

## 🎓 Report Structure

Generated reports include:

1. **Cover Page**
   - Title
   - Subject
   - Researcher information
   - Institution
   - Date
   - Citation format

2. **Executive Summary**
   - High-level overview
   - Source count
   - Key findings summary

3. **Abstract** (150-250 words)
   - Research scope
   - Methodology
   - Main conclusions

4. **Introduction**
   - Topic background
   - Research objectives
   - Report structure

5. **Literature Review**
   - Source synthesis
   - Key themes
   - Research landscape

6. **Main Sections** (3-4 sections)
   - Covers each subtopic in depth
   - Data-driven analysis
   - Citation-backed claims

7. **Data & Analysis**
   - Statistical information
   - Trends and patterns
   - Empirical evidence

8. **Challenges**
   - Current limitations
   - Research gaps
   - Practical obstacles

9. **Future Outlook**
   - Emerging trends
   - Research directions
   - Predictions

10. **Conclusion**
    - Summary of findings
    - Implications
    - Final remarks

11. **References**
    - APA or IEEE formatted
    - Complete bibliographic information
    - Clickable URLs

## 💡 Tips for Best Results

### Topic Selection

✅ **Good Topics**:
- "Machine Learning in Healthcare"
- "Renewable Energy Technologies"
- "Blockchain Security"
- "Climate Change Adaptation Strategies"

❌ **Avoid**:
- Too broad: "Science"
- Too narrow: "Algorithm XYZ version 2.3.1"
- Non-academic: "Best restaurants in Paris"
- Very new topics (< 6 months old)

### Optimization

1. **Be Specific**: "Deep Learning for Medical Imaging" > "AI in Medicine"
2. **Use Established Terms**: Use standard academic terminology
3. **Academic Focus**: Ensure topic has scholarly research available
4. **Moderate Scope**: Not too broad, not too niche

## 🐛 Troubleshooting

### Common Issues

#### "Only X sources found. Need 3+"

**Cause**: Topic too niche or search terms ineffective

**Solutions**:
- Broaden your topic slightly
- Use more common terminology
- Try a related but more established topic
- Retry (search results vary)

#### Rate Limiting Errors

**Cause**: API usage limits exceeded

**Solutions**:
- Wait 5-10 minutes before retrying
- Check API key quota
- Reduce frequency of report generation

#### Timeout During Processing

**Cause**: Network issues or API latency

**Solutions**:
- Normal execution is 6-8 minutes - be patient
- Don't refresh the page during processing
- Check internet connection
- Retry if timeout > 15 minutes

#### Poor Quality Sources

**Cause**: Topic lacks academic research

**Solutions**:
- Verify topic has scholarly publications
- Add more specific academic context
- Check topic spelling and terminology

## 🔐 Security & Privacy

- **API Keys**: Store securely in secrets.toml (never commit to git)
- **Data Storage**: All data stored in session state (not persisted)
- **Privacy**: No user data collected or transmitted except to Anthropic API
- **Rate Limiting**: Prevents excessive API usage

## 📝 Citation Formats

### APA Example
```
Author, A. (2024). Title of the Paper. Journal Name. 
Retrieved from https://example.edu/paper
```

### IEEE Example
```
[1] A. Author, "Title of the Paper," Journal Name, 2024. 
Available: https://example.edu/paper
```

## 🛠️ Development

### Project Structure

```
academic-report-writer/
├── streamlit_app.py           # Main application
├── README.md                  # This file
├── architecture.svg           # System architecture diagram
├── requirements.txt           # Python dependencies
├── .streamlit/
│   └── secrets.toml          # API configuration (not in git)
└── .gitignore                # Git ignore rules
```

### Key Functions

- `execute_research_pipeline()` - Main orchestration function
- `analyze_topic_with_ai()` - Topic analysis and query generation
- `execute_web_research_optimized()` - Web search with source validation
- `extract_metadata_from_context()` - Smart metadata extraction
- `batch_extract_titles_only()` - Efficient title extraction
- `generate_draft_optimized()` - Report writing with citations
- `generate_html_report_optimized()` - HTML/PDF generation

### Dependencies

```txt
streamlit>=1.28.0
requests>=2.31.0
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional citation formats (MLA, Chicago)
- More domain credibility rules
- Enhanced source validation
- Multi-language support
- Export to DOCX/LaTeX
- Custom report templates

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **Anthropic** - Claude AI platform and API
- **Streamlit** - Web application framework
- **Academic Community** - For establishing citation standards

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/academic-report-writer/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/academic-report-writer/wiki)
- **Email**: support@example.com

## 🗺️ Roadmap

### Version 3.3 (Planned)
- [ ] DOCX export support
- [ ] Custom citation styles
- [ ] Multi-language reports
- [ ] Source quality scoring enhancements

### Version 4.0 (Future)
- [ ] Collaborative editing
- [ ] Version control for reports
- [ ] Advanced statistical analysis
- [ ] Integration with reference managers (Zotero, Mendeley)

## ⚡ Quick Reference

| Feature | Details |
|---------|---------|
| **Execution Time** | 6-8 minutes |
| **API Calls** | 8-12 total |
| **Sources** | 10-12 academic sources |
| **Output Format** | HTML (PDF-ready) |
| **Citation Styles** | APA, IEEE |
| **Models Used** | Claude Sonnet 4 |
| **Rate Limit** | 5s between calls |
| **Max Retries** | 3 attempts |

---

**Version 3.2** | Built with ❤️ using Claude AI | Last Updated: January 2026
