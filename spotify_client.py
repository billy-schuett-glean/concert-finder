import logging
from collections import defaultdict
from urllib.parse import urlparse

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI

logger = logging.getLogger(__name__)
SCOPES = "user-top-read playlist-read-private playlist-read-collaborative"


class SpotifyRelatedArtistsForbidden(RuntimeError):
    pass

CURATED_SIMILAR_ARTISTS = {
    'Bon Iver': ['Big Red Machine', 'S. Carey', 'Volcano Choir', 'Novo Amor', 'Daughter'],
    'The National': ['El Vy', 'The War on Drugs', 'Gang of Youths', 'Interpol', 'Frightened Rabbit'],
    'Phoebe Bridgers': ['boygenius', 'Lucy Dacus', 'Julien Baker', 'Soccer Mommy', 'Snail Mail'],
    'Fleet Foxes': ['Father John Misty', 'Midlake', 'Lord Huron', 'Band of Horses', 'The Head and the Heart'],
    'Mt. Joy': ['Caamp', 'The Revivalists', 'Rainbow Kitten Surprise', 'Flipturn', 'The Backseat Lovers'],
    'Noah Kahan': ['Hozier', 'Gregory Alan Isakov', 'Mt. Joy', 'The Lumineers', 'Josiah and the Bonnevilles'],
    'The War on Drugs': ['Kurt Vile', 'Future Islands', 'The National', 'Gang of Youths', 'Spoon'],
    'Kacey Musgraves': ['Maren Morris', 'Brandi Carlile', 'Maggie Rogers', 'Ruston Kelly', 'The Chicks'],
    'Khruangbin': ['Parcels', 'Men I Trust', 'Unknown Mortal Orchestra', 'Jungle', 'Skinshape'],
    'Maggie Rogers': ['HAIM', 'Japanese House', 'Gracie Abrams', 'Lola Young', 'MUNA'],
}

GENRE_FALLBACKS = {
    'indie folk': ['Gregory Alan Isakov', 'Hollow Coves', 'José González', 'The Paper Kites', 'Leif Vollebekk'],
    'stomp and holler': ['Caamp', 'The Head and the Heart', 'Lord Huron', 'Watchhouse', 'Typhoon'],
    'folk-pop': ['Maggie Rogers', 'Angie McMahon', 'Lola Young', 'Wilderado', 'Hazlett'],
    'indie rock': ['Sam Fender', 'Hippo Campus', 'The Backseat Lovers', 'Palace', 'Spacey Jane'],
    'chamber pop': ['Weyes Blood', 'Perfume Genius', 'Japanese Breakfast', 'Aldous Harding', 'Grizzly Bear'],
    'modern rock': ['Manchester Orchestra', 'Silversun Pickups', 'Spoon', 'Metric', 'Future Islands'],
    'indie soul': ['Michael Kiwanuka', 'Leon Bridges', 'Durand Jones & The Indications', 'Aaron Frazer', 'Cautious Clay'],
    'neo-psychedelic': ['Crumb', 'Mild High Club', 'Sugar Candy Mountain', 'Temples', 'Babe Rainbow'],
    'alt-country': ['Jason Isbell and the 400 Unit', 'Waxahatchee', 'Wednesday', 'MJ Lenderman', 'Hiss Golden Messenger'],
    'singer-songwriter': ['Searows', 'Tom Odell', 'Ben Howard', 'Matilda Mann', 'Katherine Priddy'],
}


def get_spotify_client(cache_path='.cache'):
    """Authenticate with Spotify and return a spotipy client."""
    try:
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SCOPES,
            cache_path=cache_path,
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return sp
    except Exception as e:
        logger.error('Spotify auth failed: %s', e)
        raise


def _normalize_artist_item(item):
    return {
        'artist_name': item.get('name'),
        'spotify_id': item.get('id'),
        'genres': item.get('genres', []),
        'popularity': item.get('popularity', 0),
    }


