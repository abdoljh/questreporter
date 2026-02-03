"""
Unit Tests for Citation Formatting - ZERO API COST

Run with: python test_citations.py
Or with pytest: pytest test_citations.py -v

These tests validate IEEE/APA citation formatting without making any API calls.
"""

import unittest
import re
from typing import Dict


# ================================================================================
# COPY OF ORIGINAL FORMATTING FUNCTION (for comparison)
# ================================================================================

def format_citation_ieee_original(source: Dict, index: int) -> str:
    """Original IEEE formatting function - for comparison"""
    meta = source.get('metadata', {})
    authors = meta.get('authors', 'Research Team')
    title = meta.get('title', 'Research Article')
    venue = meta.get('venue', 'Academic Publication')
    year = meta.get('year', '2024')
    url = source.get('url', '')

    if not authors or authors.lower() in ['unknown', 'author unknown']:
        authors = venue + ' Authors'

    if not title or title.lower() == 'unknown':
        title = 'Research Article'

    citation = f'[{index}] {authors}, "{title}," <i>{venue}</i>, {year}. [Online]. Available: <a href="{url}" target="_blank">{url}</a>'

    return citation


# ================================================================================
# FIXED IEEE FORMATTING FUNCTIONS (User's Custom Style)
# ================================================================================

# Institutional/organizational names that should NOT be modified
INSTITUTIONAL_NAMES = {
    'research team', 'authors', 'contributors', 'editors', 'staff',
    'ieee authors', 'acm authors', 'arxiv contributors', 'nature authors',
    'academic publication authors', 'university', 'institute', 'laboratory',
    'organization', 'consortium', 'group', 'committee', 'department'
}


def is_institutional_name(name: str) -> bool:
    """Check if name is an institutional/organizational name"""
    name_lower = name.lower().strip()
    if name_lower in INSTITUTIONAL_NAMES:
        return True
    for suffix in ['authors', 'contributors', 'team', 'staff', 'editors', 'group']:
        if name_lower.endswith(suffix):
            return True
    return False


def format_authors_ieee(authors_str: str) -> str:
    """
    Format multiple authors for IEEE style (full names preserved).

    Format:
    - Two authors: "Author One and Author Two"
    - Three+ authors: "Author One, Author Two, and Author Three"
    - Institutional names preserved as-is
    - "et al." preserved
    """
    if not authors_str:
        return "Research Team"

    if is_institutional_name(authors_str):
        return authors_str

    # Handle "et al." cases
    if 'et al' in authors_str.lower():
        match = re.match(r'^([^,]+?)(?:\s+et\s+al\.?)$', authors_str, re.IGNORECASE)
        if match:
            first_author = match.group(1).strip()
            return f"{first_author} et al."
        return authors_str

    # Split by comma or "and"
    authors = re.split(r',\s*|\s+and\s+', authors_str)
    authors = [a.strip() for a in authors if a.strip()]

    if not authors:
        return "Research Team"

    if len(authors) == 1:
        return authors[0]
    elif len(authors) == 2:
        return f"{authors[0]} and {authors[1]}"
    else:
        return ', '.join(authors[:-1]) + ', and ' + authors[-1]


def format_citation_ieee_fixed(source: Dict, index: int) -> str:
    """
    Format citation in IEEE style (User's Custom Format).

    Format: [N] Authors, "Title," Venue, Year.
            Link: URL

    Rules:
    1. Full author names (not initials)
    2. Institutional names preserved as-is
    3. Comma INSIDE closing quotation mark for title
    4. Venue without italics
    5. Link on separate line
    """
    meta = source.get('metadata', {})
    authors = meta.get('authors', 'Research Team')
    title = meta.get('title', 'Research Article')
    venue = meta.get('venue', 'Academic Publication')
    year = meta.get('year', '2024')
    url = source.get('url', '')

    # Ensure no 'unknown' values
    if not authors or authors.lower() in ['unknown', 'author unknown']:
        authors = venue + ' Authors'

    if not title or title.lower() == 'unknown':
        title = 'Research Article'

    # Format authors (preserves full names and institutional names)
    formatted_authors = format_authors_ieee(authors)

    # Format: [N] Authors, "Title," Venue, Year.
    # Link: URL
    citation = f'[{index}] {formatted_authors}, "{title}," {venue}, {year}. \nLink: {url}'

    return citation


