#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from config import DESTINATIONS, PRIMARY_DATE_WINDOW
from spotify_client import get_my_top_artists
from bandsintown_client import search_artist_events
from ticketmaster_client import search_events_by_city

def debug_spotify_top_artists():
    print("=== 1. SPOTIFY TOP ARTISTS ===")
    try:
        artists = get_my_top_artists(limit=20)
        if artists:
            for i, artist in enumerate(artists, 1):
                print(f"{i}. {artist['artist_name']} (ID: {artist['spotify_id']}, Genres: {artist.get('genres', [])}, Popularity: {artist.get('popularity', 0)})")
        else:
            print("No artists returned from Spotify.")
    except Exception as e:
        print(f"Error getting Spotify artists: {e}")
    print()

def debug_bandsintown_api():
    print("=== 2. BANDSINTOWN SCRAPING TEST ===")
    try:
        artists = ['Bon Iver', 'Tyler Childers']
        for artist in artists:
            print(f"\n--- Scraping Bandsintown for: {artist} ---")
            events = search_artist_events(artist, PRIMARY_DATE_WINDOW[0], PRIMARY_DATE_WINDOW[1])
            print(f"Found {len(events)} events")
            if events:
                for event in events[:2]:  # Show first 2
                    print(f"  - {event['event_date']}: {event['venue_name']} in {event['city']}, {event['region']} ({event['source']})")
            else:
                print("  No events found.")
    except Exception as e:
        print(f"Error testing Bandsintown scraping: {e}")
    print()

def debug_ticketmaster_api():
    print("=== 3. TICKETMASTER API TEST ===")
    test_cities = [
        {'city': 'Austin', 'state': 'TX', 'country': 'US'},
        {'city': 'Nashville', 'state': 'TN', 'country': 'US'}
    ]
    try:
        for city_info in test_cities:
            print(f"\n--- Testing Ticketmaster for: {city_info['city']}, {city_info['state']} ---")
            events = search_events_by_city(city_info['city'], city_info['state'], city_info['country'], PRIMARY_DATE_WINDOW[0], PRIMARY_DATE_WINDOW[1])
            print(f"Found {len(events)} events")
            if events:
                for event in events[:3]:  # Show first 3
                    print(f"  - {event['event_date']}: {event['artist_name']} at {event['venue_name']} ({event['source']}) - Price: {event.get('price_range', 'N/A')}")
            else:
                print("  No events found.")
    except Exception as e:
        print(f"Error testing Ticketmaster: {e}")
    print()

def debug_city_matching():
    print("=== 4. CITY MATCHING LOGIC ===")
    print("Destinations and their search terms:")
    for dest in DESTINATIONS:
        print(f"  - {dest['name']}: Search terms: {dest['search_terms']}")
    print()

if __name__ == "__main__":
    debug_spotify_top_artists()
    debug_bandsintown_api()
    debug_ticketmaster_api()
    debug_city_matching()