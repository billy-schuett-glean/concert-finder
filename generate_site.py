#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a beautiful static HTML site from results.txt
"""

from datetime import datetime
from collections import defaultdict
import re


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

    # Group by month
    def group_by_month(concert_list):
        grouped = defaultdict(list)
        for concert in concert_list:
            grouped[concert['month_year']].append(concert)
        return grouped

    summer_by_month = group_by_month(summer_concerts)
    outside_by_month = group_by_month(outside_concerts)

    # Generate concert cards HTML
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

    # Generate city filter buttons
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
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}

        /* Hero Section */
        .hero {{
            text-align: center;
            padding: 6rem 2rem 4rem;
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

        /* Filter Section */
        .filters {{
            padding: 3rem 0 2rem;
            text-align: center;
        }}

        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            justify-content: center;
            margin-top: 1.5rem;
        }}

        .city-filter, .tab-button {{
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

        .city-filter:hover, .tab-button:hover {{
            background: rgba(255,255,255,0.08);
            border-color: rgba(201, 149, 107, 0.3);
            color: #c9956b;
        }}

        .city-filter.active, .tab-button.active {{
            background: rgba(201, 149, 107, 0.15);
            border-color: #c9956b;
            color: #c9956b;
        }}

        /* Tabs */
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
        }}

        .tab-button.active {{
            border-bottom-color: #c9956b;
            background: transparent;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        /* Month Dividers */
        .month-divider {{
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            font-style: italic;
            color: #c9956b;
            margin: 3rem 0 1.5rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(201, 149, 107, 0.3);
        }}

        /* Concert Cards */
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

        /* Hidden state for filtering */
        .concert-card.hidden {{
            display: none;
        }}

        .month-divider.hidden {{
            display: none;
        }}

        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: #666;
            font-size: 1.1rem;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero {{
                padding: 4rem 1.5rem 3rem;
            }}

            .hero-title {{
                font-size: 3rem;
            }}

            .stats-bar {{
                flex-direction: column;
                gap: 0.75rem;
                padding: 1.5rem 2rem;
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
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab-button active" data-tab="summer">Your Summer</button>
            <button class="tab-button" data-tab="outside">Worth the Trip</button>
        </div>

        <!-- Summer Tab -->
        <div class="tab-content active" id="summer">
            <!-- Filters -->
            <div class="filters">
                <div class="filter-buttons">
                    <button class="city-filter active" data-city="all">All Cities</button>
                    {city_buttons}
                </div>
            </div>

            <!-- Concert List -->
            <div class="concerts">
                {summer_html}
            </div>
        </div>

        <!-- Outside Tab -->
        <div class="tab-content" id="outside">
            <!-- Concert List -->
            <div class="concerts">
                {outside_html}
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {{
            button.addEventListener('click', () => {{
                const tabId = button.dataset.tab;

                // Update active states
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

                // Update active filter
                cityFilters.forEach(f => f.classList.remove('active'));
                filter.classList.add('active');

                // Filter concerts
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

                    // Hide month dividers if no concerts in that month
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

        // Stagger animation delays
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


if __name__ == '__main__':
    main()