# ================================================================================
# TEST CASES
# ================================================================================

class TestAuthorFormatting(unittest.TestCase):
    """Test author name formatting (full names preserved)"""

    def test_single_name(self):
        """Single word names should pass through unchanged"""
        self.assertEqual(format_authors_ieee("Einstein"), "Einstein")

    def test_two_part_name(self):
        """First Last -> First Last (full name preserved)"""
        self.assertEqual(format_authors_ieee("John Smith"), "John Smith")

    def test_three_part_name(self):
        """First Middle Last -> First Middle Last (full name preserved)"""
        self.assertEqual(format_authors_ieee("John David Smith"), "John David Smith")

    def test_empty_name(self):
        """Empty string should return default"""
        self.assertEqual(format_authors_ieee(""), "Research Team")


class TestMultipleAuthors(unittest.TestCase):
    """Test multiple author formatting (full names)"""

    def test_single_author(self):
        """Single author formatting (full name)"""
        self.assertEqual(format_authors_ieee("John Smith"), "John Smith")

    def test_two_authors(self):
        """Two authors: 'A and B' format (full names)"""
        result = format_authors_ieee("John Smith, Jane Doe")
        self.assertEqual(result, "John Smith and Jane Doe")

    def test_three_authors(self):
        """Three authors: 'A, B, and C' format (full names)"""
        result = format_authors_ieee("John Smith, Jane Doe, Bob Wilson")
        self.assertEqual(result, "John Smith, Jane Doe, and Bob Wilson")

    def test_et_al(self):
        """et al. should be preserved with first author as full name"""
        result = format_authors_ieee("John Smith et al.")
        self.assertEqual(result, "John Smith et al.")

    def test_empty_authors(self):
        """Empty authors should return default"""
        self.assertEqual(format_authors_ieee(""), "Research Team")

    def test_institutional_authors(self):
        """Institutional names should NOT be modified"""
        self.assertEqual(format_authors_ieee("Research Team"), "Research Team")
        self.assertEqual(format_authors_ieee("IEEE Authors"), "IEEE Authors")
        self.assertEqual(format_authors_ieee("ArXiv Contributors"), "ArXiv Contributors")


class TestIEEECitation(unittest.TestCase):
    """Test full IEEE citation formatting (User's Custom Style)"""

    def setUp(self):
        """Sample source data for tests"""
        self.sample_source = {
            'url': 'https://example.com/paper',
            'metadata': {
                'authors': 'John Smith, Jane Doe',
                'title': 'A Study on Testing',
                'venue': 'IEEE Transactions on Testing',
                'year': '2024'
            }
        }

    def test_basic_formatting(self):
        """Test basic custom IEEE citation format"""
        result = format_citation_ieee_fixed(self.sample_source, 1)

        self.assertTrue(result.startswith('[1]'))
        self.assertIn('John Smith and Jane Doe', result)  # Full names
        self.assertIn('"A Study on Testing,"', result)  # Comma inside quotes
        self.assertIn('IEEE Transactions on Testing,', result)  # No italics
        self.assertNotIn('[Online]. Available:', result)  # No online link format
        self.assertIn('Link:', result)  # Simple Link format

    def test_comma_placement(self):
        """Custom IEEE requires comma INSIDE closing quotation mark for title"""
        result = format_citation_ieee_fixed(self.sample_source, 1)
        self.assertIn('Testing,"', result)  # Comma inside quote
        self.assertNotIn('Testing",', result)  # This would be wrong

    def test_no_italics(self):
        """Venue should NOT be italicized"""
        result = format_citation_ieee_fixed(self.sample_source, 1)
        self.assertNotIn('<i>', result)
        self.assertNotIn('</i>', result)

    def test_link_format(self):
        """URL should use 'Link:' format, not '[Online]. Available:'"""
        result = format_citation_ieee_fixed(self.sample_source, 1)
        self.assertIn('Link: https://example.com/paper', result)
        self.assertNotIn('[Online]. Available:', result)

    def test_unknown_author_handling(self):
        """Unknown authors should get venue-based attribution"""
        source = {
            'url': 'https://example.com',
            'metadata': {
                'authors': 'unknown',
                'title': 'Test Paper',
                'venue': 'IEEE',
                'year': '2024'
            }
        }
        result = format_citation_ieee_fixed(source, 1)
        self.assertIn('IEEE Authors', result)
        self.assertNotIn('unknown', result.lower())

    def test_missing_metadata(self):
        """Missing metadata should use defaults"""
        source = {'url': 'https://example.com', 'metadata': {}}
        result = format_citation_ieee_fixed(source, 1)

        self.assertTrue(result.startswith('[1]'))
        self.assertIn('Research Team', result)

    def test_index_numbering(self):
        """Test different index numbers"""
        for i in [1, 5, 10, 99]:
            result = format_citation_ieee_fixed(self.sample_source, i)
            self.assertTrue(result.startswith(f'[{i}]'))