def _aggregate_artists(artist_records):
    merged = {}
    for artist in artist_records:
        artist_id = artist.get('spotify_id')
        if not artist_id:
            continue
        if artist_id not in merged:
            merged[artist_id] = {
                **artist,
                'ranges': set([artist.get('range')]) if artist.get('range') else set(),
            }
        else:
            entry = merged[artist_id]
            if artist.get('range') and artist['range'] not in entry['ranges']:
                entry['ranges'].add(artist['range'])
            entry['genres'] = list({*entry.get('genres', []), *artist.get('genres', [])})
            entry['popularity'] = max(entry.get('popularity', 0), artist.get('popularity', 0))

    for e in merged.values():
        e['range_count'] = len(e.get('ranges', []))
    return sorted(merged.values(), key=lambda x: (-x.get('range_count', 0), -x.get('popularity', 0), x.get('artist_name', '')))


def get_my_top_artists(limit=30):
    """Get top artists across short_term, medium_term, and long_term."""
    try:
        sp = get_spotify_client()
        all_artists = []
        for time_range in ['short_term', 'medium_term', 'long_term']:
            items = sp.current_user_top_artists(limit=limit, time_range=time_range).get('items', [])
            for item in items:
                artist_data = _normalize_artist_item(item)
                artist_data['range'] = time_range
                all_artists.append(artist_data)

        deduped = _aggregate_artists(all_artists)
        for artist in deduped:
            artist.pop('ranges', None)
        return deduped
    except Exception as e:
        logger.error('Error fetching top artists: %s', e)
        return []


def _extract_playlist_id(playlist_url):
    if 'playlist' in playlist_url:
        if playlist_url.startswith('http://') or playlist_url.startswith('https://'):
            parsed = urlparse(playlist_url)
            parts = parsed.path.strip('/').split('/')
            if 'playlist' in parts:
                idx = parts.index('playlist')
                if idx + 1 < len(parts):
                    return parts[idx + 1]

        if playlist_url.startswith('spotify:playlist:'):
            return playlist_url.split(':')[-1]
    return None


def get_playlist_artists(playlist_url):
    """Get unique artists from a playlist URL."""
    try:
        sp = get_spotify_client()
        playlist_id = _extract_playlist_id(playlist_url)
        if not playlist_id:
            logger.error('Invalid playlist URL: %s', playlist_url)
            return []

        artists_map = {}
        offset = 0

        while True:
            response = sp.playlist_items(playlist_id, limit=100, offset=offset)
            items = response.get('items', [])
            for item in items:
                track = item.get('track') or {}
                for artist in track.get('artists', []):
                    artist_id = artist.get('id')
                    if not artist_id or artist_id in artists_map:
                        continue
                    try:
                        artist_full = sp.artist(artist_id)
                        artists_map[artist_id] = _normalize_artist_item(artist_full)
                    except Exception as e:
                        logger.warning('Failed to fetch artist %s: %s', artist_id, e)
            if not response.get('next'):
                break
            offset += len(items)

        return sorted(artists_map.values(), key=lambda x: (-x.get('popularity', 0), x.get('artist_name', '')))
    except Exception as e:
        logger.error('Error fetching playlist artists: %s', e)
        return []


def get_similar_artists(spotify_id, limit=5):
    """Get related artists for a given Spotify artist ID."""
    try:
        sp = get_spotify_client()
        response = sp.artist_related_artists(spotify_id)
        if not response:
            logger.warning('Empty response for related artists: %s', spotify_id)
            return []
        artists = response.get('artists', [])[:limit]
        result = [_normalize_artist_item(a) for a in artists]
        logger.debug('Got %d similar artists for %s', len(result), spotify_id)
        return result
    except Exception as e:
        status_code = getattr(e, 'http_status', None)
        if status_code == 403:
            raise SpotifyRelatedArtistsForbidden('Spotify related artists endpoint returned 403 Forbidden') from e
        logger.warning('Could not fetch related artists for %s: %s (type: %s)', spotify_id, e, type(e).__name__)
        return []


def _normalize_text(value):
    return ' '.join((value or '').strip().lower().split())


