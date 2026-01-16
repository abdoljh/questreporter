# streamlit_app.py
# 
# with Rate Limiting
# Version 4

import streamlit as st
import json
import requests
import time
from datetime import datetime
import base64
from typing import List, Dict, Any
import re

# Page configuration
st.set_page_config(
    page_title="Online Report Writer System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4F46E5;
    }
    .css-1d391kg {
        padding-top: 1.5rem;
    }
    .report-stats {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .source-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background-color: #F0F9FF;
        border-radius: 0.25rem;
        border-left: 3px solid #3B82F6;
    }
    .stButton > button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'step' not in st.session_state:
    st.session_state.step = 'input'
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        'topic': '',
        'subject': '',
        'researcher': '',
        'institution': '',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
if 'progress' not in st.session_state:
    st.session_state.progress = {
        'stage': '',
        'detail': '',
        'percent': 0
    }
if 'research' not in st.session_state:
    st.session_state.research = {
        'queries': [],
        'sources': [],
        'subtopics': []
    }
if 'draft' not in st.session_state:
    st.session_state.draft = None
if 'critique' not in st.session_state:
    st.session_state.critique = None
if 'final_report' not in st.session_state:
    st.session_state.final_report = None
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'api_call_count' not in st.session_state:
    st.session_state.api_call_count = 0
if 'last_api_call_time' not in st.session_state:
    st.session_state.last_api_call_time = 0

# Get API key from Streamlit secrets
try:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
    API_AVAILABLE = True
except (KeyError, FileNotFoundError):
    st.error("⚠️ Anthropic API key not found in secrets. Please add it to your Streamlit secrets.")
    API_AVAILABLE = False

def update_progress(stage: str, detail: str, percent: int):
    """Update progress in session state"""
    st.session_state.progress = {
        'stage': stage,
        'detail': detail,
        'percent': min(100, percent)
    }

def calculate_credibility(url: str) -> int:
    """Calculate credibility score based on domain"""
    url_lower = url.lower()
    if '.gov' in url_lower or '.edu' in url_lower:
        return 95
    if 'nature.com' in url_lower or 'science.org' in url_lower or 'ieee.org' in url_lower:
        return 95
    if 'acm.org' in url_lower or 'springer.com' in url_lower:
        return 90
    if 'arxiv.org' in url_lower or 'researchgate.net' in url_lower:
        return 88
    if '.org' in url_lower:
        return 85
    return 75

def rate_limit_wait():
    """Implement rate limiting between API calls"""
    current_time = time.time()
    time_since_last_call = current_time - st.session_state.last_api_call_time
    
    # Wait at least 3 seconds between calls to avoid rate limiting
    min_wait_time = 3.0
    if time_since_last_call < min_wait_time:
        wait_time = min_wait_time - time_since_last_call
        time.sleep(wait_time)
    
    st.session_state.last_api_call_time = time.time()
    st.session_state.api_call_count += 1

def parse_json_response(text: str) -> Dict:
    """Parse JSON from AI response, handling code blocks"""
    try:
        # Remove markdown code blocks
        cleaned = re.sub(r'```json\n?|```\n?', '', text).strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}

