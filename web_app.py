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

# Custom CSS - Premium Editorial Design
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@400;500;700&display=swap" rel="stylesheet">

<style>
    /* Base Styles */
    .stApp {
        background-color: #0a0a0a;
    }

    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Instrument Serif', serif !important;
        color: #e8e0d5 !important;
    }

    p, div, span, li {
        font-family: 'DM Sans', sans-serif !important;
        color: #e8e0d5 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hero Section */
    .hero-container {
        text-align: center;
        padding: 4rem 2rem 3rem 2rem;
        margin-bottom: 3rem;
        background: linear-gradient(180deg, rgba(212, 165, 116, 0.08) 0%, rgba(10, 10, 10, 0) 100%);
        border-bottom: 1px solid #2a2a2a;
    }

    .hero-title {
        font-family: 'Instrument Serif', serif;
        font-size: 5rem;
        font-weight: 400;
        font-style: italic;
        background: linear-gradient(135deg, #d4a574 0%, #e8d4b8 50%, #d4a574 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }

    .hero-subtitle {
        font-family: 'DM Sans', sans-serif;
        font-size: 1.25rem;
        color: #a89884;
        font-weight: 400;
        margin-bottom: 2rem;
        letter-spacing: 0.05em;
    }

    .summary-bar {
        display: inline-block;
        background: #141414;
        border: 1px solid #2a2a2a;
        padding: 1rem 2.5rem;
        border-radius: 50px;
        font-size: 1rem;
        color: #e8e0d5;
        font-weight: 500;
    }

    .summary-number {
        color: #d4a574;
        font-weight: 700;
        font-size: 1.1rem;
    }

    /* Custom Tabs */
    .tab-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 3rem;
        justify-content: center;
        border-bottom: 1px solid #2a2a2a;
        padding-bottom: 0;
    }

    .tab-button {
        font-family: 'Instrument Serif', serif;
        font-size: 1.5rem;
        color: #666;
        background: none;
        border: none;
        padding: 1rem 2rem;
        cursor: pointer;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
        font-style: italic;
    }

    .tab-button:hover {
        color: #d4a574;
    }

    .tab-button.active {
        color: #d4a574;
        border-bottom-color: #d4a574;
    }

    /* Destination Cards */
    .destination-card {
        background: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .destination-card:hover {
        border-color: #3a3a3a;
        transform: translateY(-2px);
    }

    .destination-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--city-gradient);
        opacity: 0.8;
    }

    .destination-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0;
    }

    .destination-name {
        font-family: 'Instrument Serif', serif;
        font-size: 2.5rem;
        font-weight: 400;
        color: #e8e0d5;
        margin: 0;
    }

    .show-count-badge {
        background: rgba(212, 165, 116, 0.15);
        color: #d4a574;
        padding: 0.5rem 1.25rem;
        border-radius: 50px;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        font-weight: 600;
        border: 1px solid rgba(212, 165, 116, 0.3);
    }

    /* Concert Cards */
    .concert-row {
        background: #0f0f0f;
        border: 1px solid #1a1a1a;
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.3s ease;
    }

    .concert-row:hover {
        background: #141414;
        border-color: #2a2a2a;
        transform: translateX(4px);
    }

    .concert-info {
        flex: 1;
    }

    .concert-artist {
        font-family: 'Instrument Serif', serif;
        font-size: 1.75rem;
        font-weight: 400;
        color: #e8e0d5;
        margin-bottom: 0.5rem;
    }

    .concert-date {
        font-family: 'DM Sans', sans-serif;
        font-size: 1rem;
        color: #d4a574;
        font-weight: 500;
        margin-bottom: 0.25rem;
    }

    .concert-venue {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: #888;
        font-weight: 400;
    }

    .concert-badges {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        margin-top: 0.75rem;
    }

    .badge-your-artist {
        background: rgba(212, 165, 116, 0.2);
        color: #d4a574;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid rgba(212, 165, 116, 0.3);
    }

    .badge-discovery {
        background: rgba(91, 158, 143, 0.2);
        color: #5b9e8f;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: 1px solid rgba(91, 158, 143, 0.3);
    }

    .ticket-link {
        font-family: 'DM Sans', sans-serif;
        color: #888;
        text-decoration: none;
        font-size: 0.95rem;
        font-weight: 500;
        transition: all 0.3s ease;
        white-space: nowrap;
    }

    .ticket-link:hover {
        color: #d4a574;
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #2a2a2a;
    }

    .sidebar-title {
        font-family: 'Instrument Serif', serif;
        font-size: 1.5rem;
        color: #e8e0d5;
        margin-bottom: 1.5rem;
        font-style: italic;
    }

    .artist-item {
        display: flex;
        align-items: center;
        margin-bottom: 0.75rem;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.9rem;
        color: #b8b0a5;
    }

    .artist-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 0.75rem;
        flex-shrink: 0;
    }

    /* City-specific gradients */
    .city-austin::before { background: linear-gradient(90deg, #d4a574, #e8a055); }
    .city-portland::before { background: linear-gradient(90deg, #5b9eb8, #4a7b9e); }
    .city-red-rocks::before { background: linear-gradient(90deg, #7b9e7d, #5d7c6f); }
    .city-berkeley::before { background: linear-gradient(90deg, #e8a055, #d47a54); }
    .city-montreal::before { background: linear-gradient(90deg, #5b8eb8, #4a6b9e); }
    .city-vancouver::before { background: linear-gradient(90deg, #5b9e8f, #4a7d7e); }
    .city-nashville::before { background: linear-gradient(90deg, #d4a574, #c49564); }
    .city-savannah::before { background: linear-gradient(90deg, #c4a574, #b49564); }
    .city-charleston::before { background: linear-gradient(90deg, #7b9eb8, #6a8da7); }
    .city-asheville::before { background: linear-gradient(90deg, #7b9e7d, #6a8d6c); }
    .city-morrison::before { background: linear-gradient(90deg, #7b9e7d, #5d7c6f); }
    .city-denver::before { background: linear-gradient(90deg, #7b9e7d, #5d7c6f); }

    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .concert-row {
        animation: fadeIn 0.4s ease-out;
    }

    /* Refresh button */
    .stButton button {
        background: #141414;
        color: #d4a574;
        border: 1px solid #2a2a2a;
        border-radius: 50px;
        padding: 0.5rem 1.5rem;
        font-family: 'DM Sans', sans-serif;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background: #1a1a1a;
        border-color: #d4a574;
    }
</style>
""", unsafe_allow_html=True)

def get_artist_color(index):
    """Generate a muted color for artist dots."""
    colors = [
        "#d4a574", "#5b9e8f", "#b89884", "#7b9e7d", "#c49564",
        "#5b8eb8", "#a88f74", "#6b8e7d", "#d49574", "#5b7e8f",
        "#c4a574", "#7b8e9e", "#b49564", "#6b9e8f", "#d4b584",
    ]
    return colors[index % len(colors)]

def get_city_class(city_name):
    """Get CSS class for city-specific gradients."""
    city_lower = city_name.lower()
    if 'austin' in city_lower:
        return 'city-austin'
    elif 'portland' in city_lower:
        return 'city-portland'
    elif 'morrison' in city_lower or 'denver' in city_lower:
        return 'city-morrison'
    elif 'berkeley' in city_lower or 'san francisco' in city_lower or 'oakland' in city_lower:
        return 'city-berkeley'
    elif 'montreal' in city_lower or 'montréal' in city_lower:
        return 'city-montreal'
    elif 'vancouver' in city_lower:
        return 'city-vancouver'
    elif 'nashville' in city_lower:
        return 'city-nashville'
    elif 'savannah' in city_lower:
        return 'city-savannah'
    elif 'charleston' in city_lower:
        return 'city-charleston'
    elif 'asheville' in city_lower:
        return 'city-asheville'
    else:
        return 'city-austin'  # default

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
    """Render a premium concert card."""
    artist_name = event.get('artist_name', 'Unknown Artist')
    event_date = event.get('event_date', '')
    venue_name = event.get('venue_name', '')
    match_type = event.get('match_type', '')
    similar_to = event.get('similar_to', [])
    ticket_url = event.get('ticket_url', '')

    formatted_date = format_concert_date(event_date)

    # Create badge
    if match_type == 'your_artist':
        badge = '<span class="badge-your-artist">Your Artist</span>'
    else:
        similar_text = f"Discovery — similar to {', '.join(similar_to[:2])}" if similar_to else "Discovery"
        badge = f'<span class="badge-discovery">{similar_text}</span>'

    card_html = f"""
    <div class="concert-row">
        <div class="concert-info">
            <div class="concert-artist">{artist_name}</div>
            <div class="concert-date">{formatted_date}</div>
            <div class="concert-venue">{venue_name}</div>
            <div class="concert-badges">
                {badge}
            </div>
        </div>
        <a href="{ticket_url}" target="_blank" class="ticket-link">Get Tickets →</a>
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

def render_destination_section(city, events, expanded=True):
    """Render a destination card with concerts."""
    city_class = get_city_class(city)
    show_count = len(events)
    show_text = "show" if show_count == 1 else "shows"

    # Use Streamlit expander but with custom styling
    with st.expander(f"", expanded=expanded):
        # Custom header inside expander
        st.markdown(
            f'<div class="destination-card {city_class}">'
            f'<div class="destination-header">'
            f'<div class="destination-name">{city}</div>'
            f'<div class="show-count-badge">{show_count} {show_text}</div>'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Sort events by date
        sorted_events = sorted(events, key=lambda x: x.get('event_date_raw', ''))

        for event in sorted_events:
            render_concert_card(event)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-title">Your Artists</div>', unsafe_allow_html=True)

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Load data
    try:
        sp_artists, discovery_artists, matches = load_data()

        if sp_artists is None:
            st.stop()

        # Display top artists in sidebar
        with st.sidebar:
            for i, artist in enumerate(sp_artists[:20]):
                color = get_artist_color(i)
                artist_name = artist.get('artist_name', 'Unknown')

                st.markdown(
                    f'<div class="artist-item">'
                    f'<span class="artist-dot" style="background: {color};"></span>'
                    f'<span>{artist_name}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Hero Section
        your_count = len(matches.get('your_artist', []))
        discovery_count = len(matches.get('discovery', []))
        all_matches = matches.get('your_artist', []) + matches.get('discovery', []) + matches.get('outside_dates', [])
        city_count = len({e.get('city') for e in all_matches if e.get('city')})

        st.markdown(
            f'<div class="hero-container">'
            f'<div class="hero-title">Concert Finder</div>'
            f'<div class="hero-subtitle">Summer Shows for Billy & Gretchen</div>'
            f'<div class="summary-bar">'
            f'<span class="summary-number">{your_count}</span> shows by your artists + '
            f'<span class="summary-number">{discovery_count}</span> discoveries across '
            f'<span class="summary-number">{city_count}</span> cities'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Tab selection using session state
        if 'active_tab' not in st.session_state:
            st.session_state.active_tab = 'summer'

        # Custom tab buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                if st.button("Your Summer", key="tab_summer", use_container_width=True):
                    st.session_state.active_tab = 'summer'
            with subcol2:
                if st.button("Worth the Trip", key="tab_outside", use_container_width=True):
                    st.session_state.active_tab = 'outside'

        st.markdown("<br>", unsafe_allow_html=True)

        # Show content based on active tab
        if st.session_state.active_tab == 'summer':
            summer_events = matches.get('your_artist', []) + matches.get('discovery', [])

            if not summer_events:
                st.markdown('<div style="text-align: center; color: #888; padding: 3rem;">No concerts found in your summer travel window.</div>', unsafe_allow_html=True)
            else:
                # Group by destination
                grouped = group_by_destination(summer_events)

                # Sort destinations by number of events
                sorted_destinations = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

                for city, events in sorted_destinations:
                    render_destination_section(city, events, expanded=len(sorted_destinations) <= 3)

        else:  # outside dates
            outside_events = matches.get('outside_dates', [])

            if not outside_events:
                st.markdown('<div style="text-align: center; color: #888; padding: 3rem;">No concerts found outside your travel window.</div>', unsafe_allow_html=True)
            else:
                # Group by destination
                grouped = group_by_destination(outside_events)

                # Sort destinations by number of events
                sorted_destinations = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

                for city, events in sorted_destinations:
                    render_destination_section(city, events, expanded=False)

    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.exception(e)

if __name__ == '__main__':
    main()