def _build_discovery_from_fallbacks(my_artists, similar_limit=5):
    discovery_map = {}
    owned_names = {_normalize_text(artist.get('artist_name')) for artist in my_artists if artist.get('artist_name')}
    genre_counts = defaultdict(int)

    for artist in my_artists:
        artist_name = artist.get('artist_name')
        if not artist_name:
            continue

        for similar_name in CURATED_SIMILAR_ARTISTS.get(artist_name, [])[:similar_limit]:
            normalized = _normalize_text(similar_name)
            if not normalized or normalized in owned_names:
                continue
            entry = discovery_map.setdefault(
                normalized,
                {
                    'artist_name': similar_name,
                    'spotify_id': None,
                    'genres': [],
                    'popularity': 0,
                    'similar_to': set(),
                    'discovery_source': 'curated',
                },
            )
            entry['similar_to'].add(artist_name)

        for genre in artist.get('genres', []):
            normalized_genre = _normalize_text(genre)
            if normalized_genre:
                genre_counts[normalized_genre] += 1

    for genre, _count in sorted(genre_counts.items(), key=lambda item: (-item[1], item[0])):
        for similar_name in GENRE_FALLBACKS.get(genre, [])[:similar_limit]:
            normalized = _normalize_text(similar_name)
            if not normalized or normalized in owned_names:
                continue
            entry = discovery_map.setdefault(
                normalized,
                {
                    'artist_name': similar_name,
                    'spotify_id': None,
                    'genres': [genre],
                    'popularity': 0,
                    'similar_to': set(),
                    'discovery_source': 'genre_fallback',
                },
            )
            if genre not in entry['genres']:
                entry['genres'].append(genre)

    discovery_artists = []
    for artist in discovery_map.values():
        discovery_artists.append(
            {
                **{k: v for k, v in artist.items() if k != 'similar_to'},
                'similar_to': sorted(artist.get('similar_to', [])),
            }
        )

    discovery_artists.sort(key=lambda artist: (artist.get('discovery_source', ''), artist.get('artist_name', '')))
    return discovery_artists


def build_full_artist_list(include_similar=True, similar_limit=5):
    """Build full artist list including similar artists for discovery.
    
    Args:
        include_similar: If True, fetch related artists for each of your top artists
        similar_limit: Number of similar artists to fetch per artist
    
    Returns:
        Tuple of (my_artists, discovery_artists)
    """
    my_artists = get_my_top_artists()
    discovery_map = {}

    if include_similar:
        print('Fetching similar artists for discovery (this may take a moment)...')
        for i, base in enumerate(my_artists, 1):
            base_id = base.get('spotify_id')
            if not base_id:
                continue
            try:
                similar = get_similar_artists(base_id, limit=similar_limit)
            except SpotifyRelatedArtistsForbidden:
                print('  Spotify related artists unavailable; using curated discovery fallbacks.')
                discovery_artists = _build_discovery_from_fallbacks(my_artists, similar_limit=similar_limit)
                my_artists_formatted = [dict(a, source='yours') for a in my_artists]
                discovery_formatted = [dict(a, source='discovery') for a in discovery_artists]
                return my_artists_formatted, discovery_formatted
            if similar:
                print(f'  {base.get("artist_name")}: found {len(similar)} similar artists')
            for artist in similar:
                aid = artist.get('spotify_id')
                if not aid or aid == base_id:
                    continue
                if aid not in discovery_map:
                    discovery_map[aid] = {
                        **artist,
                        'similar_to': set([base.get('artist_name')]),
                    }
                else:
                    discovery_map[aid]['similar_to'].add(base.get('artist_name'))
        if not discovery_map:
            print('  No related artists returned; using curated discovery fallbacks.')
            discovery_artists = _build_discovery_from_fallbacks(my_artists, similar_limit=similar_limit)
            my_artists_formatted = [dict(a, source='yours') for a in my_artists]
            discovery_formatted = [dict(a, source='discovery') for a in discovery_artists]
            return my_artists_formatted, discovery_formatted

    discovery_artists = []
    for artist in discovery_map.values():
        discovery_artists.append({
            **{k: v for k, v in artist.items() if k != 'similar_to'},
            'similar_to': list(artist.get('similar_to', [])),
        })

    my_artists_formatted = [dict(a, source='yours') for a in my_artists]
    discovery_formatted = [dict(a, source='discovery') for a in discovery_artists]

    return my_artists_formatted, discovery_formatted


if __name__ == '__main__':
    print('spotify_client.py loaded')