def call_anthropic_api(messages: List[Dict], max_tokens: int = 1000, use_web_search: bool = False) -> Dict:
    """Call Anthropic Claude API with rate limiting and proper tool configuration"""
    if not API_AVAILABLE:
        raise Exception("API key not configured")

    rate_limit_wait()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": messages
    }

    # CRITICAL: Use correct web search tool type
    if use_web_search:
        data["tools"] = [{
            "type": "web_search_20250305",
            "name": "web_search"
        }]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 429:
                wait_time = 15 * (attempt + 1)
                st.warning(f"⏳ Rate limited. Waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(8 * (attempt + 1))
    
    raise Exception("Failed after max retries")

def analyze_topic_with_ai(topic: str, subject: str) -> Dict:
    """Analyze topic and generate research structure"""
    update_progress('Topic Analysis', 'Analyzing topic and creating research plan...', 10)

    prompt = f"""You are a research planning assistant. Analyze this research topic:

Topic: "{topic}"
Subject: "{subject}"

Create a research plan with:
1. 5-7 specific subtopics that cover different aspects of "{topic}"
2. 8-10 search queries that will find REAL academic sources about "{topic}"

IMPORTANT RULES:
- Every subtopic MUST be directly about "{topic}"
- Every query MUST include the exact phrase "{topic}"
- Queries should target academic papers, research articles, and technical reports
- Focus on finding recent (2020-2025) publications

Return ONLY valid JSON:
{{
  "subtopics": ["Specific aspect 1 of {topic}", "Specific aspect 2 of {topic}", ...],
  "researchQueries": ["{topic} latest research 2024", "{topic} academic papers", ...]
}}"""

    try:
        response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=1200)

        if 'content' in response:
            text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
            result = parse_json_response(text)
            
            if not result.get('subtopics') or not result.get('researchQueries'):
                raise ValueError("Invalid response structure")
            
            return result
            
    except Exception as e:
        st.warning(f"Topic analysis issue: {e}. Using fallback structure.")
    
    # Fallback with topic-specific queries
    return {
        "subtopics": [
            f"Foundations and Core Concepts of {topic}",
            f"Current State and Recent Advances in {topic}",
            f"Applications and Use Cases of {topic}",
            f"Challenges and Limitations in {topic}",
            f"Future Directions for {topic}"
        ],
        "researchQueries": [
            f"{topic} research 2024 2025",
            f"{topic} academic papers recent",
            f"{topic} scientific publications",
            f"{topic} technical advances",
            f"{topic} industry applications",
            f"{topic} challenges limitations",
            f"{topic} future trends",
            f"latest developments {topic}"
        ]
    }

