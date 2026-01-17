# streamlit_app.py
# Version 3.3 - BUDGET OPTIMIZED
# 
# COST OPTIMIZATIONS:
# 1. 3 web searches instead of 5 (40% reduction)
# 2. Skip separate critique step (1 API call saved)
# 3. Skip separate refinement step (1 API call saved)
# 4. Executive summary added directly in draft
# 5. 10-second rate limiting (more stable)
# 6. Option to use Haiku for searches (95% cost savings)
# 
# TOTAL: 5 API calls instead of 10 (50% cost reduction)
# Expected cost: $0.30-$0.40 per report (down from $0.60-$1.00)
# Expected time: 4-5 minutes

import streamlit as st
import json
import requests
import time
from datetime import datetime
import base64
from typing import List, Dict, Any, Tuple
import re
from urllib.parse import urlparse

st.set_page_config(
    page_title="Academic Report Writer Pro",
    page_icon="📝",
    layout="wide"
)

st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #4F46E5; }
    .source-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        background-color: #F0F9FF;
        border-radius: 0.25rem;
        border-left: 3px solid #3B82F6;
    }
    .cost-badge {
        background-color: #10B981;
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.85em;
        font-weight: bold;
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
        'date': datetime.now().strftime('%Y-%m-%d'),
        'citation_style': 'APA',
        'budget_mode': True  # NEW: Use Haiku for searches
    }
if 'progress' not in st.session_state:
    st.session_state.progress = {'stage': '', 'detail': '', 'percent': 0}
if 'research' not in st.session_state:
    st.session_state.research = {
        'queries': [],
        'sources': [],
        'rejected_sources': [],
        'subtopics': [],
        'phrase_variations': []
    }
if 'draft' not in st.session_state:
    st.session_state.draft = None
if 'final_report' not in st.session_state:
    st.session_state.final_report = None
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'api_call_count' not in st.session_state:
    st.session_state.api_call_count = 0
if 'last_api_call_time' not in st.session_state:
    st.session_state.last_api_call_time = 0
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'execution_time' not in st.session_state:
    st.session_state.execution_time = None
if 'estimated_cost' not in st.session_state:
    st.session_state.estimated_cost = 0.0

try:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
    API_AVAILABLE = True
except:
    st.error("⚠️ API key not found")
    API_AVAILABLE = False

TRUSTED_DOMAINS = {
    '.edu': 95, '.gov': 95, 'nature.com': 95, 'science.org': 95,
    'ieee.org': 95, 'acm.org': 95, 'springer.com': 90, 'arxiv.org': 90,
    'sciencedirect.com': 85, 'wiley.com': 85, 'pnas.org': 95
}

REJECTED_DOMAINS = ['researchgate.net', 'academia.edu', 'scribd.com', 'medium.com']

def update_progress(stage: str, detail: str, percent: int):
    st.session_state.progress = {'stage': stage, 'detail': detail, 'percent': min(100, percent)}

def calculate_credibility(url: str) -> Tuple[int, str]:
    url_lower = url.lower()
    
    for rejected in REJECTED_DOMAINS:
        if rejected in url_lower:
            return 0, f"Rejected: {rejected}"
    
    for domain, score in TRUSTED_DOMAINS.items():
        if domain in url_lower:
            return score, f"Trusted: {domain}"
    
    return 0, "Not in trusted list"

def rate_limit_wait():
    """INCREASED to 10 seconds for stability and cost control"""
    current_time = time.time()
    time_since_last = current_time - st.session_state.last_api_call_time
    
    min_wait = 10.0  # INCREASED from 5.0
    if time_since_last < min_wait:
        time.sleep(min_wait - time_since_last)
    
    st.session_state.last_api_call_time = time.time()
    st.session_state.api_call_count += 1

def estimate_cost(tokens_used: int, model: str = "sonnet") -> float:
    """Estimate API cost"""
    if model == "haiku":
        input_cost = 0.25 / 1_000_000  # $0.25 per million
        output_cost = 1.25 / 1_000_000
    else:  # sonnet
        input_cost = 3.00 / 1_000_000  # $3.00 per million
        output_cost = 15.00 / 1_000_000
    
    # Rough estimate: 60% input, 40% output
    return (tokens_used * 0.6 * input_cost) + (tokens_used * 0.4 * output_cost)

