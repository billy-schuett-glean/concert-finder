import re
from datetime import datetime
from difflib import SequenceMatcher

from config import PRIMARY_DATE_WINDOW


def normalize_artist_name(name):
    """Normalize artist name for basic comparison."""
    if not name or not isinstance(name, str):
        return ''
    n = name.lower().strip()
    n = re.sub(r"^the\s+", '', n)
    n = re.sub(r"[^a-z0-9&]+", ' ', n)
    n = re.sub(r"\s+", ' ', n).strip()
    return n


def fuzzy_match_artist(event_artist, spotify_artists, threshold=0.75):
    """Try to match event artist to Spotify artist using fuzzy matching.
    
    Returns tuple: (matched_artist_info, is_exact_match, similarity_score)
    """
    event_norm = normalize_artist_name(event_artist)
    if not event_norm:
        return None, False, 0.0
    
    best_match = None
    best_score = 0.0
    
    for spotify_artist_info in spotify_artists:
        spotify_name = spotify_artist_info.get('artist_name', '')
        if not spotify_name:
            continue
        
        spotify_norm = normalize_artist_name(spotify_name)
        
        # Exact match after normalization
        if event_norm == spotify_norm:
            return spotify_artist_info, True, 1.0
        
        # Fuzzy match
        ratio = SequenceMatcher(None, event_norm, spotify_norm).ratio()
        if ratio > best_score:
            best_score = ratio
            best_match = spotify_artist_info
    
    # Return match if it exceeds threshold
    if best_score >= threshold:
        return best_match, False, best_score
    
    return None, False, best_score


def _in_window(date_raw, window):
    try:
        dt = datetime.fromisoformat(date_raw)
    except Exception:
        return False
    start = datetime.fromisoformat(window[0])
    end = datetime.fromisoformat(window[1])
    return start <= dt <= end


def find_matches(my_artists, discovery_artists, all_events, destinations):
    """Match events to Spotify artists using exact and fuzzy matching."""
    your_map = {}
    your_list = [a for a in my_artists if a.get('artist_name')]
    for artist in my_artists:
        norm = normalize_artist_name(artist.get('artist_name'))
        if norm:
            your_map[norm] = artist

    disc_map = {}
    disc_list = [a for a in discovery_artists if a.get('artist_name')]
    similarity = {}
    for artist in discovery_artists:
        norm = normalize_artist_name(artist.get('artist_name'))
        if norm:
            disc_map[norm] = artist
            similarity[norm] = artist.get('similar_to', [])

    categories = {'your_artist': [], 'discovery': [], 'outside_dates': []}

    for event in all_events:
        performer_names = [name for name in event.get('performer_names', []) if name]
        candidate_names = performer_names or [event.get('artist_name') or '']
        normalized_candidates = [normalize_artist_name(name) for name in candidate_names if normalize_artist_name(name)]

        if not normalized_candidates:
            continue

        match_type = None
        similar_to = []
        matched_name = None

        for idx, norm_artist in enumerate(normalized_candidates):
            if norm_artist in your_map:
                match_type = 'your_artist'
                matched_name = candidate_names[idx]
                break
            if norm_artist in disc_map:
                match_type = 'discovery'
                similar_to = similarity.get(norm_artist, [])
                matched_name = candidate_names[idx]
                break

        # Only use fuzzy matching when the upstream source did not provide structured performers.
        if not match_type and not performer_names:
            for candidate_name in candidate_names:
                matched_artist, is_exact, score = fuzzy_match_artist(candidate_name, your_list, threshold=0.92)
                if matched_artist:
                    match_type = 'your_artist'
                    matched_name = matched_artist.get('artist_name') or candidate_name
                    break

        if not match_type and not performer_names:
            for candidate_name in candidate_names:
                matched_artist, is_exact, score = fuzzy_match_artist(candidate_name, disc_list, threshold=0.92)
                if matched_artist:
                    match_type = 'discovery'
                    similar_to = matched_artist.get('similar_to', [])
                    matched_name = matched_artist.get('artist_name') or candidate_name
                    break

        if not match_type:
            continue

        raw_date = event.get('event_date_raw') or event.get('event_date')
        in_travel_window = _in_window(raw_date, PRIMARY_DATE_WINDOW)

        match_info = {
            'artist_name': matched_name or event.get('artist_name', ''),
            'match_type': match_type,
            'similar_to': similar_to,
            'event_date': event.get('event_date', ''),
            'venue_name': event.get('venue_name', ''),
            'city': event.get('city', ''),
            'state': event.get('region', ''),
            'ticket_url': event.get('ticket_url', ''),
            'source': event.get('source', ''),
            'price_range': event.get('price_range', ''),
            'in_travel_window': in_travel_window,
            'event_date_raw': raw_date,
            'destination': event.get('destination', ''),
            'performer_names': performer_names,
        }

        if in_travel_window:
            categories[match_type].append(match_info)
        else:
            categories['outside_dates'].append(match_info)

    return categories


def deduplicate_events(events):
    unique = {}

    for event in events:
        artist = normalize_artist_name(event.get('artist_name'))
        city = (event.get('city') or '').strip().lower()
        date_raw = event.get('event_date_raw') or event.get('event_date')

        if not artist or not city or not date_raw:
            key = f"{artist}|{city}|{date_raw}"
        else:
            try:
                d = datetime.fromisoformat(date_raw)
                key = f"{artist}|{city}|{d.strftime('%Y-%m-%d')}"
            except Exception:
                key = f"{artist}|{city}|{date_raw}"

        existing = unique.get(key)
        if not existing:
            unique[key] = event
            continue

        existing_price = existing.get('price_range', '')
        new_price = event.get('price_range', '')

        if new_price and not existing_price:
            unique[key] = event
        elif new_price and existing_price:
            unique[key] = event if len(new_price) >= len(existing_price) else existing

    return list(unique.values())


def sort_and_format_results(matches):
    flattened = []

    for cat in ['your_artist', 'discovery', 'outside_dates']:
        for item in matches.get(cat, []):
            flattened.append(item)

    def key_fn(item):
        return (
            0 if item.get('in_travel_window') else 1,
            item.get('event_date_raw', ''),
            0 if item.get('match_type') == 'your_artist' else 1,
        )

    sorted_items = sorted(flattened, key=key_fn)

    formatted = []
    for item in sorted_items:
        formatted.append({
            'Date': item.get('event_date', ''),
            'Artist': item.get('artist_name', ''),
            'Type': item.get('match_type', ''),
            'SimilarTo': ', '.join(item.get('similar_to', [])) if item.get('match_type') == 'discovery' else '',
            'Venue': item.get('venue_name', ''),
            'City': item.get('city', ''),
            'State': item.get('state', ''),
            'Source': item.get('source', ''),
            'Price': item.get('price_range', ''),
            'Tickets': item.get('ticket_url', ''),
            'InTravelWindow': item.get('in_travel_window', False),
            'Destination': item.get('destination', ''),
        })

    return formatted


if __name__ == '__main__':
    print('matcher module loaded')
