#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path

from colorama import Fore, Style, init as colorama_init
from tabulate import tabulate

from seatgeek_client import search_all_artists as search_seatgeek_artists, search_all_cities as search_seatgeek_cities
from config import DESTINATIONS, PRIMARY_DATE_WINDOW, SECONDARY_DATE_WINDOW
from matcher import deduplicate_events, find_matches, sort_and_format_results
# Bandsintown is disabled - API returns 403 Forbidden
# from bandsintown_client import search_all_artists as search_bandsintown_all
from spotify_client import get_my_top_artists, get_playlist_artists, build_full_artist_list


def print_banner():
    print(Fore.CYAN + '🎵 Concert Finder for Billy & Gretchen 🎵' + Style.RESET_ALL)
    print('Finding shows in your favorite vacation spots!\n')


def print_date_window():
    print('📅 Primary travel window: May 25 - Aug 25, 2026')
    print('📅 Also checking: Sep 1 - Dec 31, 2026\n')


def dump_results(results, filename='results.txt'):
    lines = []
    for r in results:
        line = ' | '.join([f'{k}: {v}' for k, v in r.items()])
        lines.append(line)
    Path(filename).write_text('\n'.join(lines), encoding='utf-8')


def main():
    colorama_init(autoreset=True)
    parser = argparse.ArgumentParser(description='Concert Finder CLI')
    parser.add_argument('--playlist', type=str, help='Spotify playlist URL to include')
    parser.add_argument('--add-artist', action='append', help='Add artist name to search for', default=[])
    args = parser.parse_args()

    print_banner()

    sp_artists = get_my_top_artists()
    if not sp_artists:
        print(Fore.RED + 'Failed to load Spotify top artists. Exiting.' + Style.RESET_ALL)
        sys.exit(1)

    print(Fore.GREEN + '🎧 Based on your Spotify listening, your top artists are:' + Style.RESET_ALL)
    for i, a in enumerate(sp_artists[:20], start=1):
        print(f'{i}. {a.get("artist_name")} (pop {a.get("popularity")})')

    discovery_artists = []
    try:
        if not discovery_artists:
            print(Fore.CYAN + '\nBuilding discovery artist list...' + Style.RESET_ALL)
            _, discovery_artists = build_full_artist_list(include_similar=True)
    except Exception as e:
        print(Fore.YELLOW + f'⚠️  Warning: could not build discovery list: {e}' + Style.RESET_ALL)

    if discovery_artists:
        print(Fore.BLUE + f'\n🔍 Found {len(discovery_artists)} discovery artists you might love:' + Style.RESET_ALL)
        for i, a in enumerate(discovery_artists[:15], start=1):
            similar = ', '.join(a.get('similar_to', [])) or 'N/A'
            print(f'{i}. {a.get("artist_name")} (similar to: {similar})')
    else:
        print(Fore.YELLOW + '⚠️  No discovery artists found (this may indicate Spotify API access issues)' + Style.RESET_ALL)

    print('\n' + Fore.YELLOW + '📍 Searching for shows in your vacation spots:' + Style.RESET_ALL)
    for dest in DESTINATIONS:
        print(f'- {dest.get("name")}')

    print_date_window()

    artists_for_search = []
    artists_for_search.extend(sp_artists)

    if args.playlist:
        playlist_artists = get_playlist_artists(args.playlist)
        if playlist_artists:
            print('\n' + Fore.MAGENTA + f'🎶 Added {len(playlist_artists)} artists from playlist' + Style.RESET_ALL)
            artists_for_search.extend(playlist_artists)

    for name in args.add_artist or []:
        artists_for_search.append({'artist_name': name, 'spotify_id': None, 'genres': [], 'popularity': 0})

    grouped = {}
    for artist in artists_for_search:
        norm_l = (artist.get('artist_name') or '').strip().lower()
        if norm_l and norm_l not in grouped:
            grouped[norm_l] = artist
    artists_for_search = list(grouped.values())

    print(Fore.CYAN + f'\nSearching SeatGeek for {len(artists_for_search)} artists...' + Style.RESET_ALL)
    seatgeek_artist_events = search_seatgeek_artists(artists_for_search, DESTINATIONS, PRIMARY_DATE_WINDOW[0], SECONDARY_DATE_WINDOW[1])

    print(Fore.CYAN + f'\nSearching SeatGeek for concerts in {len(DESTINATIONS)} destination cities...' + Style.RESET_ALL)
    seatgeek_city_events = search_seatgeek_cities(DESTINATIONS, PRIMARY_DATE_WINDOW[0], SECONDARY_DATE_WINDOW[1])

    seatgeek_events = seatgeek_artist_events + seatgeek_city_events

    ticket_events = []
    print(Fore.YELLOW + '\nTicketmaster disabled: API key returns 401 Unauthorized, relying on SeatGeek only.' + Style.RESET_ALL)

    all_events = seatgeek_events + ticket_events
    print(f'\nTotal events collected: {len(all_events)} before deduplication')
    
    all_events = deduplicate_events(all_events)
    print(f'After deduplication: {len(all_events)} unique events')

    matches = find_matches(sp_artists, discovery_artists, all_events, DESTINATIONS)

    print('\n' + Fore.GREEN + '🎵 YOUR ARTISTS IN YOUR VACATION SPOTS (Memorial Day - Aug 25)' + Style.RESET_ALL)
    your_rows = [
        {'Date': e['event_date'], 'Artist': e['artist_name'], 'Venue': e['venue_name'], 'City': e['city'], 'Tickets': e['ticket_url']}
        for e in matches.get('your_artist', [])
    ]
    if your_rows:
        print(tabulate(your_rows, headers='keys', tablefmt='grid'))
    else:
        print('No shows found for your artists in the travel window.')

    print('\n' + Fore.BLUE + '🔍 NEW DISCOVERIES IN YOUR VACATION SPOTS (Memorial Day - Aug 25)' + Style.RESET_ALL)
    discovery_rows = [
        {'Date': e['event_date'], 'Artist': f"{e['artist_name']} (similar to {', '.join(e.get('similar_to', []))})", 'Venue': e['venue_name'], 'City': e['city'], 'Tickets': e['ticket_url']}
        for e in matches.get('discovery', [])
    ]
    if discovery_rows:
        print(tabulate(discovery_rows, headers='keys', tablefmt='grid'))
    else:
        print('No discovery shows found in the travel window.')

    print('\n' + Fore.YELLOW + '📅 OUTSIDE YOUR TRAVEL DATES (but worth knowing about)' + Style.RESET_ALL)
    outside_rows = [
        {'Date': e['event_date'], 'Artist': e['artist_name'], 'Venue': e['venue_name'], 'City': e['city'], 'Tickets': e['ticket_url']}
        for e in matches.get('outside_dates', [])
    ]
    if outside_rows:
        print(tabulate(outside_rows, headers='keys', tablefmt='grid'))
    else:
        print('No outside-window shows found.')

    your_count = len(matches.get('your_artist', []))
    discovery_count = len(matches.get('discovery', []))
    city_count = len({e.get('city') for e in all_events if e.get('city')})

    print('\n' + Fore.MAGENTA + f'Found {your_count} shows by your artists and {discovery_count} new discoveries across {city_count} cities!' + Style.RESET_ALL)

    output_rows = sort_and_format_results(matches)
    dump_results(output_rows, 'results.txt')
    print(Fore.GREEN + '\nSaved results to results.txt' + Style.RESET_ALL)


if __name__ == '__main__':
    main()
