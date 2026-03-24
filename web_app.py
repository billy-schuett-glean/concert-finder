#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from datetime import datetime
from collections import defaultdict
import sys

from spotify_client import get_my_top_artists, build_full_artist_list
from seatgeek_client import search_all_artists as search_seatgeek_artists, search_all_cities as search_seatgeek_cities
from config import DESTINATIONS, PRIMARY_DATE_WINDOW, SECONDARY_DATE_WINDOW
from matcher import deduplicate_events, find_matches

# Page config
st.set_page_config(
    page_title="Concert Finder - Billy & Gretchen",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #FF6B6B 0%, #4ECDC4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .summary-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0 2rem 0;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
    }

    .concert-card {
        background: #1E2129;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        border-left: 4px solid #FF6B6B;
        transition: transform 0.2s;
    }

    .concert-card:hover {
        transform: translateX(5px);
    }

    .artist-name {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #FAFAFA;
    }

    .concert-date {
        font-size: 1.1rem;
        color: #4ECDC4;
        margin-bottom: 0.25rem;
    }

    .venue-name {
        font-size: 0.95rem;
        color: #B8B8B8;
        margin-bottom: 0.5rem;
    }

    .badge-your {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .badge-discovery {
        background: linear-gradient(135deg, #4ECDC4 0%, #556270 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 0.5rem;
    }

    .destination-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FF6B6B;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #FF6B6B;
        padding-bottom: 0.5rem;
    }

    .artist-dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .sidebar-artist {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }

    .ticket-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        margin-top: 0.5rem;
        font-weight: 600;
        transition: opacity 0.2s;
    }

    .ticket-button:hover {
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

def get_artist_color(index):
    """Generate a color for artist dots based on index."""
    colors = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
        "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52B788",
        "#E63946", "#A8DADC", "#F4A261", "#2A9D8F", "#E76F51",
        "#264653", "#E9C46A", "#F4A261", "#E76F51", "#8AC926"
    ]
    return colors[index % len(colors)]

def format_concert_date(date_str):
    """Format date string to 'Friday, July 11'."""
    try:
        dt = datetime.strptime(date_str, '%a, %B %d, %Y')
        return dt.strftime('%A, %B %d')
    except:
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime('%A, %B %d')
        except:
            return date_str

def group_by_destination(matches):
    """Group events by destination city."""
    grouped = defaultdict(list)

    for event in matches:
        city = event.get('city', 'Unknown')
        grouped[city].append(event)

    return grouped

