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
# COPY OF CURRENT FORMATTING FUNCTIONS (for comparison)
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
# IMPROVED IEEE FORMATTING FUNCTION
# ================================================================================

def format_author_ieee(name: str) -> str:
    """
    Convert author name to IEEE format: "A. B. Lastname"

    Examples:
        "John Smith" -> "J. Smith"
        "John David Smith" -> "J. D. Smith"
        "J. Smith" -> "J. Smith" (already formatted)
    """
    name = name.strip()
    if not name:
        return name

    # Already in initial format (e.g., "J. Smith")
    if re.match(r'^[A-Z]\.\s', name):
        return name

    parts = name.split()
    if len(parts) == 1:
        return parts[0]

    # Last part is surname, rest are given names -> convert to initials
    surname = parts[-1]
    initials = [p[0].upper() + '.' for p in parts[:-1] if p]

    return ' '.join(initials) + ' ' + surname


# Institutional/organizational names that should NOT be converted to initials
INSTITUTIONAL_NAMES = {
    'research team', 'authors', 'contributors', 'editors', 'staff',
    'ieee authors', 'acm authors', 'arxiv contributors', 'nature authors',
    'academic publication authors', 'university', 'institute', 'laboratory',
    'organization', 'consortium', 'group', 'committee', 'department'
}


def is_institutional_name(name: str) -> bool:
    """Check if name is an institutional/organizational name that shouldn't be formatted"""
    name_lower = name.lower().strip()
    # Check direct matches
    if name_lower in INSTITUTIONAL_NAMES:
        return True
    # Check if it ends with common institutional suffixes
    for suffix in ['authors', 'contributors', 'team', 'staff', 'editors', 'group']:
        if name_lower.endswith(suffix):
            return True
    return False


def format_authors_ieee(authors_str: str) -> str:
    """
    Format multiple authors for IEEE style.

    IEEE format:
    - Single author: "A. B. Lastname"
    - Two authors: "A. B. Lastname and C. D. Lastname"
    - Three+ authors: "A. B. Lastname, C. D. Lastname, and E. F. Lastname"

    Institutional names (like "IEEE Authors", "Research Team") are NOT formatted.

    Examples:
        "John Smith" -> "J. Smith"
        "John Smith, Jane Doe" -> "J. Smith and J. Doe"
        "IEEE Authors" -> "IEEE Authors" (institutional, not formatted)
    """
    if not authors_str:
        return "Research Team"

    # Check if this is an institutional name - don't format these
    if is_institutional_name(authors_str):
        return authors_str

    # Handle "et al." cases - extract first author before "et al"
    if 'et al' in authors_str.lower():
        # Match first author, stopping before "et al"
        match = re.match(r'^([^,]+?)(?:\s+et\s+al\.?)', authors_str, re.IGNORECASE)
        if match:
            first_author = match.group(1).strip()
            if not is_institutional_name(first_author):
                first_author = format_author_ieee(first_author)
            return f"{first_author} et al."
        return authors_str

    # Split by comma or "and"
    authors = re.split(r',\s*|\s+and\s+', authors_str)
    authors = [a.strip() for a in authors if a.strip()]

    if not authors:
        return "Research Team"

    # Format each author (skip institutional names)
    formatted = []
    for a in authors:
        if is_institutional_name(a):
            formatted.append(a)
        else:
            formatted.append(format_author_ieee(a))

    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    else:
        return ', '.join(formatted[:-1]) + ', and ' + formatted[-1]


def format_citation_ieee_fixed(source: Dict, index: int) -> str:
    """
    Format citation in IEEE style - CORRECTED VERSION

    IEEE Reference Format for Online Sources:
    [N] A. B. Author, "Article title," Journal Name, vol. X, no. Y, pp. ZZ-ZZ, Month Year.
        [Online]. Available: URL. [Accessed: Month Day, Year].

    Simplified for web sources:
    [N] A. B. Author, "Article title", Publication, Year. [Online]. Available: URL

    Key IEEE rules applied:
    1. Authors as initials + surname (human names only)
    2. Institutional names preserved as-is
    3. Comma OUTSIDE closing quotation mark for title
    4. Journal/venue in italics
    5. [Online]. Available: format for URLs
    """
    meta = source.get('metadata', {})
    authors = meta.get('authors', 'Research Team')
    title = meta.get('title', 'Research Article')
    venue = meta.get('venue', 'Academic Publication')
    year = meta.get('year', '2024')
    url = source.get('url', '')

    # Ensure no 'unknown' values - use venue-based institutional attribution
    if not authors or authors.lower() in ['unknown', 'author unknown']:
        authors = venue + ' Authors'

    if not title or title.lower() == 'unknown':
        title = 'Research Article'

    # Format authors to IEEE style (initials + surname)
    # Note: format_authors_ieee() automatically preserves institutional names
    formatted_authors = format_authors_ieee(authors)

    # IEEE format: [N] A. B. Author, "Title", Venue, Year. [Online]. Available: URL
    # Note: Comma goes OUTSIDE the closing quotation mark in IEEE style
    citation = f'[{index}] {formatted_authors}, "{title}", <i>{venue}</i>, {year}. [Online]. Available: <a href="{url}" target="_blank">{url}</a>'

    return citation