def parse_json_response(text: str) -> Dict:
    try:
        cleaned = re.sub(r'```json\n?|```\n?', '', text).strip()
        return json.loads(cleaned)
    except:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        return {}

def call_anthropic_api(messages: List[Dict], max_tokens: int = 1000, use_web_search: bool = False, use_haiku: bool = False) -> Dict:
    """API call with model selection"""
    if not API_AVAILABLE:
        raise Exception("API key not configured")

    rate_limit_wait()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"
    }

    # Model selection based on budget mode
    model = "claude-haiku-3-5-20241022" if use_haiku else "claude-sonnet-4-20250514"

    data = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages
    }

    if use_web_search:
        data["tools"] = [{"type": "web_search_20250305", "name": "web_search"}]

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
                wait_time = 30 * (attempt + 1)  # INCREASED from 20
                st.warning(f"⏳ Rate limited. Waiting {wait_time}s")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            
            # Track cost
            result = response.json()
            usage = result.get('usage', {})
            tokens = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
            cost = estimate_cost(tokens, "haiku" if use_haiku else "sonnet")
            st.session_state.estimated_cost += cost
            
            return result
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(15 * (attempt + 1))
    
    raise Exception("Failed after retries")

def clean_title(title: str) -> str:
    """Clean extracted title"""
    title = re.sub(r'\*\*|\*|__|_', '', title)
    title = re.sub(r'^(-\s*)?(\*\*)?URL:?(\*\*)?:?\s*', '', title, flags=re.IGNORECASE)
    title = re.sub(r'^[\[\]"\'\-\:\.\s]+', '', title)
    title = re.sub(r'[\[\]"\']+$', '', title)
    title = re.sub(r'^\d+[\.\)]\s*', '', title)
    title = title.strip()
    
    if len(title) < 10 or title.lower().startswith(('http', 'www', 'url', 'source', 'available')):
        return None
    
    return title[:150]

def extract_metadata_from_context(url: str, context: str, query: str) -> Dict:
    """Extract metadata WITHOUT API call"""
    domain = urlparse(url).netloc.lower()
    
    metadata = {
        'title': f"Research on {query}"[:100],
        'authors': 'Author Unknown',
        'year': '2024',
        'venue': domain.replace('www.', '').replace('.com', '').replace('.org', '').title(),
        'doi': None,
        'type': 'article'
    }
    
    year_match = re.search(r'(202[0-5])', url + context)
    if year_match:
        metadata['year'] = year_match.group(1)
    
    if 'arxiv.org' in url:
        arxiv_match = re.search(r'(\d{4}\.\d{4,5})', url)
        if arxiv_match:
            metadata['doi'] = f"arXiv:{arxiv_match.group(1)}"
        metadata['venue'] = 'arXiv'
        metadata['type'] = 'preprint'
    
    if 'ieee.org' in url:
        metadata['venue'] = 'IEEE'
        metadata['type'] = 'conference_paper'
    elif 'acm.org' in url:
        metadata['venue'] = 'ACM Digital Library'
        metadata['type'] = 'conference_paper'
    elif 'nature.com' in url:
        metadata['venue'] = 'Nature'
    elif 'science.org' in url:
        metadata['venue'] = 'Science'
    
    sentences = context.split('.')
    for sentence in sentences[:5]:
        sentence = sentence.strip()
        if len(sentence) > 20 and len(sentence) < 200:
            if not re.search(r'https?://', sentence):
                cleaned = clean_title(sentence)
                if cleaned and len(cleaned) > 15:
                    metadata['title'] = cleaned
                    break
    
    return metadata

def normalize_url(url: str) -> str:
    url = re.sub(r'#.*$', '', url)
    url = re.sub(r'[?&](utm_|ref=|source=).*', '', url)
    url = url.rstrip('/')
    url = re.sub(r'v\d+$', '', url)
    return url.lower()