def render_concert_card(event):
    """Render a concert card with all details."""
    artist_name = event.get('artist_name', 'Unknown Artist')
    event_date = event.get('event_date', '')
    venue_name = event.get('venue_name', '')
    match_type = event.get('match_type', '')
    similar_to = event.get('similar_to', [])
    ticket_url = event.get('ticket_url', '')

    formatted_date = format_concert_date(event_date)

    # Create badge
    if match_type == 'your_artist':
        badge = '<span class="badge-your">YOUR ARTIST</span>'
    else:
        similar_text = f"similar to {', '.join(similar_to[:2])}" if similar_to else "discovery"
        badge = f'<span class="badge-discovery">DISCOVERY — {similar_text}</span>'

    card_html = f"""
    <div class="concert-card">
        <div class="artist-name">{artist_name}</div>
        <div class="concert-date">📅 {formatted_date}</div>
        <div class="venue-name">📍 {venue_name}</div>
        <div>{badge}</div>
        <a href="{ticket_url}" target="_blank" class="ticket-button">🎟️ Get Tickets</a>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def load_data():
    """Load and process all concert data."""
    # Get Spotify artists
    sp_artists = get_my_top_artists()
    if not sp_artists:
        st.error("Failed to load Spotify top artists.")
        return None, None, None

    # Get discovery artists
    discovery_artists = []
    try:
        with st.spinner('Building discovery artist list...'):
            _, discovery_artists = build_full_artist_list(include_similar=True)
    except Exception as e:
        st.warning(f'Could not build discovery list: {e}')

    # Search for events
    artists_for_search = sp_artists.copy()

    # Deduplicate
    grouped = {}
    for artist in artists_for_search:
        norm_l = (artist.get('artist_name') or '').strip().lower()
        if norm_l and norm_l not in grouped:
            grouped[norm_l] = artist
    artists_for_search = list(grouped.values())

    with st.spinner('Searching SeatGeek for concerts...'):
        seatgeek_artist_events = search_seatgeek_artists(
            artists_for_search,
            DESTINATIONS,
            PRIMARY_DATE_WINDOW[0],
            SECONDARY_DATE_WINDOW[1]
        )

        seatgeek_city_events = search_seatgeek_cities(
            DESTINATIONS,
            PRIMARY_DATE_WINDOW[0],
            SECONDARY_DATE_WINDOW[1]
        )

    all_events = seatgeek_artist_events + seatgeek_city_events
    all_events = deduplicate_events(all_events)

    # Find matches
    matches = find_matches(sp_artists, discovery_artists, all_events, DESTINATIONS)

    return sp_artists, discovery_artists, matches

def main():
    # Header
    st.markdown('<div class="main-header">🎵 Concert Finder — Summer Vacation Shows for You & Gretchen</div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("🎧 Your Top Artists")
        st.caption("Based on your Spotify listening")

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()

    # Load data
    try:
        sp_artists, discovery_artists, matches = load_data()

        if sp_artists is None:
            st.stop()

        # Display top artists in sidebar
        with st.sidebar:
            for i, artist in enumerate(sp_artists[:15]):
                color = get_artist_color(i)
                artist_name = artist.get('artist_name', 'Unknown')
                popularity = artist.get('popularity', 0)

                st.markdown(
                    f'<div class="sidebar-artist">'
                    f'<span class="artist-dot" style="background: {color};"></span>'
                    f'<span>{artist_name} ({popularity})</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Summary banner
        your_count = len(matches.get('your_artist', []))
        discovery_count = len(matches.get('discovery', []))

        all_matches = matches.get('your_artist', []) + matches.get('discovery', []) + matches.get('outside_dates', [])
        city_count = len({e.get('city') for e in all_matches if e.get('city')})

        st.markdown(
            f'<div class="summary-banner">'
            f'Found {your_count} shows by your artists and {discovery_count} discoveries across {city_count} cities!'
            f'</div>',
            unsafe_allow_html=True
        )

        # Create tabs
        tab1, tab2 = st.tabs(["🌞 Summer Window (May 25 - Aug 25)", "📅 Outside Your Dates"])

        with tab1:
            summer_events = matches.get('your_artist', []) + matches.get('discovery', [])

            if not summer_events:
                st.info("No concerts found in your summer travel window.")
            else:
                # Group by destination
                grouped = group_by_destination(summer_events)

                # Sort destinations by number of events
                sorted_destinations = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

                for city, events in sorted_destinations:
                    with st.expander(f"📍 {city} ({len(events)} show{'s' if len(events) != 1 else ''})", expanded=len(sorted_destinations) <= 3):
                        # Sort events by date
                        sorted_events = sorted(events, key=lambda x: x.get('event_date_raw', ''))

                        for event in sorted_events:
                            render_concert_card(event)

        with tab2:
            outside_events = matches.get('outside_dates', [])

            if not outside_events:
                st.info("No concerts found outside your travel window.")
            else:
                # Group by destination
                grouped = group_by_destination(outside_events)

                # Sort destinations by number of events
                sorted_destinations = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

                for city, events in sorted_destinations:
                    with st.expander(f"📍 {city} ({len(events)} show{'s' if len(events) != 1 else ''})", expanded=False):
                        # Sort events by date
                        sorted_events = sorted(events, key=lambda x: x.get('event_date_raw', ''))

                        for event in sorted_events:
                            render_concert_card(event)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.exception(e)

if __name__ == '__main__':
    main()
