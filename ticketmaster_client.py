import logging
import time
from datetime import datetime

import requests

from config import TICKETMASTER_API_KEY

logger = logging.getLogger(__name__)
BASE_URL = 'https://app.ticketmaster.com/discovery/v2/events.json'


class TicketmasterUnauthorizedError(RuntimeError):
    pass


def _format_date(date_str):
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%a, %B %d, %Y'), dt.strftime('%Y-%m-%d')
    except Exception:
        return date_str, date_str


def _extract_artist_name(event):
    attractions = event.get('_embedded', {}).get('attractions', [])
    if attractions:
        return ', '.join([a.get('name', '') for a in attractions if a.get('name')])
    return 'Unknown Artist'


def _extract_performer_names(event):
    attractions = event.get('_embedded', {}).get('attractions', [])
    return [a.get('name', '').strip() for a in attractions if a.get('name')]


def _extract_price_range(event):
    price_ranges = event.get('priceRanges', [])
    if price_ranges:
        min_price = price_ranges[0].get('min')
        max_price = price_ranges[0].get('max')
        currency = price_ranges[0].get('currency', '')
        if min_price is not None and max_price is not None:
            return f"${min_price:.0f} - ${max_price:.0f} {currency}"
    return ''


def _parse_events(response_json):
    events = response_json.get('_embedded', {}).get('events', [])
    results = []
    for event in events:
        event_date_time = event.get('dates', {}).get('start', {}).get('dateTime')
        event_date, event_date_raw = _format_date(event_date_time or '')
        venue = (event.get('_embedded', {}).get('venues', []) or [{}])[0]

        results.append({
            'artist_name': _extract_artist_name(event),
            'performer_names': _extract_performer_names(event),
            'event_date': event_date,
            'event_date_raw': event_date_raw,
            'venue_name': venue.get('name', ''),
            'city': venue.get('city', {}).get('name', ''),
            'region': venue.get('state', {}).get('stateCode', '') or venue.get('country', {}).get('countryCode', ''),
            'country': venue.get('country', {}).get('countryCode', ''),
            'ticket_url': event.get('url', ''),
            'price_range': _extract_price_range(event),
            'source': 'ticketmaster',
        })
    return results


def search_events_by_city(city, state_code, country_code, start_date, end_date):
    page = 0
    all_results = []

    while True:
        params = {
            'apikey': TICKETMASTER_API_KEY,
            'city': city,
            'stateCode': state_code,
            'countryCode': country_code,
            'classificationName': 'music',
            'startDateTime': f'{start_date}T00:00:00Z',
            'endDateTime': f'{end_date}T23:59:59Z',
            'size': 50,
            'page': page,
        }

        try:
            r = requests.get(BASE_URL, params=params, timeout=15)
            if r.status_code == 401:
                raise TicketmasterUnauthorizedError('Ticketmaster API key returned 401 Unauthorized')
            r.raise_for_status()
            data = r.json()

            page_results = _parse_events(data)
            all_results.extend(page_results)

            page_info = data.get('page', {})
            if page >= page_info.get('totalPages', 0) - 1:
                break
            page += 1
            time.sleep(0.3)

        except TicketmasterUnauthorizedError:
            raise
        except requests.HTTPError as e:
            logger.warning('Ticketmaster HTTP error for city %s: %s', city, e)
            break
        except Exception as e:
            logger.warning('Ticketmaster error for city %s: %s', city, e)
            break

    return all_results


def search_artist_in_cities(artist_name, destinations, start_date, end_date):
    all_results = []
    for idx, dest in enumerate(destinations, start=1):
        try:
            params = {
                'apikey': TICKETMASTER_API_KEY,
                'keyword': artist_name,
                'city': dest.get('city'),
                'stateCode': dest.get('state'),
                'countryCode': dest.get('country'),
                'classificationName': 'music',
                'startDateTime': f'{start_date}T00:00:00Z',
                'endDateTime': f'{end_date}T23:59:59Z',
                'size': 50,
            }
            r = requests.get(BASE_URL, params=params, timeout=15)
            if r.status_code == 401:
                raise TicketmasterUnauthorizedError('Ticketmaster API key returned 401 Unauthorized')
            r.raise_for_status()
            data = r.json()
            events = _parse_events(data)
            for event in events:
                event['destination'] = dest.get('name')
            all_results.extend(events)
        except Exception as e:
            logger.warning('Ticketmaster search failed for %s in %s: %s', artist_name, dest.get('name'), e)

        if idx < len(destinations):
            time.sleep(0.3)

    return all_results


def search_all_destinations(destinations, start_date, end_date):
    all_results = []
    for idx, dest in enumerate(destinations, start=1):
        city = dest.get('city')
        state = dest.get('state')
        country = dest.get('country')

        if not city:
            continue

        results = search_events_by_city(city, state, country, start_date, end_date)
        for event in results:
            event['destination'] = dest.get('name')
        all_results.extend(results)

        if idx < len(destinations):
            time.sleep(0.3)
    return all_results


if __name__ == '__main__':
    print('ticketmaster_client loaded')