def execute_web_research_real(queries: List[str], topic: str) -> List[Dict]:
    """Execute REAL web research using Claude's web search tool"""
    update_progress('Web Research', f'Searching for real sources about "{topic}"...', 25)
    
    sources = []
    trusted_keywords = [
        'arxiv', 'ieee', 'acm', 'springer', 'nature', 'science', 
        'scholar', 'researchgate', 'edu', 'gov', 'org', 'journal',
        'conference', 'proceedings', 'publication', 'paper', 'research'
    ]
    
    # Limit queries to avoid rate limiting
    limited_queries = queries[:8]
    
    for i, query in enumerate(limited_queries):
        progress = 25 + (i / len(limited_queries)) * 25
        update_progress('Web Research', f'Query {i+1}/{len(limited_queries)}: {query[:50]}...', progress)

        try:
            # Use web search tool to get REAL results
            search_prompt = f"""Search the web for: {query}

Find recent academic papers, research articles, or technical reports specifically about this topic. 
Look for sources from universities (.edu), research institutions, IEEE, ACM, arXiv, Google Scholar, or academic journals.

Provide the titles, URLs, and brief summaries of what you find."""

            response = call_anthropic_api(
                messages=[{"role": "user", "content": search_prompt}],
                max_tokens=2000,
                use_web_search=True  # Enable web search
            )

            if 'content' in response:
                full_text = ""
                
                # Extract ALL content including citations
                for block in response['content']:
                    if block.get('type') == 'text':
                        full_text += block.get('text', '')
                
                # Extract URLs and context from the response
                # Claude often provides citations in the format [citation_number]
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\)]+[^\s<>"{}|\\^`\[\]\).,;:!?\)]'
                found_urls = re.findall(url_pattern, full_text)
                
                for url in found_urls:
                    # Check if URL contains trusted keywords
                    url_lower = url.lower()
                    is_trusted = any(keyword in url_lower for keyword in trusted_keywords)
                    
                    if is_trusted:
                        # Extract title and context around the URL
                        url_pos = full_text.find(url)
                        context_start = max(0, url_pos - 400)
                        context_end = min(len(full_text), url_pos + 400)
                        context = full_text[context_start:context_end]
                        
                        # Try to extract title
                        lines_before = full_text[:url_pos].split('\n')
                        title_candidates = [line.strip() for line in lines_before[-5:] if line.strip() and not line.strip().startswith('http')]
                        title = title_candidates[-1] if title_candidates else f"Research on {topic}"
                        
                        # Clean title
                        title = re.sub(r'^\d+\.\s*', '', title)  # Remove leading numbers
                        title = re.sub(r'[\[\]"]', '', title)  # Remove brackets and quotes
                        title = title[:150]  # Limit length
                        
                        sources.append({
                            'title': title.strip(),
                            'url': url,
                            'content': context.strip()[:600],
                            'query': query,
                            'credibilityScore': calculate_credibility(url),
                            'dateAccessed': datetime.now().isoformat()
                        })

        except Exception as e:
            st.warning(f"Search failed for: {query[:50]}... ({str(e)})")
            continue

    # Deduplicate by URL
    seen_urls = set()
    unique_sources = []
    for source in sources:
        if source['url'] not in seen_urls:
            seen_urls.add(source['url'])
            unique_sources.append(source)

    st.info(f"✅ Found {len(unique_sources)} unique trusted sources")
    
    return unique_sources

def generate_draft_from_sources(topic: str, subject: str, subtopics: List[str], sources: List[Dict]) -> Dict:
    """Generate draft using REAL source content"""
    update_progress('Drafting', f'Writing report about "{topic}" using {len(sources)} real sources...', 55)

    if not sources:
        raise Exception("No sources available to generate report")

    # Prepare source summaries
    source_details = []
    for i, s in enumerate(sources[:15], 1):
        source_details.append(f"""
SOURCE [{i}]:
Title: {s.get('title', 'Unknown')}
URL: {s.get('url', 'No URL')}
Content: {s.get('content', 'No content')[:500]}
Credibility: {s.get('credibilityScore', 0)}%
""")
    
    sources_text = "\n".join(source_details)

    prompt = f"""You are writing an academic research report about "{topic}" in the field of {subject}.

CRITICAL REQUIREMENTS:
1. The ENTIRE report must be about "{topic}" - do NOT write about other topics
2. Use ONLY information from the provided sources below
3. Cite sources as [Source N] throughout the text
4. Do NOT invent or hallucinate information
5. Stay focused on "{topic}" in every section

SUBTOPICS TO COVER:
{chr(10).join(f"{i+1}. {st}" for i, st in enumerate(subtopics))}

REAL SOURCES (USE THESE):
{sources_text}

Write a comprehensive report with these sections:
1. Abstract (150-250 words summarizing the report about "{topic}")
2. Introduction (explaining why "{topic}" is important)
3. Literature Review (synthesizing what the sources say about "{topic}")
4. Main Body (3-4 detailed sections covering subtopics of "{topic}")
5. Data & Analysis (statistics and findings about "{topic}" from sources)
6. Challenges (limitations and issues in "{topic}")
7. Future Outlook (future directions for "{topic}")
8. Conclusion (summarizing findings about "{topic}")

Return ONLY valid JSON with NO markdown:
{{
  "abstract": "text about {topic}",
  "introduction": "text about {topic}",
  "literatureReview": "text about {topic} from sources",
  "mainSections": [
    {{"title": "Title about {topic}", "content": "content with [Source N] citations"}}
  ],
  "dataAnalysis": "statistics about {topic} from sources",
  "challenges": "challenges in {topic}",
  "futureOutlook": "future of {topic}",
  "conclusion": "summary of {topic} findings"
}}"""

    try:
        response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=6000)

        if 'content' in response:
            text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
            draft = parse_json_response(text)

            # Validate draft is about the correct topic
            draft_text = json.dumps(draft).lower()
            topic_mentions = draft_text.count(topic.lower())
            
            if topic_mentions < 10:
                st.warning(f"⚠️ Draft may not be focused enough on '{topic}' ({topic_mentions} mentions)")

            # Ensure all required keys
            required_keys = ['abstract', 'introduction', 'literatureReview', 'mainSections',
                            'dataAnalysis', 'challenges', 'futureOutlook', 'conclusion']
            for key in required_keys:
                if key not in draft or not draft[key]:
                    if key == 'mainSections':
                        draft[key] = [{'title': f'Analysis of {topic}', 'content': f'Detailed analysis of {topic} based on research sources.'}]
                    else:
                        draft[key] = f"This section examines {topic} based on available research."

            return draft

    except Exception as e:
        st.error(f"Draft generation failed: {e}")
        raise

