# 🎵 Concert Finder

A premium web application that discovers concerts in your favorite vacation destinations by analyzing your Spotify listening history and searching SeatGeek for upcoming shows.

## ✨ Features

- **Spotify Integration**: Analyzes your top artists across short, medium, and long-term listening periods
- **Smart Discovery**: Suggests concerts by similar artists based on curated recommendations and genre matching
- **Multi-City Search**: Searches for concerts in your planned vacation destinations
- **Beautiful UI**: Premium editorial design with warm amber/gold accents inspired by music magazines
- **Date Filtering**: Separates shows in your travel window from other dates worth knowing about
- **Exact Matching**: Verifies artist names against SeatGeek's performer data to avoid false positives
- **Smart Filtering**: Removes parking passes, VIP packages, and non-concert events

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Spotify Developer Account
- SeatGeek API Access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/billy-schuett-glean/concert-finder.git
cd concert-finder
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SEATGEEK_CLIENT_ID=your_seatgeek_client_id
```

### Running the Web App

```bash
streamlit run web_app.py
```

The app will open in your browser at `http://localhost:8501`

### Running the CLI

```bash
python main.py
```

## 🎨 Design

The web interface features a premium editorial aesthetic with:
- **Typography**: Instrument Serif for headings, DM Sans for body text
- **Color Palette**: Warm amber/gold accents on near-black background
- **Layout**: Large destination cards with city-specific gradient accents
- **Interaction**: Smooth animations and hover effects

## 📍 Destinations

Currently configured to search in:
- Red Rocks / Morrison, CO
- Thompson's Point / Portland, ME
- Greek Theatre / Berkeley, CA
- Savannah, GA
- Charleston, SC
- Nashville, TN
- Austin, TX
- Asheville, NC
- Montreal, QC, Canada
- Vancouver, BC, Canada

Edit `config.py` to customize your destinations.

## 🔧 Configuration

### Date Windows

Edit `PRIMARY_DATE_WINDOW` and `SECONDARY_DATE_WINDOW` in `config.py`:

```python
PRIMARY_DATE_WINDOW = ('2026-05-25', '2026-08-25')
SECONDARY_DATE_WINDOW = ('2026-09-01', '2026-12-31')
```

### Destinations

Add or modify destinations in `config.py`:

```python
DESTINATIONS = [
    {
        'name': 'Your City',
        'city': 'City Name',
        'state': 'ST',
        'country': 'US',
        'search_terms': ['City Name, ST'],
        'venue_name': 'Optional Specific Venue'
    },
    # ...
]
```

## 📦 Project Structure

```
concert-finder/
├── web_app.py              # Streamlit web interface
├── main.py                 # CLI interface
├── spotify_client.py       # Spotify API integration
├── seatgeek_client.py      # SeatGeek API integration
├── matcher.py              # Event matching logic
├── config.py               # Configuration and destinations
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
└── .env                    # Environment variables (not in git)
```

## 🎯 How It Works

1. **Fetch Your Artists**: Pulls your top Spotify artists across multiple time ranges
2. **Build Discovery List**: Uses curated similar-artist mappings and genre-based recommendations as fallback (since Spotify's related-artists endpoint returns 403)
3. **Search SeatGeek**: Queries SeatGeek for concerts by both your artists and discovery artists in your vacation cities
4. **Exact Matching**: Verifies artist names appear in SeatGeek's structured performer data to avoid false positives
5. **Filter & Deduplicate**: Removes non-concert events (parking, VIP packages) and duplicate listings
6. **Present Results**: Groups concerts by destination and date window with beautiful UI

## 🛠️ Technologies

- **Streamlit**: Web framework
- **Spotipy**: Spotify API wrapper
- **Requests**: HTTP client for SeatGeek API
- **Python-dotenv**: Environment variable management
- **Colorama & Tabulate**: CLI formatting

## 📝 License

MIT

## 🙏 Acknowledgments

Built for finding the perfect concerts during summer vacation trips.