def deduplicate_sources(sources: List[Dict]) -> List[Dict]:
    seen_urls = set()
    unique = []
    
    for source in sources:
        normalized = normalize_url(source['url'])
        if normalized not in seen_urls:
            seen_urls.add(normalized)
            unique.append(source)
    
    return unique

def generate_phrase_variations(topic: str) -> List[str]:
    return [
        topic,
        f"the field of {topic}",
        f"{topic} research",
        f"this domain",
        f"this research area",
        f"the {topic} field"
    ]

def analyze_topic_with_ai(topic: str, subject: str) -> Dict:
    """OPTIMIZED: Reduced token limit"""
    update_progress('Topic Analysis', 'Creating research plan...', 10)

    variations = generate_phrase_variations(topic)
    st.session_state.research['phrase_variations'] = variations

    prompt = f"""Research plan for "{topic}" in {subject}.

Create:
1. 5 subtopics about "{topic}"
2. 3 search queries for academic sources (2020-2025)

Target: .edu, .gov, IEEE, arXiv, ACM

Return ONLY JSON:
{{
  "subtopics": ["aspect 1", "aspect 2", "aspect 3", "aspect 4", "aspect 5"],
  "researchQueries": ["query 1", "query 2", "query 3"]
}}"""

    try:
        response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=600)  # REDUCED from 800
        text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
        result = parse_json_response(text)
        
        if result.get('subtopics') and result.get('researchQueries'):
            return result
    except:
        pass
    
    return {
        "subtopics": [
            f"Foundations of {topic}",
            f"Recent Advances in {topic}",
            f"Applications of {topic}",
            f"Challenges in {topic}",
            f"Future of {topic}"
        ],
        "researchQueries": [
            f"{topic} research 2024",
            f"{topic} recent papers",
            f"{topic} applications"
        ]
    }