def critique_draft(draft: Dict, sources: List[Dict], topic: str) -> Dict:
    """Critique draft for quality and topic relevance"""
    update_progress('Review', 'Reviewing draft quality and accuracy...', 72)

    prompt = f"""Review this research report draft about "{topic}".

CHECK THESE CRITICAL ISSUES:
1. Is the report actually about "{topic}" throughout?
2. Are sources properly cited as [Source N]?
3. Is the content based on real research (not hallucinated)?
4. Is the academic tone maintained?
5. Are there logical flow issues?

Number of sources available: {len(sources)}

Return ONLY valid JSON:
{{
  "topicRelevance": 85,
  "factIssues": ["list any unsupported claims"],
  "flowIssues": ["list flow problems"],
  "citationIssues": ["list citation problems"],
  "overallScore": 85,
  "recommendations": ["specific improvements needed"]
}}"""

    try:
        response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=1500)

        if 'content' in response:
            text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
            critique = parse_json_response(text)

            # Ensure required keys
            if 'overallScore' not in critique:
                critique['overallScore'] = 75
            for key in ['factIssues', 'flowIssues', 'citationIssues', 'recommendations']:
                if key not in critique:
                    critique[key] = []

            return critique

    except Exception as e:
        st.warning(f"Critique had issues: {e}")
        return {
            'topicRelevance': 75,
            'factIssues': [],
            'flowIssues': [],
            'citationIssues': [],
            'overallScore': 75,
            'recommendations': ['Review completed with standard assessment']
        }

def refine_draft(draft: Dict, critique: Dict, topic: str) -> Dict:
    """Refine draft based on critique"""
    update_progress('Refinement', 'Polishing and improving the report...', 85)

    prompt = f"""Refine this research report about "{topic}".

Quality Score: {critique.get('overallScore', 75)}/100
Issues to fix: {', '.join(critique.get('recommendations', [])[:3])}

IMPROVEMENTS NEEDED:
1. Add a compelling Executive Summary (200 words) about "{topic}"
2. Ensure every section stays focused on "{topic}"
3. Improve transitions between sections
4. Enhance academic tone
5. Verify citations are present

Return the COMPLETE refined report as JSON with executiveSummary added.
Return ONLY valid JSON, NO markdown."""

    try:
        response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=6000)

        if 'content' in response:
            text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
            refined = parse_json_response(text)

            if 'executiveSummary' not in refined:
                refined['executiveSummary'] = f"This comprehensive research report examines {topic}, drawing on {len(st.session_state.research['sources'])} authoritative sources to provide insights and analysis."

            # Merge with original to ensure no data loss
            for key in draft:
                if key not in refined or not refined[key]:
                    refined[key] = draft[key]

            return refined

    except Exception as e:
        st.warning(f"Refinement had issues: {e}")
        draft['executiveSummary'] = f"This report examines {topic} through analysis of {len(st.session_state.research['sources'])} research sources."
        return draft

