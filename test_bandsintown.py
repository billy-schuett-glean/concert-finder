#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from bandsintown_client import search_artist_events
from config import PRIMARY_DATE_WINDOW, SECONDARY_DATE_WINDOW

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_bandsintown():
    """Test Bandsintown API with specific artists."""
    test_artists = ['Bon Iver', 'Tyler Childers', 'Father John Misty']

    print("Testing Bandsintown API with different request variations...")
    print(f"Date range: {PRIMARY_DATE_WINDOW[0]} to {SECONDARY_DATE_WINDOW[1]}")
    print()

    for artist in test_artists:
        print(f"Testing {artist}...")
        try:
            events = search_artist_events(artist, PRIMARY_DATE_WINDOW[0], SECONDARY_DATE_WINDOW[1])
            print(f"Found {len(events)} events for {artist}")

            for i, event in enumerate(events[:5], 1):  # Show first 5 events
                print(f"  {i}. {event['event_date']} - {event['venue_name']} in {event['city']}, {event['region']}")
                print(f"     Tickets: {event['ticket_url']}")

            if not events:
                print(f"  No events found for {artist}")

        except Exception as e:
            print(f"Error testing {artist}: {e}")

        print()

if __name__ == '__main__':
    test_bandsintown()