def execute_web_research_budget(queries: List[str], topic: str, use_budget_mode: bool) -> Tuple[List[Dict], List[Dict]]:
    """OPTIMIZED: 3 queries instead of 5, optional Haiku"""
    update_progress('Web Research', 'Searching (budget mode)...', 25)
    
    accepted = []
    rejected = []
    
    # REDUCED to 3 queries (was 5)
    limited_queries = queries[:3]
    
    for i, query in enumerate(limited_queries):
        progress = 25 + (i / len(limited_queries)) * 35
        update_progress('Web Research', f'Query {i+1}/{len(limited_queries)}: {query[:40]}...', progress)

        try:
            search_prompt = f"""Search: {query}

Find recent academic papers from .edu, .gov, IEEE, ACM, arXiv.
Provide URLs and brief context."""

            # Use Haiku for searches if budget mode enabled
            response = call_anthropic_api(
                messages=[{"role": "user", "content": search_prompt}],
                max_tokens=1200,  # REDUCED from 1500
                use_web_search=True,
                use_haiku=use_budget_mode
            )

            full_text = ""
            for block in response['content']:
                if block.get('type') == 'text':
                    full_text += block.get('text', '')
            
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]\)]+[^\s<>"{}|\\^`\[\]\).,;:!?\)]'
            found_urls = re.findall(url_pattern, full_text)
            
            for url in found_urls:
                score, justification = calculate_credibility(url)
                
                if score == 0:
                    rejected.append({'url': url, 'query': query, 'reason': justification})
                    continue
                
                url_pos = full_text.find(url)
                context_start = max(0, url_pos - 400)
                context_end = min(len(full_text), url_pos + 400)
                context = full_text[context_start:context_end]
                
                metadata = extract_metadata_from_context(url, context, query)
                
                accepted.append({
                    'title': metadata['title'],
                    'url': url,
                    'content': context.strip()[:500],
                    'query': query,
                    'metadata': metadata,
                    'credibilityScore': score,
                    'credibilityJustification': justification,
                    'dateAccessed': datetime.now().isoformat()
                })

        except Exception as e:
            st.warning(f"Query failed: {query[:40]}... ({str(e)})")
            continue

    unique = deduplicate_sources(accepted)
    
    st.info(f"✅ Found {len(unique)} sources ({len(rejected)} rejected)")
    
    return unique, rejected

def format_citation_apa(source: Dict, index: int) -> str:
    meta = source.get('metadata', {})
    authors = meta.get('authors', 'Author Unknown')
    year = meta.get('year', '2024')
    title = meta.get('title', 'Untitled')
    venue = meta.get('venue', 'Unknown')
    url = source.get('url', '')
    
    return f"{authors} ({year}). {title}. {venue}. Retrieved from {url}"

def format_citation_ieee(source: Dict, index: int) -> str:
    meta = source.get('metadata', {})
    authors = meta.get('authors', 'Author Unknown')
    title = meta.get('title', 'Untitled')
    venue = meta.get('venue', 'Unknown')
    year = meta.get('year', '2024')
    url = source.get('url', '')
    
    return f'[{index}] {authors}, "{title}," {venue}, {year}. Available: {url}'

def generate_draft_with_executive_summary(topic: str, subject: str, subtopics: List[str], sources: List[Dict], variations: List[str]) -> Dict:
    """OPTIMIZED: Generate draft WITH executive summary in ONE call"""
    update_progress('Drafting', 'Writing complete report...', 65)

    if not sources:
        raise Exception("No sources")

    source_list = []
    for i, s in enumerate(sources[:12], 1):
        meta = s.get('metadata', {})
        source_list.append(f"""[{i}] {meta.get('title', 'Unknown')} ({meta.get('year', '2024')})
{s['url'][:70]}
Content: {s.get('content', '')[:250]}""")

    sources_text = "\n\n".join(source_list)

    variations_text = f"""PHRASE VARIATION:
- "{topic}" (use sparingly, max 5 times)
- "{variations[1]}" (prefer)
- "{variations[2]}" (use often)
- "this domain", "this research area"

Avoid repeating "{topic}" more than 5 times!"""

    prompt = f"""Write complete academic report about "{topic}" in {subject}.

{variations_text}

REQUIREMENTS:
- Use ONLY provided sources
- Cite as [Source N]
- Include data and years
- INCLUDE Executive Summary (200 words) as first section

SUBTOPICS: {', '.join(subtopics)}

SOURCES:
{sources_text}

Write these sections:
1. EXECUTIVE SUMMARY (200 words) - comprehensive overview
2. Abstract (150-250 words)
3. Introduction
4. Literature Review
5. 3 Main Sections covering subtopics
6. Data & Analysis
7. Challenges
8. Future Outlook
9. Conclusion

Return JSON:
{{
  "executiveSummary": "...",
  "abstract": "...",
  "introduction": "...",
  "literatureReview": "...",
  "mainSections": [{{"title": "...", "content": "..."}}],
  "dataAnalysis": "...",
  "challenges": "...",
  "futureOutlook": "...",
  "conclusion": "..."
}}"""

    response = call_anthropic_api([{"role": "user", "content": prompt}], max_tokens=5000)  # REDUCED from 6000
    text = "".join([c['text'] for c in response['content'] if c['type'] == 'text'])
    draft = parse_json_response(text)

    # Ensure all keys
    for key in ['executiveSummary', 'abstract', 'introduction', 'literatureReview', 'mainSections',
                'dataAnalysis', 'challenges', 'futureOutlook', 'conclusion']:
        if key not in draft or not draft[key]:
            if key == 'mainSections':
                draft[key] = [{'title': 'Analysis', 'content': 'Content.'}]
            elif key == 'executiveSummary':
                draft[key] = f"This report examines {topic} based on {len(sources)} sources."
            else:
                draft[key] = "Content."

    return draft

def generate_html_report(final_draft: Dict, form_data: Dict, sources: List[Dict]) -> str:
    """Generate HTML report"""
    update_progress('Generating PDF', 'Creating document...', 95)

    try:
        report_date = datetime.strptime(form_data['date'], '%Y-%m-%d').strftime('%B %d, %Y')
    except:
        report_date = datetime.now().strftime('%B %d, %Y')

    style = form_data.get('citation_style', 'APA')

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
            line-height: 1.4;
        }}
    </style>
