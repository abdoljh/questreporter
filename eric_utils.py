# eric_utils.py
import requests
import csv
import re
import time
from datetime import datetime

def format_eric_authors(author_list):
    """
    Converts ERIC author list into IEEE 'I. Surname'.
    ERIC typically returns authors as a list of strings: ['Surname, First Name', ...].
    """
    if not author_list:
        return "Unknown Author", "Unknown"

    # Handle both list and string inputs
    if isinstance(author_list, str):
        authors = [a.strip() for a in re.split(r'[;]', author_list) if a.strip()]
    else:
        authors = author_list

    formatted = []
    full_names = []
    for auth in authors:
        # ERIC format is typically "Surname, First Name"
        parts = auth.split(',')
        if len(parts) > 1:
            surname = parts[0].strip()
            first_name = parts[1].strip()
            initial = first_name[0] if first_name else ""
            formatted.append(f"{initial}. {surname}")
            full_names.append(f"{surname}, {first_name}")
        else:
            formatted.append(auth)
            full_names.append(auth)

    # Get sort key (first author's full name for sorting)
    sort_key = full_names[0] if full_names else "Unknown"
    
    if len(formatted) >= 3:
        return f"{formatted[0]} et al.", sort_key
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}", sort_key
    return formatted[0] if formatted else "Unknown Author", sort_key

def fetch_and_process_eric(query, max_limit=20, save_csv=True):
    """
    Searches the ERIC database via the IES ERIC API.
    API Documentation: https://eric.ed.gov/?api
    """
    # The official ERIC API endpoint
    base_url = "https://api.ies.ed.gov/eric/"

    # Parameters for the search
    # Note: ERIC API uses 'search' for the query and 'rows' for count
    params = {
        "search": f"title:\"{query}\"", # Removed 'abstract:' as it's not a recognized field for direct search in ERIC API
        "format": "json",       # Request JSON response
        "rows": max_limit,      # Number of results (max 2000)
    }

    try:
        response = requests.get(base_url, params=params, timeout=20)
        if response.status_code != 200:
            print(f"[Error] ERIC API returned status: {response.status_code}")
            return []

        data = response.json()
        # ERIC returns a dictionary where 'docs' contains the list of records, nested under 'response'
        entries = data.get('response', {}).get('docs', [])
        processed_data = []
        seen_ids = set()

        for entry in entries:
            # Deduplication by ERIC ID
            eric_id = entry.get('id', '')
            if eric_id and eric_id in seen_ids:
                continue
            if eric_id:
                seen_ids.add(eric_id)

            # ERIC field for year is 'publicationdateyear'
            year = entry.get('publicationdateyear', 'n.d.')
            
            # Construct the URL using the ERIC Accession Number (id field)
            eric_url = f"https://eric.ed.gov/?id={eric_id}" if eric_id else ''

            # Format authors and get sort key
            ieee_authors, sort_key = format_eric_authors(entry.get('author'))

            processed_data.append({
                'sort_name': sort_key,
                'ieee_authors': ieee_authors,
                'title': entry.get('title'),
                'venue': entry.get('source', 'ERIC Indexed Source'),
                'year': year,
                # ERIC API does not natively provide citation counts in search results
                'citations': 0,
                'doi': eric_id or 'N/A',
                'url': eric_url
            })

        # Sort by Author Name
        processed_data.sort(key=lambda x: x['sort_name'].lower())

        # Save to Unique CSV
        if save_csv and processed_data:
            clean_q = re.sub(r"[^\w\s-]", "", query).strip().replace(" ", "_")
            filename = f"eric_{clean_q}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['ieee_authors', 'title', 'venue', 'year', 'citations', 'doi', 'url'])
                writer.writeheader()
                for row in processed_data:
                    # Filter out the helper sort_name key
                    writer.writerow({k: v for k, v in row.items() if k != 'sort_name'})
            print(f"[System] ERIC results ({len(processed_data)} papers) saved to {filename}")

        # Strategic delay for API respect
        time.sleep(1)

        return processed_data
    except Exception as e:
        print(f"[Error] ERIC integration failure: {e}")
        return []