# ================================================================================
# TEST CASES
# ================================================================================

class TestAuthorFormatting(unittest.TestCase):
    """Test IEEE author name formatting"""

    def test_single_name(self):
        """Single word names should pass through unchanged"""
        self.assertEqual(format_author_ieee("Einstein"), "Einstein")

    def test_two_part_name(self):
        """First Last -> F. Last"""
        self.assertEqual(format_author_ieee("John Smith"), "J. Smith")

    def test_three_part_name(self):
        """First Middle Last -> F. M. Last"""
        self.assertEqual(format_author_ieee("John David Smith"), "J. D. Smith")

    def test_already_formatted(self):
        """Already IEEE format should pass through"""
        self.assertEqual(format_author_ieee("J. Smith"), "J. Smith")

    def test_empty_name(self):
        """Empty string should return empty"""
        self.assertEqual(format_author_ieee(""), "")


class TestMultipleAuthors(unittest.TestCase):
    """Test IEEE multiple author formatting"""

    def test_single_author(self):
        """Single author formatting"""
        self.assertEqual(format_authors_ieee("John Smith"), "J. Smith")

    def test_two_authors(self):
        """Two authors: 'A and B' format"""
        result = format_authors_ieee("John Smith, Jane Doe")
        self.assertEqual(result, "J. Smith and J. Doe")

    def test_three_authors(self):
        """Three authors: 'A, B, and C' format"""
        result = format_authors_ieee("John Smith, Jane Doe, Bob Wilson")
        self.assertEqual(result, "J. Smith, J. Doe, and B. Wilson")

    def test_et_al(self):
        """et al. should be preserved with first author formatted"""
        result = format_authors_ieee("John Smith et al.")
        self.assertEqual(result, "J. Smith et al.")

    def test_empty_authors(self):
        """Empty authors should return default"""
        self.assertEqual(format_authors_ieee(""), "Research Team")

    def test_institutional_authors(self):
        """Institutional names should NOT be formatted to initials"""
        # Research Team should stay as-is (institutional name)
        self.assertEqual(format_authors_ieee("Research Team"), "Research Team")
        self.assertEqual(format_authors_ieee("IEEE Authors"), "IEEE Authors")
        self.assertEqual(format_authors_ieee("ArXiv Contributors"), "ArXiv Contributors")


class TestIEEECitation(unittest.TestCase):
    """Test full IEEE citation formatting"""

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
        """Test basic IEEE citation format"""
        result = format_citation_ieee_fixed(self.sample_source, 1)

        # Should start with [1]
        self.assertTrue(result.startswith('[1]'))

        # Should have formatted authors
        self.assertIn('J. Smith and J. Doe', result)

        # Title should be in quotes with comma OUTSIDE
        self.assertIn('"A Study on Testing"', result)

        # Should have [Online]. Available:
        self.assertIn('[Online]. Available:', result)

    def test_comma_placement(self):
        """IEEE requires comma OUTSIDE closing quotation mark"""
        result = format_citation_ieee_fixed(self.sample_source, 1)

        # Correct: "Title",
        # Incorrect: "Title,"
        self.assertIn('Testing",', result)  # Comma outside quote
        self.assertNotIn('Testing,"', result)  # This would be wrong

    def test_unknown_author_handling(self):
        """Unknown authors should get venue-based attribution (not formatted)"""
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
        # IEEE Authors is institutional, should not be converted to initials
        self.assertIn('IEEE Authors', result)
        self.assertNotIn('unknown', result.lower())

    def test_missing_metadata(self):
        """Missing metadata should use defaults (institutional names preserved)"""
        source = {'url': 'https://example.com', 'metadata': {}}
        result = format_citation_ieee_fixed(source, 1)

        # Should not crash and should have defaults
        self.assertTrue(result.startswith('[1]'))
        # "Research Team" is institutional and should be preserved
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
        print(f"\nORIGINAL:\n{original}")
        print(f"\nFIXED:\n{fixed}")
        print("\nKEY DIFFERENCES:")
        print("1. Authors converted to initials (A. Einstein -> A. Einstein is same,")
        print("   but 'Albert Einstein, Richard Feynman' -> 'A. Einstein, R. Feynman, and S. Hawking')")
        print("2. Comma placement: Original has comma inside quotes, Fixed has it outside")
        print("="*80)

        # Actual assertions
        self.assertIn('A. Einstein', fixed)
        self.assertIn('R. Feynman', fixed)
        self.assertIn(', and S. Hawking', fixed)


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
        # ArXiv Contributors is institutional - should NOT be formatted to initials
        self.assertIn('ArXiv Contributors', result)

    def test_ieee_source(self):
        """Test IEEE.org source"""
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
        self.assertIn('W. Zhang and L. Chen', result)
        self.assertIn('[Online]. Available:', result)


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