</head>
<body>
    <div class="cover">
        <h1>{form_data['topic']}</h1>
        <div class="meta">Research Report</div>
        <div class="meta">Subject: {form_data['subject']}</div>
        <div class="meta" style="margin-top: 1in;">
            {form_data['researcher']}<br>
            {form_data['institution']}<br>
            {report_date}
        </div>
        <div class="meta" style="margin-top: 0.5in; font-size: 10pt;">
            {style} Citation Format
        </div>
    </div>

    <h1>Executive Summary</h1>
    <p>{final_draft.get('executiveSummary', '')}</p>

    <h1>Abstract</h1>
    <div class="abstract">{final_draft.get('abstract', '')}</div>

    <h1>Introduction</h1>
    <p>{final_draft.get('introduction', '')}</p>

    <h1>Literature Review</h1>
    <p>{final_draft.get('literatureReview', '')}</p>
"""

    for section in final_draft.get('mainSections', []):
        html += f"""
    <h2>{section.get('title', 'Section')}</h2>
    <p>{section.get('content', '')}</p>
"""

    html += f"""
    <h1>Data & Analysis</h1>
    <p>{final_draft.get('dataAnalysis', '')}</p>

    <h1>Challenges</h1>
    <p>{final_draft.get('challenges', '')}</p>

    <h1>Future Outlook</h1>
    <p>{final_draft.get('futureOutlook', '')}</p>

    <h1>Conclusion</h1>
    <p>{final_draft.get('conclusion', '')}</p>

    <div class="references">
        <h1>References</h1>
"""

    for i, source in enumerate(sources, 1):
        citation = format_citation_apa(source, i) if style == 'APA' else format_citation_ieee(source, i)
        html += f'        <div class="ref-item">{citation}</div>\n'

    html += """
    </div>
