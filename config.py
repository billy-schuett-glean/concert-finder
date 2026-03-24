from dotenv import load_dotenv
import os

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'https://127.0.0.1:8888/callback'
TICKETMASTER_API_KEY = os.getenv('TICKETMASTER_API_KEY')
BANDSINTOWN_APP_ID = os.getenv('BANDSINTOWN_APP_ID')
SEATGEEK_CLIENT_ID = os.getenv('SEATGEEK_CLIENT_ID')
SEATGEEK_SECRET = os.getenv('SEATGEEK_SECRET')

DESTINATIONS = [
    {
        'name': 'Red Rocks / Morrison, CO',
        'city': 'Morrison',
        'state': 'CO',
        'country': 'US',
        'search_terms': ['Morrison, CO', 'Denver, CO', 'Golden, CO'],
        'venue_name': 'Red Rocks Amphitheatre'
    },
    {
        'name': "Thompson's Point / Portland, ME",
        'city': 'Portland',
        'state': 'ME',
        'country': 'US',
        'search_terms': ['Portland, ME'],
        'venue_name': "Thompson's Point"
    },
    {
        'name': 'Greek Theatre / Berkeley, CA',
        'city': 'Berkeley',
        'state': 'CA',
        'country': 'US',
        'search_terms': ['Berkeley, CA', 'San Francisco, CA', 'Oakland, CA'],
        'venue_name': 'Greek Theatre'
    },
    {'name': 'Savannah, GA', 'city': 'Savannah', 'state': 'GA', 'country': 'US', 'search_terms': ['Savannah, GA']},
    {'name': 'Charleston, SC', 'city': 'Charleston', 'state': 'SC', 'country': 'US', 'search_terms': ['Charleston, SC']},
    {'name': 'Nashville, TN', 'city': 'Nashville', 'state': 'TN', 'country': 'US', 'search_terms': ['Nashville, TN']},
    {'name': 'Austin, TX', 'city': 'Austin', 'state': 'TX', 'country': 'US', 'search_terms': ['Austin, TX']},
    {'name': 'Asheville, NC', 'city': 'Asheville', 'state': 'NC', 'country': 'US', 'search_terms': ['Asheville, NC']},
    {'name': 'Montreal, QC, Canada', 'city': 'Montreal', 'state': 'QC', 'country': 'CA', 'search_terms': ['Montreal, QC', 'Montréal, QC']},
    {'name': 'Vancouver, BC, Canada', 'city': 'Vancouver', 'state': 'BC', 'country': 'CA', 'search_terms': ['Vancouver, BC']},
]

PRIMARY_DATE_WINDOW = ('2026-05-25', '2026-08-25')
SECONDARY_DATE_WINDOW = ('2026-09-01', '2026-12-31')