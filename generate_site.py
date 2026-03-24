#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a beautiful static HTML site from results.txt
"""

from datetime import datetime, timedelta
from collections import defaultdict
import calendar as cal
import re


# City/Venue color mappings
CITY_COLORS = {
    'Morrison': '#c45c3a',  # Red Rocks - warm red/rust
    'Portland': '#4a90a4',  # ocean blue
    'Berkeley': '#6b8f4a',  # Greek Theatre - eucalyptus green
    'Charleston': '#9b7cb4',  # lavender
    'North Charleston': '#9b7cb4',  # same as Charleston
    'Nashville': '#c9956b',  # warm gold
    'Austin': '#d4763a',  # burnt orange
    'Asheville': '#5b8f7b',  # mountain green
    'Montreal': '#7a8db5',  # steel blue
    'Vancouver': '#4a7a6a',  # pacific teal
    'Savannah': '#b89c6a',  # spanish moss gold
}

# Venue name mappings for display
VENUE_DISPLAY = {
    'Morrison': 'Red Rocks Amphitheatre',
    'Portland': "Thompson's Point",
    'Berkeley': 'Greek Theatre at U.C. Berkeley',
}


def get_city_color(city):
    """Get the color for a city."""
    return CITY_COLORS.get(city, '#c9956b')  # Default to gold


def parse_results_file(filename='results.txt'):
    """Parse the results.txt file and return structured data."""
    concerts = []

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                # Parse pipe-delimited format
                parts = {}
                for part in line.split(' | '):
                    if ':' in part:
                        key, value = part.split(':', 1)
                        parts[key.strip()] = value.strip()

                # Extract relevant fields
                concert = {
                    'date': parts.get('Date', ''),
                    'artist': parts.get('Artist', ''),
                    'type': parts.get('Type', ''),
                    'similar_to': parts.get('SimilarTo', ''),
                    'venue': parts.get('Venue', ''),
                    'city': parts.get('City', ''),
                    'state': parts.get('State', ''),
                    'tickets': parts.get('Tickets', ''),
                    'in_window': parts.get('InTravelWindow', '') == 'True',
                }

                # Parse date to get month/year for grouping
                try:
                    dt = datetime.strptime(concert['date'], '%a, %B %d, %Y')
                    concert['date_obj'] = dt
                    concert['month_year'] = dt.strftime('%B %Y')
                    concert['month'] = dt.strftime('%B')
                    concert['day'] = dt.strftime('%d')
                    concert['weekday'] = dt.strftime('%A')
                except:
                    concert['date_obj'] = None
                    concert['month_year'] = 'Unknown'
                    concert['month'] = 'Unknown'
                    concert['day'] = ''
                    concert['weekday'] = ''

                concerts.append(concert)

    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return []

    # Sort by date
    concerts.sort(key=lambda x: x['date_obj'] if x['date_obj'] else datetime.max)

    return concerts


def generate_html(concerts):
    """Generate beautiful HTML from concert data."""

    # Get statistics
    total_shows = len([c for c in concerts if c['in_window']])
    cities = set(c['city'] for c in concerts if c['in_window'])
    city_count = len(cities)
    discovery_count = len([c for c in concerts if c['in_window'] and c['type'] == 'discovery'])

    # Get summer concerts (in window)
    summer_concerts = [c for c in concerts if c['in_window']]
    outside_concerts = [c for c in concerts if not c['in_window']]

    # Group by city/venue for "By Venue" view
    def group_by_city(concert_list):
        grouped = defaultdict(list)
        for concert in concert_list:
            city = concert['city']
            grouped[city].append(concert)
        return grouped

    summer_by_city = group_by_city(summer_concerts)

    # Group by month
    def group_by_month(concert_list):
        grouped = defaultdict(list)
        for concert in concert_list:
            grouped[concert['month_year']].append(concert)
        return grouped

    summer_by_month = group_by_month(summer_concerts)
    outside_by_month = group_by_month(outside_concerts)

    # Generate "By Venue" view HTML
    def generate_venue_view():
        html = '<div class="venue-grid">'

        # Sort cities by number of shows
        sorted_cities = sorted(summer_by_city.items(), key=lambda x: len(x[1]), reverse=True)

        for city, city_concerts in sorted_cities:
            color = get_city_color(city)
            show_count = len(city_concerts)
            show_text = "show" if show_count == 1 else "shows"

            # Get venue name
            venue_name = VENUE_DISPLAY.get(city, city_concerts[0]['venue'] if city_concerts else '')

            # Get unique artists for preview
            artists = list(dict.fromkeys([c['artist'] for c in city_concerts[:3]]))
            artist_preview = ', '.join(artists[:3])
            if len(city_concerts) > 3:
                artist_preview += f" +{len(city_concerts) - 3} more"

            html += f'''
            <div class="venue-card" data-city="{city}" style="--venue-color: {color}">
                <div class="venue-card-header">
                    <div class="venue-city">{city}</div>
                    <div class="venue-name">{venue_name}</div>
                    <div class="venue-count">{show_count} {show_text}</div>
                </div>
                <div class="venue-preview">{artist_preview}</div>
                <div class="venue-concerts hidden">
            '''

            # Add concert details for this venue
            sorted_concerts = sorted(city_concerts, key=lambda x: x['date_obj'] if x['date_obj'] else datetime.max)
            for concert in sorted_concerts:
                badge_class = 'badge-your' if concert['type'] == 'your_artist' else 'badge-discovery'
                badge_text = 'YOUR ARTIST' if concert['type'] == 'your_artist' else f"DISCOVERY — similar to {concert['similar_to']}" if concert['similar_to'] else 'DISCOVERY'

                html += f'''
                <div class="venue-concert-item">
                    <div class="venue-concert-artist">{concert['artist']}</div>
                    <div class="venue-concert-date">{concert['weekday']}, {concert['month']} {concert['day']}</div>
                    <span class="badge {badge_class}">{badge_text}</span>
                    <a href="{concert['tickets']}" target="_blank" class="venue-ticket-link">Tickets →</a>
                </div>
                '''

            html += '''
                </div>
            </div>
            '''

        html += '</div>'
        return html

    # Generate calendar view HTML
    def generate_calendar_view():
        html = ''

        # Generate calendars for May, June, July, August 2026
        months = [
            (2026, 5, 'May 2026'),
            (2026, 6, 'June 2026'),
            (2026, 7, 'July 2026'),
            (2026, 8, 'August 2026'),
        ]

        for year, month, month_name in months:
            html += f'''
            <div class="calendar-month">
                <div class="calendar-month-title">{month_name}</div>
                <div class="calendar-grid">
            '''

            # Day headers
            html += '<div class="calendar-day-header">Sun</div>'
            html += '<div class="calendar-day-header">Mon</div>'
            html += '<div class="calendar-day-header">Tue</div>'
            html += '<div class="calendar-day-header">Wed</div>'
            html += '<div class="calendar-day-header">Thu</div>'
            html += '<div class="calendar-day-header">Fri</div>'
            html += '<div class="calendar-day-header">Sat</div>'

            # Get calendar for this month
            month_cal = cal.monthcalendar(year, month)

            # Build concert lookup by date
            concerts_by_date = defaultdict(list)
            for concert in summer_concerts:
                if concert['date_obj'] and concert['date_obj'].year == year and concert['date_obj'].month == month:
                    day = concert['date_obj'].day
                    concerts_by_date[day].append(concert)

            # Generate calendar days
            for week in month_cal:
                for day in week:
                    if day == 0:
                        # Empty cell
                        html += '<div class="calendar-day empty"></div>'
                    else:
                        day_concerts = concerts_by_date.get(day, [])
                        has_concerts = len(day_concerts) > 0

                        html += f'<div class="calendar-day {"has-concerts" if has_concerts else ""}" data-date="{year}-{month:02d}-{day:02d}">'
                        html += f'<div class="calendar-day-number">{day}</div>'

                        if has_concerts:
                            html += '<div class="calendar-concerts">'
                            for concert in day_concerts:
                                city_color = get_city_color(concert['city'])
                                badge_class = 'badge-your' if concert['type'] == 'your_artist' else 'badge-discovery'
                                badge_text = 'YOUR ARTIST' if concert['type'] == 'your_artist' else f"DISCOVERY — similar to {concert['similar_to']}" if concert['similar_to'] else 'DISCOVERY'

                                # Escape quotes for data attributes
                                artist_safe = concert['artist'].replace('"', '&quot;')
                                venue_safe = concert['venue'].replace('"', '&quot;')
                                city_safe = f"{concert['city']}, {concert['state']}".replace('"', '&quot;')
                                date_safe = f"{concert['weekday']}, {concert['month']} {concert['day']}".replace('"', '&quot;')
                                badge_safe = badge_text.replace('"', '&quot;')

                                html += f'''
                                <div class="calendar-event" style="background: {city_color};"
                                     data-artist="{artist_safe}"
                                     data-venue="{venue_safe}"
                                     data-city="{city_safe}"
                                     data-date="{date_safe}"
                                     data-badge="{badge_safe}"
                                     data-badge-class="{badge_class}"
                                     data-tickets="{concert['tickets']}">
                                    {concert['artist'][:20]}{"..." if len(concert['artist']) > 20 else ""}
                                </div>
                                '''
                            html += '</div>'

                        html += '</div>'

            html += '''
                </div>
            </div>
            '''

        return html

    # Generate concert cards HTML (for list view)
    def generate_concert_cards(concerts_by_month):
        html = ""
        for month_year, month_concerts in concerts_by_month.items():
            html += f'''
            <div class="month-divider" data-month="{month_year}">
                <span>{month_year}</span>
            </div>
            '''

            for concert in month_concerts:
                badge_class = 'badge-your' if concert['type'] == 'your_artist' else 'badge-discovery'
                badge_text = 'YOUR ARTIST' if concert['type'] == 'your_artist' else f"DISCOVERY — similar to {concert['similar_to']}" if concert['similar_to'] else 'DISCOVERY'

                html += f'''
            <div class="concert-card" data-city="{concert['city']}" data-month="{month_year}">
                <div class="concert-main">
                    <div class="concert-artist">{concert['artist']}</div>
                    <div class="concert-details">
                        <span class="concert-date">{concert['weekday']}, {concert['month']} {concert['day']}</span>
                        <span class="concert-separator">·</span>
                        <span class="concert-venue">{concert['venue']}, {concert['city']}, {concert['state']}</span>
                    </div>
                    <div class="concert-footer">
                        <span class="badge {badge_class}">{badge_text}</span>
                    </div>
                </div>
                <a href="{concert['tickets']}" target="_blank" class="ticket-link">Tickets →</a>
            </div>
                '''

        return html

    summer_html = generate_concert_cards(summer_by_month)
    outside_html = generate_concert_cards(outside_by_month)

    # Generate the three views
    venue_view_html = generate_venue_view()
    calendar_view_html = generate_calendar_view()

    # Generate city filter buttons for list view
    all_cities = sorted(cities)
    city_buttons = ''.join([f'<button class="city-filter" data-city="{city}">{city}</button>' for city in all_cities])

    # Full HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Concert Finder — Summer 2026</title>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400;1,700&family=Source+Sans+3:wght@300;400;600;700&display=swap" rel="stylesheet">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background: #0d0d0d;
            color: #e2ddd5;
            font-family: 'Source Sans 3', sans-serif;
            line-height: 1.6;
            overflow-x: hidden;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 2rem;
        }}

        /* Navigation */
        .nav {{
            background: rgba(255,255,255,0.04);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 1rem 0;
            position: sticky;
            top: 0;
            z-index: 100;
            backdrop-filter: blur(10px);
        }}

        .nav-buttons {{
            display: flex;
            gap: 1rem;
            justify-content: center;
        }}

        .nav-button {{
            background: transparent;
            border: none;
            color: #888;
            padding: 0.75rem 2rem;
            font-family: 'Source Sans 3', sans-serif;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }}

        .nav-button:hover {{
            color: #c9956b;
        }}

        .nav-button.active {{
            color: #c9956b;
            border-bottom-color: #c9956b;
        }}

        /* Hero Section */
        .hero {{
            text-align: center;
            padding: 4rem 2rem 3rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}

        .hero-title {{
            font-family: 'Playfair Display', serif;
            font-size: clamp(3rem, 10vw, 7rem);
            font-style: italic;
            font-weight: 400;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #c9956b 0%, #e8c9a8 50%, #c9956b 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
        }}

        .hero-subtitle {{
            font-size: 1.25rem;
            color: #a89884;
            font-weight: 300;
            margin-bottom: 2.5rem;
            letter-spacing: 0.05em;
        }}

        .stats-bar {{
            display: inline-flex;
            gap: 2rem;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 1rem 2.5rem;
            border-radius: 50px;
            font-size: 1rem;
        }}

        .stat {{
            color: #c9956b;
            font-weight: 600;
        }}

        .stat-label {{
            color: #888;
            font-weight: 400;
            margin-left: 0.25rem;
        }}

        /* View containers */
        .view {{
            display: none;
            padding: 3rem 0;
        }}

        .view.active {{
            display: block;
        }}

        /* Venue View */
        .venue-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }}

        .venue-card {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 2rem;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .venue-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: var(--venue-color);
        }}

        .venue-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(255,255,255,0.15);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}

        .venue-card.expanded {{
            grid-column: 1 / -1;
        }}

        .venue-card-header {{
            margin-bottom: 1rem;
        }}

        .venue-city {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            font-weight: 600;
            color: var(--venue-color);
            margin-bottom: 0.5rem;
        }}

        .venue-name {{
            font-size: 1rem;
            color: #888;
            margin-bottom: 0.75rem;
        }}

        .venue-count {{
            background: rgba(255,255,255,0.08);
            display: inline-block;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--venue-color);
            font-weight: 600;
        }}

        .venue-preview {{
            color: #a89884;
            font-size: 0.95rem;
            margin-top: 1rem;
        }}

        .venue-concerts {{
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid rgba(255,255,255,0.08);
        }}

        .venue-concerts.hidden {{
            display: none;
        }}

        .venue-concert-item {{
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            display: grid;
            grid-template-columns: 1fr auto auto;
            gap: 1rem;
            align-items: center;
        }}

        .venue-concert-artist {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3rem;
            color: #e2ddd5;
            grid-column: 1 / -1;
        }}

        .venue-concert-date {{
            color: #c9956b;
            font-size: 0.95rem;
        }}

        .venue-ticket-link {{
            color: #888;
            text-decoration: none;
            transition: color 0.3s;
        }}

        .venue-ticket-link:hover {{
            color: #c9956b;
        }}

        /* Calendar View */
        .calendar-month {{
            margin-bottom: 4rem;
        }}

        .calendar-month-title {{
            font-family: 'Playfair Display', serif;
            font-size: 2.5rem;
            font-style: italic;
            color: #c9956b;
            margin-bottom: 2rem;
            text-align: center;
        }}

        .calendar-grid {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .calendar-day-header {{
            text-align: center;
            padding: 1rem 0.5rem;
            font-weight: 600;
            color: #888;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .calendar-day {{
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 0.75rem;
            min-height: 120px;
            position: relative;
            transition: all 0.3s ease;
        }}

        .calendar-day.empty {{
            background: transparent;
            border: none;
        }}

        .calendar-day.has-concerts {{
            background: rgba(255,255,255,0.04);
            border-color: rgba(255,255,255,0.08);
        }}

        .calendar-day.has-concerts:hover {{
            background: rgba(255,255,255,0.06);
        }}

        .calendar-day-number {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}

        .calendar-day.has-concerts .calendar-day-number {{
            color: #c9956b;
        }}

        .calendar-concerts {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}

        .calendar-event {{
            padding: 0.4rem 0.6rem;
            border-radius: 6px;
            font-size: 0.75rem;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .calendar-event:hover {{
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10;
        }}

        /* Event Popup */
        .event-popup {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #1a1a1a;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            padding: 2.5rem;
            max-width: 500px;
            width: 90%;
            z-index: 1000;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            display: none;
        }}

        .event-popup.active {{
            display: block;
        }}

        .popup-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 999;
            display: none;
        }}

        .popup-overlay.active {{
            display: block;
        }}

        .popup-close {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: transparent;
            border: none;
            color: #888;
            font-size: 2rem;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: color 0.3s;
        }}

        .popup-close:hover {{
            color: #c9956b;
        }}

        .popup-artist {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            color: #e2ddd5;
            margin-bottom: 1rem;
        }}

        .popup-details {{
            color: #a89884;
            font-size: 1rem;
            margin-bottom: 1.5rem;
            line-height: 1.8;
        }}

        .popup-ticket-btn {{
            display: inline-block;
            background: linear-gradient(135deg, #c9956b, #d4a574);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .popup-ticket-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(201, 149, 107, 0.3);
        }}

        /* List View (existing styles) */
        .filters {{
            padding: 2rem 0;
            text-align: center;
        }}

        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            justify-content: center;
            margin-top: 1.5rem;
        }}

        .city-filter {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            color: #888;
            padding: 0.6rem 1.5rem;
            border-radius: 50px;
            font-family: 'Source Sans 3', sans-serif;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }}

        .city-filter:hover {{
            background: rgba(255,255,255,0.08);
            border-color: rgba(201, 149, 107, 0.3);
            color: #c9956b;
        }}

        .city-filter.active {{
            background: rgba(201, 149, 107, 0.15);
            border-color: #c9956b;
            color: #c9956b;
        }}

        .tabs {{
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-bottom: 3rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 0;
        }}

        .tab-button {{
            border-radius: 0;
            border: none;
            border-bottom: 3px solid transparent;
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
            font-style: italic;
            padding: 1rem 2rem;
            background: transparent;
            color: #888;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .tab-button:hover {{
            color: #c9956b;
        }}

        .tab-button.active {{
            border-bottom-color: #c9956b;
            color: #c9956b;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .month-divider {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            font-style: italic;
            color: #c9956b;
            margin: 3rem 0 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(201, 149, 107, 0.3);
        }}

        .concert-card {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1.75rem 2rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            opacity: 0;
            transform: translateY(20px);
            animation: fadeInUp 0.6s ease forwards;
        }}

        @keyframes fadeInUp {{
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .concert-card:hover {{
            background: rgba(255,255,255,0.06);
            border-color: rgba(255,255,255,0.12);
            transform: translateX(8px);
        }}

        .concert-main {{
            flex: 1;
        }}

        .concert-artist {{
            font-family: 'Playfair Display', serif;
            font-size: 1.75rem;
            font-weight: 600;
            color: #e2ddd5;
            margin-bottom: 0.5rem;
        }}

        .concert-details {{
            font-size: 1rem;
            color: #a89884;
            margin-bottom: 0.75rem;
        }}

        .concert-date {{
            color: #c9956b;
            font-weight: 600;
        }}

        .concert-separator {{
            margin: 0 0.5rem;
            color: #555;
        }}

        .concert-venue {{
            color: #888;
        }}

        .concert-footer {{
            display: flex;
            gap: 0.75rem;
        }}

        .badge {{
            padding: 0.4rem 1rem;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .badge-your {{
            background: rgba(201, 149, 107, 0.2);
            color: #c9956b;
            border: 1px solid rgba(201, 149, 107, 0.3);
        }}

        .badge-discovery {{
            background: rgba(106, 170, 156, 0.2);
            color: #6aaa9c;
            border: 1px solid rgba(106, 170, 156, 0.3);
        }}

        .ticket-link {{
            color: #888;
            text-decoration: none;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            white-space: nowrap;
            padding: 0.5rem 1rem;
        }}

        .ticket-link:hover {{
            color: #c9956b;
        }}

        .concert-card.hidden {{
            display: none;
        }}

        .month-divider.hidden {{
            display: none;
        }}

        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: #666;
            font-size: 1.1rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero {{
                padding: 3rem 1.5rem 2rem;
            }}

            .hero-title {{
                font-size: 3rem;
            }}

            .stats-bar {{
                flex-direction: column;
                gap: 0.75rem;
                padding: 1.5rem 2rem;
            }}

            .nav-buttons {{
                gap: 0.5rem;
            }}

            .nav-button {{
                padding: 0.6rem 1rem;
                font-size: 0.9rem;
            }}

            .venue-grid {{
                grid-template-columns: 1fr;
            }}

            .calendar-grid {{
                gap: 4px;
            }}

            .calendar-day {{
                min-height: 80px;
                padding: 0.5rem;
            }}

            .calendar-event {{
                font-size: 0.65rem;
                padding: 0.3rem 0.4rem;
            }}

            .concert-card {{
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }}

            .concert-artist {{
                font-size: 1.5rem;
            }}

            .ticket-link {{
                align-self: flex-start;
            }}

            .filter-buttons {{
                gap: 0.5rem;
            }}

            .city-filter {{
                font-size: 0.85rem;
                padding: 0.5rem 1rem;
            }}
        }}
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="nav">
        <div class="nav-buttons">
            <button class="nav-button active" data-view="venue">By Venue</button>
            <button class="nav-button" data-view="calendar">Calendar</button>
            <button class="nav-button" data-view="list">List</button>
        </div>
    </nav>

    <!-- Hero Section -->
    <div class="hero">
        <h1 class="hero-title">Concert Finder</h1>
        <p class="hero-subtitle">Summer 2026 — Billy & Gretchen's Vacation Shows</p>
        <div class="stats-bar">
            <div><span class="stat">{total_shows}</span> <span class="stat-label">shows</span></div>
            <div><span class="stat">{city_count}</span> <span class="stat-label">cities</span></div>
            <div><span class="stat">{discovery_count}</span> <span class="stat-label">discoveries</span></div>
        </div>
    </div>

    <div class="container">
        <!-- By Venue View (Default) -->
        <div class="view active" id="venue-view">
            {venue_view_html}
        </div>

        <!-- Calendar View -->
        <div class="view" id="calendar-view">
            {calendar_view_html}
        </div>

        <!-- List View -->
        <div class="view" id="list-view">
            <div class="tabs">
                <button class="tab-button active" data-tab="summer">Your Summer</button>
                <button class="tab-button" data-tab="outside">Worth the Trip</button>
            </div>

            <div class="tab-content active" id="summer">
                <div class="filters">
                    <div class="filter-buttons">
                        <button class="city-filter active" data-city="all">All Cities</button>
                        {city_buttons}
                    </div>
                </div>

                <div class="concerts">
                    {summer_html}
                </div>
            </div>

            <div class="tab-content" id="outside">
                <div class="concerts">
                    {outside_html}
                </div>
            </div>
        </div>
    </div>

    <!-- Event Popup -->
    <div class="popup-overlay"></div>
    <div class="event-popup">
        <button class="popup-close">×</button>
        <div class="popup-artist"></div>
        <div class="popup-details"></div>
        <div class="popup-badge"></div>
        <a href="#" class="popup-ticket-btn" target="_blank">Get Tickets →</a>
    </div>

    <script>
        // Navigation
        const navButtons = document.querySelectorAll('.nav-button');
        const views = document.querySelectorAll('.view');

        navButtons.forEach(button => {{
            button.addEventListener('click', () => {{
                const viewId = button.dataset.view + '-view';

                navButtons.forEach(btn => btn.classList.remove('active'));
                views.forEach(view => view.classList.remove('active'));

                button.classList.add('active');
                document.getElementById(viewId).classList.add('active');
            }});
        }});

        // Venue card expansion
        document.querySelectorAll('.venue-card').forEach(card => {{
            card.addEventListener('click', (e) => {{
                if (e.target.tagName === 'A') return; // Don't toggle if clicking link

                const concerts = card.querySelector('.venue-concerts');
                const isExpanded = !concerts.classList.contains('hidden');

                // Collapse all
                document.querySelectorAll('.venue-concerts').forEach(c => c.classList.add('hidden'));
                document.querySelectorAll('.venue-card').forEach(c => c.classList.remove('expanded'));

                // Expand clicked
                if (!isExpanded) {{
                    concerts.classList.remove('hidden');
                    card.classList.add('expanded');
                }}
            }});
        }});

        // Calendar event popup
        const popup = document.querySelector('.event-popup');
        const overlay = document.querySelector('.popup-overlay');
        const closeBtn = document.querySelector('.popup-close');

        document.querySelectorAll('.calendar-event').forEach(event => {{
            event.addEventListener('click', () => {{
                const artist = event.dataset.artist;
                const venue = event.dataset.venue;
                const city = event.dataset.city;
                const date = event.dataset.date;
                const badge = event.dataset.badge;
                const badgeClass = event.dataset.badgeClass;
                const tickets = event.dataset.tickets;

                popup.querySelector('.popup-artist').textContent = artist;
                popup.querySelector('.popup-details').innerHTML = `
                    <div>${{date}}</div>
                    <div>${{venue}}</div>
                    <div>${{city}}</div>
                `;
                popup.querySelector('.popup-badge').innerHTML = `<span class="badge ${{badgeClass}}">${{badge}}</span>`;
                popup.querySelector('.popup-ticket-btn').href = tickets;

                popup.classList.add('active');
                overlay.classList.add('active');
            }});
        }});

        function closePopup() {{
            popup.classList.remove('active');
            overlay.classList.remove('active');
        }}

        closeBtn.addEventListener('click', closePopup);
        overlay.addEventListener('click', closePopup);

        // List view tabs
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {{
            button.addEventListener('click', () => {{
                const tabId = button.dataset.tab;

                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));

                button.classList.add('active');
                document.getElementById(tabId).classList.add('active');
            }});
        }});

        // City filtering
        const cityFilters = document.querySelectorAll('.city-filter');
        const concertCards = document.querySelectorAll('#summer .concert-card');
        const monthDividers = document.querySelectorAll('#summer .month-divider');

        cityFilters.forEach(filter => {{
            filter.addEventListener('click', () => {{
                const selectedCity = filter.dataset.city;

                cityFilters.forEach(f => f.classList.remove('active'));
                filter.classList.add('active');

                if (selectedCity === 'all') {{
                    concertCards.forEach(card => card.classList.remove('hidden'));
                    monthDividers.forEach(divider => divider.classList.remove('hidden'));
                }} else {{
                    concertCards.forEach(card => {{
                        if (card.dataset.city === selectedCity) {{
                            card.classList.remove('hidden');
                        }} else {{
                            card.classList.add('hidden');
                        }}
                    }});

                    monthDividers.forEach(divider => {{
                        const month = divider.dataset.month;
                        const visibleInMonth = Array.from(concertCards).some(
                            card => card.dataset.month === month && !card.classList.contains('hidden')
                        );
                        if (visibleInMonth) {{
                            divider.classList.remove('hidden');
                        }} else {{
                            divider.classList.add('hidden');
                        }}
                    }});
                }}
            }});
        }});

        // Stagger animation delays for list view
        document.querySelectorAll('.concert-card').forEach((card, index) => {{
            card.style.animationDelay = `${{index * 0.05}}s`;
        }});
    </script>
</body>
</html>'''

    return html


def main():
    print("🎵 Generating Concert Finder website...")

    # Parse results
    concerts = parse_results_file('results.txt')

    if not concerts:
        print("❌ No concerts found in results.txt")
        return

    print(f"✓ Parsed {len(concerts)} concerts")

    # Generate HTML
    html = generate_html(concerts)

    # Write to file
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✓ Generated index.html")
    print("\n🎉 Done! Open index.html in your browser to view the site.")
    print("\n📍 Features:")
    print("   - By Venue view (default): Click destination cards to see all shows")
    print("   - Calendar view: Visual monthly calendar with colored event pills")
    print("   - List view: Chronological list with city filters")


if __name__ == '__main__':
    main()