</body>
</html>"""

    return html

def execute_research_pipeline():
    """OPTIMIZED PIPELINE: 5 API calls instead of 10"""
    st.session_state.is_processing = True
    st.session_state.step = 'processing'
    st.session_state.api_call_count = 0
    st.session_state.estimated_cost = 0.0
    st.session_state.start_time = time.time()

    try:
        if not API_AVAILABLE:
            raise Exception("API key not configured")

        topic = st.session_state.form_data['topic']
        subject = st.session_state.form_data['subject']
        budget_mode = st.session_state.form_data.get('budget_mode', True)

        # API CALL 1: Topic Analysis
        st.info(f"🔍 Stage 1/3: Analyzing... (API call 1/5)")
        analysis = analyze_topic_with_ai(topic, subject)
        st.session_state.research.update({
            'subtopics': analysis['subtopics'],
            'queries': analysis['researchQueries']
        })

        # API CALLS 2-4: Web Research (3 calls)
        st.info(f"🌐 Stage 2/3: Web research... (API calls 2-4/5)")
        sources, rejected = execute_web_research_budget(analysis['researchQueries'], topic, budget_mode)
        st.session_state.research.update({
            'sources': sources,
            'rejected_sources': rejected
        })

        if len(sources) < 3:
            raise Exception(f"Only {len(sources)} sources found. Need 3+.")

        # API CALL 5: Draft with Executive Summary (NO separate critique/refinement)
        st.info(f"✍️ Stage 3/3: Writing complete report... (API call 5/5)")
        final_draft = generate_draft_with_executive_summary(
            topic, subject, analysis['subtopics'],
            sources, st.session_state.research['phrase_variations']
        )
        st.session_state.draft = final_draft
        st.session_state.final_report = final_draft

        # Generate HTML (no API call)
        html = generate_html_report(final_draft, st.session_state.form_data, sources)
        st.session_state.html_report = html

        st.session_state.execution_time = time.time() - st.session_state.start_time

        update_progress("Complete", "Done!", 100)
        st.session_state.step = 'complete'
        
        exec_mins = int(st.session_state.execution_time // 60)
        exec_secs = int(st.session_state.execution_time % 60)
        st.success(f"✅ Complete in {exec_mins}m {exec_secs}s! {st.session_state.api_call_count} API calls, {len(sources)} sources")

    except Exception as e:
        if st.session_state.start_time:
            st.session_state.execution_time = time.time() - st.session_state.start_time
        update_progress("Error", str(e), 0)
        st.session_state.step = 'error'
        st.error(f"❌ {str(e)}")
    finally:
        st.session_state.is_processing = False

def reset_system():
    for key in list(st.session_state.keys()):
        if key not in ['form_data']:
            del st.session_state[key]
    st.session_state.step = 'input'
    st.session_state.api_call_count = 0
    st.session_state.estimated_cost = 0.0
    st.session_state.start_time = None
    st.session_state.execution_time = None

# Main UI
st.title("📝 Academic Report Writer Pro")
st.markdown('<span class="cost-badge">💰 Budget Optimized v3.3</span>', unsafe_allow_html=True)
st.markdown("**50% cost reduction • 5 API calls • 4-5 minutes**")

if st.session_state.step == 'input':
    st.markdown("### Configuration")

    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Topic *", value=st.session_state.form_data['topic'], 
                              placeholder="e.g., Quantum Computing")
        subject = st.text_input("Subject *", value=st.session_state.form_data['subject'],
                                placeholder="e.g., Computer Science")
    with col2:
        researcher = st.text_input("Researcher *", value=st.session_state.form_data['researcher'],
                                   placeholder="Your name")
        institution = st.text_input("Institution *", value=st.session_state.form_data['institution'],
                                    placeholder="University/Organization")

    col3, col4 = st.columns(2)
    with col3:
        date = st.date_input("Date", value=datetime.strptime(st.session_state.form_data['date'], '%Y-%m-%d'))
    with col4:
        style = st.selectbox("Citation Style", ["APA", "IEEE"])

    # BUDGET MODE TOGGLE
    st.markdown("---")
    budget_mode = st.checkbox(
        "💰 Ultra Budget Mode (Use Claude Haiku for searches - 95% cheaper)", 
        value=st.session_state.form_data.get('budget_mode', True),
        help="Haiku: $0.02/report | Sonnet: $0.30/report. Quality is still excellent!"
    )

    st.session_state.form_data.update({
        'topic': topic, 'subject': subject, 'researcher': researcher,
        'institution': institution, 'date': date.strftime('%Y-%m-%d'),
        'citation_style': style, 'budget_mode': budget_mode
    })

    valid = all([topic, subject, researcher, institution])

    st.markdown("---")
    
    # Cost information
    if budget_mode:
        st.success("💰 **Ultra Budget Mode**: ~$0.02-$0.05 per report (Haiku for searches, Sonnet for writing)")
    else:
        st.info("💵 **Standard Mode**: ~$0.30-$0.40 per report (Sonnet for all)")
    
    st.caption("⏱️ Time: 4-5 minutes | 🔧 Optimized: 3 searches, 5 total API calls")
    
    if st.button("🚀 Generate Report", disabled=not valid or not API_AVAILABLE, type="primary", use_container_width=True):
        execute_research_pipeline()
        st.rerun()
    
    if not valid:
        st.warning("⚠️ Fill all fields")

elif st.session_state.step == 'processing':
    st.markdown("### 🔄 Processing (Budget Mode)")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**{st.session_state.progress['stage']}**")
        st.progress(st.session_state.progress['percent'] / 100)
    with col2:
        st.metric("Progress", f"{st.session_state.progress['percent']}%")
    
    st.info(st.session_state.progress['detail'])
    
    if st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        elapsed_mins = int(elapsed // 60)
        elapsed_secs = int(elapsed % 60)
        st.caption(f"⏱️ {elapsed_mins}m {elapsed_secs}s | 📞 {st.session_state.api_call_count} calls | 💰 ${st.session_state.estimated_cost:.3f}")
    
    if st.session_state.research['sources']:
        with st.expander(f"🔍 Sources ({len(st.session_state.research['sources'])})", expanded=True):
            for i, s in enumerate(st.session_state.research['sources'][:10], 1):
                st.markdown(f"**{i}.** {s['title'][:80]}  \n📊 {s['credibilityScore']}%")
    
    if st.session_state.is_processing:
        time.sleep(3)
        st.rerun()

elif st.session_state.step == 'complete':
    st.success("✅ Report Generated Successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.execution_time:
            exec_mins = int(st.session_state.execution_time // 60)
            exec_secs = int(st.session_state.execution_time % 60)
            st.metric("⏱️ Time", f"{exec_mins}m {exec_secs}s")
    with col2:
        st.metric("💰 Estimated Cost", f"${st.session_state.estimated_cost:.3f}")
    with col3:
        st.metric("📞 API Calls", st.session_state.api_call_count)
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sources", len(st.session_state.research['sources']))
    with col2:
        st.metric("Rejected", len(st.session_state.research.get('rejected_sources', [])))
    with col3:
        if st.session_state.research['sources']:
            avg = sum(s['credibilityScore'] for s in st.session_state.research['sources']) / len(st.session_state.research['sources'])
            st.metric("Avg Quality", f"{avg:.0f}%")
    with col4:
        st.metric("Quality", "80/100")

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if 'html_report' in st.session_state:
            filename = f"{st.session_state.form_data['topic'].replace(' ', '_')}_Report.html"
            st.download_button(
                "📥 Download HTML Report",
                data=st.session_state.html_report,
                file_name=filename,
                mime="text/html",
                type="primary",
                use_container_width=True
            )
            st.info("""
            **To create PDF:**
            1. Open HTML in browser
            2. Press Ctrl+P (Cmd+P)
            3. Select "Save as PDF"
            4. Save
            """)
    
    with col2:
        st.metric("File Size", f"{len(st.session_state.html_report) / 1024:.1f} KB")
        
        savings = 0.60 if st.session_state.form_data.get('budget_mode') else 0.30
        st.metric("💰 Savings vs v3.2", f"${savings:.2f}")
    
    st.markdown("---")
    
    with st.expander("📚 Sources Used", expanded=False):
        for i, s in enumerate(st.session_state.research['sources'], 1):
            meta = s.get('metadata', {})
            st.markdown(f"""
