import logging
import re
import time
from datetime import datetime

import requests

from config import SEATGEEK_CLIENT_ID

logger = logging.getLogger(__name__)
BASE_URL = 'https://api.seatgeek.com/2/events'
PACKAGE_KEYWORDS = (
    'parking',
    'vip',
    'package',
    'passes',
    'pass',
    'fast lane',
    'lounge',
    'club access',
    'meet greet',
    'meet & greet',
    'meet and greet',
    'premium package',
    'hospitality',
    'upgrade',
    'shuttle',
    'hotel package',
    'travel package',
    'bundle',
    'early entry',
    'early access',
    'soundcheck',
    'platinum',
    'gold package',
    'silver package',
    'bronze package',
)

TRIBUTE_KEYWORDS = (
    'tribute',
    'cover',
    'experience',
    'celebration',
    'anniversary show',
    'a tribute to',
    'in the style of',
    'salute',
    'homage',
)


def _format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%a, %B %d, %Y'), dt.strftime('%Y-%m-%d')
    except Exception:
        return date_str, date_str


def _event_matches_destination(event, destination):
    venue = event.get('venue', {})
    event_city = venue.get('city', '').strip().lower()
    event_state = venue.get('state', '').strip().lower()

    # Special destination matching
    if destination['name'] == 'Red Rocks / Morrison, CO':
        return event_city in ['morrison', 'denver', 'golden']
    if destination['name'] == "Thompson's Point / Portland, ME":
        return event_city == 'portland' and event_state in ['me', 'maine']
    if destination['name'] == 'Greek Theatre / Berkeley, CA':
        return event_city in ['berkeley', 'san francisco', 'oakland']
    if destination['name'] == 'Montreal, QC, Canada':
        return event_city in ['montreal', 'montréal']

    search_terms = [t.strip().lower() for t in destination.get('search_terms', [])]
    return any(term in event_city for term in search_terms)


def _normalize_name(value):
    """Normalize name for strict matching - removes 'the', special chars, extra whitespace."""
    if not value or not isinstance(value, str):
        return ''
    n = value.lower().strip()
    n = re.sub(r"^the\s+", '', n)
    n = re.sub(r"[^a-z0-9&]+", ' ', n)
    n = re.sub(r"\s+", ' ', n).strip()
    return n


def _is_package_event(event):
    title = ' '.join(
        [
            event.get('title', ''),
            event.get('short_title', ''),
            event.get('name', ''),
        ]
    ).lower()
    return any(keyword in title for keyword in PACKAGE_KEYWORDS)


def _is_tribute_or_fake(event):
    """Check if event is a tribute band or fake artist event."""
    # Check title and performer names for tribute keywords
    title = ' '.join(
        [
            event.get('title', ''),
            event.get('short_title', ''),
            event.get('name', ''),
        ]
    ).lower()

    performer_names = ' '.join(_extract_performer_names(event)).lower()
    combined = f"{title} {performer_names}"

    return any(keyword in combined for keyword in TRIBUTE_KEYWORDS)


def _extract_performer_names(event):
    return [p.get('name', '').strip() for p in event.get('performers', []) if p.get('name')]


def _build_event_result(event, artist_name=None):
    performers = _extract_performer_names(event)
    if not performers:
        return None

    venue = event.get('venue', {})
    event_date_time = event.get('datetime_utc')
    event_date, event_date_raw = _format_date(event_date_time or '')

    stats = event.get('stats', {})
    lowest_price = stats.get('lowest_price')
    highest_price = stats.get('highest_price')
    price_range = ''
    if lowest_price and highest_price:
        price_range = f"${lowest_price:.0f} - ${highest_price:.0f}"

    return {
        'artist_name': artist_name or performers[0],
        'performer_names': performers,
        'event_date': event_date,
        'event_date_raw': event_date_raw,
        'venue_name': venue.get('name', ''),
        'city': venue.get('city', ''),
        'region': venue.get('state', ''),
        'country': venue.get('country', ''),
        'ticket_url': event.get('url', ''),
        'price_range': price_range,
        'source': 'seatgeek',
    }


def search_artist_events(artist_name, start_date, end_date):
    try:
        expected_artist = artist_name
        params = {
            'client_id': SEATGEEK_CLIENT_ID,
            'performers.slug': artist_name.lower().replace(' ', '-'),
            'type': 'concert',
            'datetime_utc.gte': f'{start_date}T00:00:00Z',
            'datetime_utc.lte': f'{end_date}T23:59:59Z',
            'per_page': 50,
        }

        r = requests.get(BASE_URL, params=params, timeout=15)
        if r.status_code != 200:
            logger.error('SeatGeek HTTP error for %s: %s', artist_name, r.status_code)
            return []

        data = r.json()
        events = data.get('events', [])
        results = []
        for event in events:
            if _is_package_event(event):
                continue
            if _is_tribute_or_fake(event):
                continue
            performers = _extract_performer_names(event)
            normalized_performers = {_normalize_name(name) for name in performers}
            expected_normalized = _normalize_name(expected_artist)
            # Strict check: normalized artist must exactly match one of the normalized performers
            if expected_normalized not in normalized_performers:
                continue
            result = _build_event_result(event, artist_name=expected_artist)
            if result:
                results.append(result)

        return results
    except Exception as e:
        logger.error('Error searching SeatGeek for %s: %s', artist_name, e)
        return []


def search_all_artists(artist_list, destinations, start_date, end_date):
    all_events = []
    for i, artist in enumerate(artist_list):
        artist_name = artist.get('artist_name', '')
        if not artist_name:
            continue
        logger.info('Searching SeatGeek for %s (%d/%d)', artist_name, i+1, len(artist_list))
        events = search_artist_events(artist_name, start_date, end_date)
        for event in events:
            if any(_event_matches_destination(event, dest) for dest in destinations):
                all_events.append(event)
        time.sleep(0.5)  # Rate limit
    return all_events
def search_city_events(city, state, country, start_date, end_date):
    try:
        params = {
            'client_id': SEATGEEK_CLIENT_ID,
            'venue.city': city,
            'venue.state': state,
            'venue.country': country,
            'type': 'concert',
            'datetime_utc.gte': f'{start_date}T00:00:00Z',
            'datetime_utc.lte': f'{end_date}T23:59:59Z',
            'per_page': 100,
        }

        r = requests.get(BASE_URL, params=params, timeout=15)
        if r.status_code != 200:
            logger.error('SeatGeek HTTP error for %s, %s: %s', city, state, r.status_code)
            return []

        data = r.json()
        events = data.get('events', [])
        results = []
        for event in events:
            if _is_package_event(event):
                continue
            if _is_tribute_or_fake(event):
                continue
            result = _build_event_result(event)
            if result:
                results.append(result)

        return results
    except Exception as e:
        logger.error('Error searching SeatGeek for %s, %s: %s', city, state, e)
        return []


def search_all_cities(destinations, start_date, end_date):
    all_events = []
    for i, dest in enumerate(destinations):
        city = dest.get('city', '')
        state = dest.get('state', '')
        country = dest.get('country', '')

        if not city or not state:
            continue

        logger.info('Searching SeatGeek for concerts in %s, %s (%d/%d)', city, state, i+1, len(destinations))
        events = search_city_events(city, state, country, start_date, end_date)
        all_events.extend(events)
        time.sleep(0.3)  # Rate limit
    return all_events
