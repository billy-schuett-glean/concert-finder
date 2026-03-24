import logging
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests

from config import BANDSINTOWN_APP_ID

logger = logging.getLogger(__name__)


def _format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%a, %B %d, %Y'), dt.strftime('%Y-%m-%d')
    except Exception:
        return date_str, date_str


def _event_matches_destination(event, destination):
    event_city = event.get('city', '').strip().lower()
    event_region = event.get('region', '').strip().lower()

    # Special destination matching
    if destination['name'] == 'Red Rocks / Morrison, CO':
        return event_city in ['morrison', 'denver', 'golden']
    if destination['name'] == "Thompson's Point / Portland, ME":
        return event_city == 'portland' and event_region in ['me', 'maine']
    if destination['name'] == 'Greek Theatre / Berkeley, CA':
        return event_city in ['berkeley', 'san francisco', 'oakland']
    if destination['name'] == 'Montreal, QC, Canada':
        return event_city in ['montreal', 'montréal']

    search_terms = [t.strip().lower() for t in destination.get('search_terms', [])]
    return any(term in event_city for term in search_terms)


def _make_api_request(artist_name, variation):
    """Make API request with different variations to find working approach."""
    base_url = 'https://rest.bandsintown.com/artists'
    app_id = 'ag'  # Use the app_id from the working curl example

    # Try different artist name encodings
    if variation.get('url_encode', False):
        artist_path = quote_plus(artist_name.lower())
    else:
        artist_path = artist_name.lower().replace(' ', '%20')  # Manual space encoding

    url = f'{base_url}/{artist_path}/events/?format=json&app_id={app_id}&api_version=3.0'

    headers = {}
    if variation.get('user_agent') == 'curl':
        headers['User-Agent'] = 'curl/7.64.0'
        headers['Accept'] = '*/*'
    elif variation.get('user_agent') == 'browser':
        headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    logger.info('Trying variation %s for %s: %s', variation['name'], artist_name, url)
    logger.info('Headers: %s', headers)

    try:
        response = requests.get(url, headers=headers, timeout=15)
        logger.info('Status: %d, Response length: %d', response.status_code, len(response.text))

        return {
            'variation': variation['name'],
            'status_code': response.status_code,
            'response_text': response.text[:500],  # First 500 chars
            'url': url,
            'headers': headers,
            'success': response.status_code == 200
        }
    except Exception as e:
        logger.error('Request failed for variation %s: %s', variation['name'], e)
        return {
            'variation': variation['name'],
            'status_code': None,
            'response_text': str(e),
            'url': url,
            'headers': headers,
            'success': False
        }


def _test_artist_api(artist_name):
    """Test all variations of the API request for an artist."""
    variations = [
        {'name': 'curl_headers_no_encode', 'user_agent': 'curl', 'url_encode': False},
        {'name': 'curl_headers_encoded', 'user_agent': 'curl', 'url_encode': True},
        {'name': 'browser_headers_no_encode', 'user_agent': 'browser', 'url_encode': False},
        {'name': 'browser_headers_encoded', 'user_agent': 'browser', 'url_encode': True},
        {'name': 'no_headers_no_encode', 'user_agent': None, 'url_encode': False},
        {'name': 'no_headers_encoded', 'user_agent': None, 'url_encode': True},
    ]

    results = []
    for variation in variations:
        result = _make_api_request(artist_name, variation)
        results.append(result)

        # Print results immediately
        print(f"\n=== {artist_name} - {variation['name']} ===")
        print(f"URL: {result['url']}")
        print(f"Headers: {result['headers']}")
        print(f"Status: {result['status_code']}")
        print(f"Response: {result['response_text']}")

        time.sleep(1)  # Rate limit

    return results


def search_artist_events(artist_name, start_date, end_date):
    """Search for artist events using Bandsintown API.

    NOTE: Bandsintown API is protected by Cloudflare and returns empty results
    for automated requests. This function is disabled until a reliable scraping
    solution can be implemented.
    """
    logger.info('Bandsintown API disabled due to Cloudflare protection - returning empty results')
    return []

    except Exception as e:
        logger.error('Error searching Bandsintown for %s: %s', artist_name, e)
        return []


def search_all_artists(artist_list, destinations, start_date, end_date):
    all_events = []
    for i, artist in enumerate(artist_list):
        artist_name = artist.get('artist_name', '')
        if not artist_name:
            continue
        logger.info('Searching Bandsintown for %s (%d/%d)', artist_name, i+1, len(artist_list))
        events = search_artist_events(artist_name, start_date, end_date)
        for event in events:
            if any(_event_matches_destination(event, dest) for dest in destinations):
                all_events.append(event)
        time.sleep(0.5)  # Rate limit
    return all_events