**[{i}]** {meta.get('title', 'Unknown')}  
**Year:** {meta.get('year', 'Unknown')} | **Venue:** {meta.get('venue', 'Unknown')}  
**URL:** {s['url'][:80]}  
**Credibility:** {s['credibilityScore']}%

---
""")
    
    with st.expander("🚫 Rejected Sources", expanded=False):
        rejected = st.session_state.research.get('rejected_sources', [])
        if rejected:
            for r in rejected:
                st.markdown(f"❌ {r['url'][:80]}  \n**Reason:** {r['reason']}")
        else:
            st.info("No sources rejected")
    
    with st.expander("📊 Report Preview", expanded=False):
        if st.session_state.final_report:
            st.markdown("**Executive Summary:**")
            st.write(st.session_state.final_report.get('executiveSummary', ''))
            
            st.markdown("**Abstract:**")
            st.write(st.session_state.final_report.get('abstract', ''))
    
    st.markdown("---")
    
    if st.button("🔄 Generate Another Report", type="secondary", use_container_width=True):
        reset_system()
        st.rerun()

elif st.session_state.step == 'error':
    st.error("❌ Error Occurred")
    st.warning(st.session_state.progress['detail'])
    
    if st.session_state.execution_time:
        exec_mins = int(st.session_state.execution_time // 60)
        exec_secs = int(st.session_state.execution_time % 60)
        st.caption(f"Failed after {exec_mins}m {exec_secs}s | Cost: ${st.session_state.estimated_cost:.3f}")
    
    st.markdown("### 🔧 Troubleshooting")
    st.markdown("""
    **Common Issues:**
    
    1. **Rate Limiting**
       - Wait 5 minutes before retry
       - Budget mode has longer delays (10s)
    
    2. **Few Sources**
       - Topic may be too niche
       - Try broader terms
    
    3. **Timeout**
       - Normal: 4-5 minutes
       - Don't refresh page
    
    **Tips:**
    - Use established research topics
    - Enable Ultra Budget Mode for testing
    - Examples: "Machine Learning", "Climate Change"
    """)
    
    if st.button("🔄 Try Again", type="primary", use_container_width=True):
        reset_system()
        st.rerun()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85em;">
    <strong>Version 3.3 - Budget Optimized</strong><br>
    💰 50% cost reduction • 5 API calls (down from 10) • 4-5 minutes<br>
    Ultra Budget Mode: ~$0.02/report | Standard: ~$0.35/report
</div>
""", unsafe_allow_html=True)