class TestCompareOriginalVsFixed(unittest.TestCase):
    """Compare original vs fixed IEEE formatting"""

    def test_show_differences(self):
        """Print comparison of original vs fixed output"""
        source = {
            'url': 'https://arxiv.org/abs/2301.00001',
            'metadata': {
                'authors': 'Albert Einstein, Richard Feynman, Stephen Hawking',
                'title': 'A Grand Unified Theory of Everything',
                'venue': 'Physical Review Letters',
                'year': '2024'
            }
        }

        original = format_citation_ieee_original(source, 1)
        fixed = format_citation_ieee_fixed(source, 1)

        print("\n" + "="*80)
        print("COMPARISON: Original vs Fixed IEEE Citation")
        print("="*80)
        print(f"\nORIGINAL (Standard IEEE with italics):\n{original}")
        print(f"\nFIXED (User's Custom Style):\n{fixed}")
        print("\nKEY DIFFERENCES:")
        print("1. Full author names with 'and' before last author")
        print("2. Comma INSIDE title quotes")
        print("3. No italics for venue")
        print("4. 'Link:' format instead of '[Online]. Available:'")
        print("="*80)

        # Assertions
        self.assertIn('Albert Einstein, Richard Feynman, and Stephen Hawking', fixed)
        self.assertIn('"A Grand Unified Theory of Everything,"', fixed)
        self.assertNotIn('<i>', fixed)
        self.assertIn('Link:', fixed)


class TestRealWorldExamples(unittest.TestCase):
    """Test with realistic source data"""

    def test_arxiv_source(self):
        """Test arXiv-style source with institutional attribution"""
        source = {
            'url': 'https://arxiv.org/abs/2301.00001',
            'metadata': {
                'authors': 'ArXiv Contributors',
                'title': 'Attention Is All You Need',
                'venue': 'arXiv preprint',
                'year': '2023'
            }
        }
        result = format_citation_ieee_fixed(source, 1)
        self.assertIn('[1]', result)
        self.assertIn('ArXiv Contributors', result)
        self.assertIn('"Attention Is All You Need," arXiv preprint, 2023.', result)

    def test_ieee_source(self):
        """Test IEEE.org source (full names)"""
        source = {
            'url': 'https://ieeexplore.ieee.org/document/123456',
            'metadata': {
                'authors': 'Wei Zhang, Li Chen',
                'title': 'Deep Learning for Signal Processing',
                'venue': 'IEEE Signal Processing Magazine',
                'year': '2024'
            }
        }
        result = format_citation_ieee_fixed(source, 3)
        self.assertIn('[3]', result)
        self.assertIn('Wei Zhang and Li Chen', result)
        self.assertIn('"Deep Learning for Signal Processing," IEEE Signal Processing Magazine, 2024.', result)

    def test_plos_source(self):
        """Test PLOS ONE style source"""
        source = {
            'url': 'https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0298861',
            'metadata': {
                'authors': 'Shengnan Wu',
                'title': 'Application of multimedia technology to innovative vocational education',
                'venue': 'PLOS ONE',
                'year': '2024'
            }
        }
        result = format_citation_ieee_fixed(source, 2)
        self.assertIn('[2] Shengnan Wu, "Application of multimedia technology to innovative vocational education," PLOS ONE, 2024.', result)
        self.assertIn('Link:', result)


# ================================================================================
# MAIN RUNNER
# ================================================================================

if __name__ == '__main__':
    print("="*80)
    print("IEEE Citation Formatting Tests - ZERO API COST")
    print("="*80)
    print("\nThese tests validate citation formatting without any API calls.")
    print("Run the full pipeline only after these tests pass.\n")

    # Run tests with verbosity
    unittest.main(verbosity=2)