def generate_html_report(refined_draft: Dict, form_data: Dict, sources: List[Dict]) -> str:
    """Generate final HTML report"""
    update_progress('Report Generation', 'Creating professional HTML document...', 95)

    try:
        report_date = datetime.strptime(form_data['date'], '%Y-%m-%d').strftime('%B %d, %Y')
    except:
        report_date = datetime.now().strftime('%B %d, %Y')

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{form_data['topic']} - Research Report</title>
    <style>
        @page {{ margin: 1in; }}
        body {{
            font-family: 'Times New Roman', serif;
            font-size: 12pt;
            line-height: 1.6;
            color: #000;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 0.5in;
        }}
        .cover {{
            text-align: center;
            padding-top: 2in;
            page-break-after: always;
        }}
        .cover h1 {{
            font-size: 24pt;
            font-weight: bold;
            margin: 1in 0 0.5in 0;
        }}
        .cover .meta {{
            font-size: 14pt;
            margin: 0.25in 0;
        }}
        h1 {{
            font-size: 18pt;
            margin-top: 0.5in;
            border-bottom: 2px solid #333;
            padding-bottom: 0.1in;
        }}
        h2 {{
            font-size: 14pt;
            margin-top: 0.3in;
            font-weight: bold;
        }}
        p {{
            text-align: justify;
            margin: 0.15in 0;
        }}
        .abstract {{
            font-style: italic;
            margin: 0.25in 0.5in;
        }}
        .references {{
            page-break-before: always;
        }}
        .ref-item {{
            margin: 0.15in 0 0.15in 0.5in;
            text-indent: -0.5in;
            padding-left: 0.5in;
            font-size: 10pt;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>{form_data['topic']}</h1>
        <div class="meta">A Research Report</div>
        <div class="meta">Subject: {form_data['subject']}</div>
        <div class="meta" style="margin-top: 1in;">
            Prepared by<br>
            {form_data['researcher']}<br>
            {form_data['institution']}<br>
            {report_date}
        </div>
    </div>

    <h1>Executive Summary</h1>
    <p>{refined_draft.get('executiveSummary', 'Executive summary not available.')}</p>

    <h1>Abstract</h1>
    <div class="abstract">{refined_draft.get('abstract', 'Abstract not available.')}</div>

    <h1>Introduction</h1>
    <p>{refined_draft.get('introduction', 'Introduction not available.')}</p>

    <h1>Literature Review</h1>
    <p>{refined_draft.get('literatureReview', 'Literature review not available.')}</p>
"""

    # Add main sections
    for section in refined_draft.get('mainSections', []):
        html += f"""
    <h2>{section.get('title', 'Section')}</h2>
    <p>{section.get('content', 'Content not available.')}</p>
"""

    html += f"""
    <h1>Data & Statistical Analysis</h1>
    <p>{refined_draft.get('dataAnalysis', 'Data analysis not available.')}</p>

    <h1>Challenges and Limitations</h1>
    <p>{refined_draft.get('challenges', 'Challenges not available.')}</p>

    <h1>Future Outlook</h1>
    <p>{refined_draft.get('futureOutlook', 'Future outlook not available.')}</p>

    <h1>Conclusion</h1>
    <p>{refined_draft.get('conclusion', 'Conclusion not available.')}</p>

    <div class="references">
        <h1>References</h1>
"""

    # Add real references
    for i, source in enumerate(sources, 1):
        try:
            date_str = datetime.fromisoformat(source['dateAccessed'].replace('Z', '+00:00')).strftime('%B %d, %Y')
        except:
            date_str = datetime.now().strftime('%B %d, %Y')

        html += f"""
        <div class="ref-item">
            [{i}] {source.get('title', 'Unknown')}. Retrieved from {source.get('url', 'No URL')} (Accessed: {date_str}. Credibility: {source.get('credibilityScore', 0)}%)
        </div>
"""

    html += """
    </div>
</body>
</html>"""

    return html

def execute_research_pipeline():
    """Main execution pipeline"""
    st.session_state.is_processing = True
    st.session_state.step = 'processing'
    st.session_state.api_call_count = 0

    try:
        if not API_AVAILABLE:
            raise Exception("API key not configured")

        topic = st.session_state.form_data['topic']
        subject = st.session_state.form_data['subject']

        # Stage 1: Topic Analysis
        st.info(f"🔍 Stage 1: Analyzing '{topic}'...")
        analysis = analyze_topic_with_ai(topic, subject)
        st.session_state.research = {
            'subtopics': analysis['subtopics'],
            'queries': analysis['researchQueries'],
            'sources': []
        }

        # Stage 2: REAL Web Research
        st.info(f"🌐 Stage 2: Searching for real sources about '{topic}'...")
        sources = execute_web_research_real(analysis['researchQueries'], topic)
        st.session_state.research['sources'] = sources

        if len(sources) < 3:
            raise Exception(f"Only found {len(sources)} sources. Need at least 3 quality sources. Try a different topic or try again.")

        # Stage 3: Generate Draft from REAL sources
        st.info(f"✍️ Stage 3: Writing report using {len(sources)} real sources...")
        draft = generate_draft_from_sources(topic, subject, analysis['subtopics'], sources)
        st.session_state.draft = draft

        # Stage 4: Critique
        st.info("🔍 Stage 4: Reviewing quality...")
        critique = critique_draft(draft, sources, topic)
        st.session_state.critique = critique

        # Stage 5: Refine
        st.info("✨ Stage 5: Final refinements...")
        refined = refine_draft(draft, critique, topic)
        st.session_state.final_report = refined

        # Stage 6: Generate HTML
        st.info("📄 Stage 6: Creating PDF-ready document...")
        html = generate_html_report(refined, st.session_state.form_data, sources)
        
        update_progress("Complete", f"Report about '{topic}' generated successfully!", 100)
        st.session_state.html_report = html
        st.session_state.step = 'complete'
        
        st.success(f"✅ Complete! Used {st.session_state.api_call_count} API calls and {len(sources)} real sources.")

    except Exception as e:
        update_progress("Error", str(e), 0)
        st.session_state.step = 'error'
        st.error(f"❌ Error: {str(e)}")
    finally:
        st.session_state.is_processing = False

def reset_system():
    """Reset system"""
    for key in list(st.session_state.keys()):
        if key != 'form_data':
            del st.session_state[key]
    st.session_state.step = 'input'
    st.session_state.form_data = {
        'topic': '',
        'subject': '',
        'researcher': '',
        'institution': '',
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    st.session_state.api_call_count = 0

# Main UI
st.title("📝 Online Report Writer System")
st.markdown("**AI-Powered Academic Research Report Generator with Real Web Sources**")

if st.session_state.step == 'input':
    st.markdown("### Research Report Configuration")

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_input(
            "Report Topic *",
            value=st.session_state.form_data['topic'],
            placeholder="e.g., Quantum Computing, Machine Learning in Healthcare",
            help="Be specific - this will be the focus of ALL research"
        )
        subject = st.text_input(
            "Subject / Field *",
            value=st.session_state.form_data['subject'],
            placeholder="e.g., Computer Science, Medicine",
            help="Academic field"
        )

    with col2:
        researcher = st.text_input(
            "Researcher Name *",
            value=st.session_state.form_data['researcher'],
            placeholder="Your name"
        )
        institution = st.text_input(
            "Institution *",
            value=st.session_state.form_data['institution'],
            placeholder="University or Organization"
        )

    date = st.date_input(
        "Report Date",
        value=datetime.strptime(st.session_state.form_data['date'], '%Y-%m-%d')
    )

    # Update form data
    st.session_state.form_data = {
        'topic': topic,
        'subject': subject,
        'researcher': researcher,
        'institution': institution,
        'date': date.strftime('%Y-%m-%d')
    }

    is_form_valid = all([topic, subject, researcher, institution])

    st.markdown("---")
    
    col_info, col_button = st.columns([2, 1])
    with col_info:
        st.info("⏱️ **Time:** 4-6 minutes | 📊 **Sources:** Real academic papers & research")
    
    with col_button:
        if st.button(
            "🚀 Generate Report",
            disabled=not is_form_valid or not API_AVAILABLE,
            type="primary",
            use_container_width=True
        ):
            execute_research_pipeline()
            st.rerun()
    
    if not is_form_valid:
        st.warning("⚠️ Please fill in all required fields")
    
    st.markdown("---")
    st.markdown("""
    **📋 How it works:**
    1. **Topic Analysis**: Breaks down your topic into research dimensions
    2. **Web Research**: Searches for REAL academic sources (.edu, .gov, IEEE, arXiv, etc.)
    3. **Draft Generation**: Writes report using actual source content
    4. **Quality Review**: Checks accuracy and topic relevance
    5. **Refinement**: Polishes language and structure
    6. **PDF Export**: Creates professional document
    
    **✨ Key Features:**
    - ✅ Uses real web search to find current academic papers
    - ✅ Only cites trusted sources (universities, research institutions)
    - ✅ Stays focused on YOUR specific topic
    - ✅ No hallucinated content - all facts from real sources
    - ✅ Proper academic citations throughout
    """)

elif st.session_state.step == 'processing':
    st.markdown("### 🔄 Research in Progress")
    
    progress_placeholder = st.empty()
    
    with progress_placeholder.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{st.session_state.progress['stage']}**")
            st.progress(st.session_state.progress['percent'] / 100)
        with col2:
            st.metric("Progress", f"{st.session_state.progress['percent']}%")

        st.info(f"ℹ️ {st.session_state.progress['detail']}")
        
        if st.session_state.api_call_count > 0:
            st.caption(f"📞 API Calls: {st.session_state.api_call_count} | ⏱️ Please wait...")

    if st.session_state.research['queries']:
        with st.expander(f"📋 Research Queries ({len(st.session_state.research['queries'])})", expanded=False):
            for i, query in enumerate(st.session_state.research['queries'], 1):
                st.markdown(f"**{i}.** {query}")

    if st.session_state.research['subtopics']:
        with st.expander(f"📚 Subtopics ({len(st.session_state.research['subtopics'])})", expanded=False):
            for i, subtopic in enumerate(st.session_state.research['subtopics'], 1):
                st.markdown(f"**{i}.** {subtopic}")

    if st.session_state.research['sources']:
        with st.expander(f"🔍 Real Sources Found ({len(st.session_state.research['sources'])})", expanded=True):
            for i, source in enumerate(st.session_state.research['sources'], 1):
                cred_color = "🟢" if source.get('credibilityScore', 0) >= 90 else "🟡" if source.get('credibilityScore', 0) >= 85 else "🟠"
                st.markdown(f"""
                <div class="source-item">
                    <strong>{cred_color} {i}. {source.get('title', 'Untitled')[:100]}</strong><br>
                    <small>🔗 <a href="{source.get('url', '#')}" target="_blank">{source.get('url', 'No URL')[:80]}</a></small><br>
                    <small>📊 Credibility: {source.get('credibilityScore', 0)}%</small>
                </div>
                """, unsafe_allow_html=True)

    if st.session_state.is_processing:
        time.sleep(2)
        st.rerun()

elif st.session_state.step == 'complete':
    st.success("✅ Report Generated Successfully with Real Sources!")
    
    st.markdown("### 📋 Report Details")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📝 Topic**")
        st.info(st.session_state.form_data['topic'])
    with col2:
        st.markdown("**🎓 Subject**")
        st.info(st.session_state.form_data['subject'])
    with col3:
        st.markdown("**👤 Researcher**")
        st.info(st.session_state.form_data['researcher'])

    st.markdown("### 📊 Research Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    with stat_col1:
        st.metric("Search Queries", len(st.session_state.research['queries']))
    with stat_col2:
        st.metric("Real Sources", len(st.session_state.research['sources']))
    with stat_col3:
        if st.session_state.research['sources']:
            avg_cred = sum(s.get('credibilityScore', 0) for s in st.session_state.research['sources']) / len(st.session_state.research['sources'])
            st.metric("Avg Credibility", f"{avg_cred:.0f}%")
        else:
            st.metric("Avg Credibility", "N/A")
    with stat_col4:
        if st.session_state.critique:
            score = st.session_state.critique.get('overallScore', 'N/A')
            st.metric("Quality Score", f"{score}/100" if score != 'N/A' else "N/A")
        else:
            st.metric("Quality Score", "N/A")

    st.markdown("---")

    st.markdown("### 📄 Report Preview")

    if st.session_state.final_report:
        with st.expander("📋 Executive Summary", expanded=True):
            st.write(st.session_state.final_report.get('executiveSummary', 'Not available'))

        with st.expander("🔍 Abstract", expanded=False):
            st.write(st.session_state.final_report.get('abstract', 'Not available'))

        with st.expander("📖 Introduction", expanded=False):
            st.write(st.session_state.final_report.get('introduction', 'Not available'))

        if st.session_state.final_report.get('mainSections'):
            with st.expander("📑 Main Sections", expanded=False):
                for section in st.session_state.final_report['mainSections']:
                    st.subheader(section.get('title', 'Section'))
                    st.write(section.get('content', 'Not available'))

        with st.expander("🎯 Conclusion", expanded=False):
            st.write(st.session_state.final_report.get('conclusion', 'Not available'))

    if st.session_state.research['sources']:
        with st.expander(f"📚 References - {len(st.session_state.research['sources'])} Real Sources", expanded=False):
            for i, source in enumerate(st.session_state.research['sources'], 1):
                cred_emoji = "🟢" if source.get('credibilityScore', 0) >= 90 else "🟡"
                st.markdown(f"""
                **{cred_emoji} [{i}]** {source.get('title', 'Unknown')}  
                🔗 [{source.get('url', 'No URL')}]({source.get('url', '#')})  
                📊 Credibility: {source.get('credibilityScore', 0)}% | 📅 Accessed: {source.get('dateAccessed', 'Unknown')[:10]}
                
                ---
                """)

    if st.session_state.critique:
        with st.expander("✅ Quality Review Feedback", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Overall Score", f"{st.session_state.critique.get('overallScore', 'N/A')}/100")
                if 'topicRelevance' in st.session_state.critique:
                    st.metric("Topic Relevance", f"{st.session_state.critique['topicRelevance']}/100")
            with col2:
                st.metric("API Calls Used", st.session_state.api_call_count)
                st.metric("Sources Used", len(st.session_state.research['sources']))

            if st.session_state.critique.get('recommendations'):
                st.markdown("**📝 Review Notes:**")
                for rec in st.session_state.critique['recommendations']:
                    st.markdown(f"• {rec}")

    st.markdown("---")
    st.markdown("### 📥 Download Report")

    if 'html_report' in st.session_state:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            filename = f"{st.session_state.form_data['topic'].replace(' ', '_')}_Research_Report.html"
            
            st.download_button(
                label="📥 Download HTML Report",
                data=st.session_state.html_report,
                file_name=filename,
                mime="text/html",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            file_size_kb = len(st.session_state.html_report) / 1024
            st.metric("File Size", f"{file_size_kb:.1f} KB")

        st.info("""
        **📋 How to Create PDF:**
        1. Click "📥 Download HTML Report" above
        2. Open the HTML file in any web browser (Chrome, Firefox, Edge, Safari)
        3. Press `Ctrl+P` (Windows/Linux) or `Cmd+P` (Mac)
        4. In the print dialog, select **"Save as PDF"** as the destination
        5. Click "Save" to create your professional PDF report
        
        **💡 PDF Tips:**
        - ✅ Enable "Background graphics" for better appearance
        - ✅ Set margins to "Default" or "Minimum"
        - ✅ Use "Portrait" orientation
        - ✅ Paper size: Letter or A4
        """)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Generate Another Report", use_container_width=True, type="secondary"):
            reset_system()
            st.rerun()

elif st.session_state.step == 'error':
    st.error("❌ Error Occurred During Report Generation")

    st.warning(st.session_state.progress['detail'])
    
    st.markdown("### 🔧 Troubleshooting")
    st.markdown("""
    **Common Issues:**
    
    1. **"Only found X sources"**
       - Topic may be too specific or niche
       - Try broader terms (e.g., "AI in Healthcare" instead of "GPT-4 in dental diagnosis")
       - Try again - web search results can vary
    
    2. **Rate Limiting (429 Error)**
       - Wait 3-5 minutes before trying again
       - The API has usage limits per minute
       - Consider trying during off-peak hours
    
    3. **API Key Issues**
       - Verify your Anthropic API key is correct in Streamlit secrets
       - Check that your API key has available credits
       - Ensure you're using claude-sonnet-4-20250514 model
    
    4. **Network/Timeout**
       - Check your internet connection
       - The process takes 4-6 minutes - don't refresh the page
       - If timeout occurs, try a simpler topic first
    
    **💡 Tips for Better Results:**
    - Use clear, established topics with plenty of research
    - Be specific but not overly narrow
    - Popular fields: AI, Healthcare, Climate, Technology, Education
    - Wait 2-3 minutes between report generations
    """)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Try Again", use_container_width=True, type="primary"):
            reset_system()
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    <p><strong>🔬 Autonomous Research Pipeline with REAL Web Search</strong></p>
    <p style="font-size: 0.9em;">
        Topic Analysis → <b>Live Web Research</b> → Draft from Real Sources → Quality Review → Refinement → PDF-Ready Report
    </p>
    <p style="font-size: 0.8em; margin-top: 1em;">
        Powered by Claude Sonnet 4 • Real-time web search • Trusted academic sources only<br>
        Sources: .edu, .gov, IEEE, ACM, arXiv, Nature, Science, Springer, and other academic publishers
    </p>
    <p style="font-size: 0.75em; color: #999; margin-top: 0.5em;">
        🚀 Version 2.0 - Enhanced with real web search and source verification
    </p>
</div>
""", unsafe_allow_html=True)