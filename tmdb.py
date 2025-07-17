# tmdb.py
"""
TMDb API integration helper module.
Provides search, details lookup, and episode listing functions.
"""
import requests
import os
from dotenv import load_dotenv

# Load API key from environment
load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
# Base URLs for API endpoints and images
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

def search_title(query):
    """
    Search TMDb for movies or TV shows matching the query string.
    Returns a list of dicts: id, media_type, name, poster_url, year.
    """
    params = {
        "api_key": API_KEY,
        "query": query
    }

    response = requests.get(f"{BASE_URL}/search/multi", params=params)

    results = []

    if response.status_code == 200:
        for item in response.json().get("results", []):
            # Skip types other than movie or TV
            if item["media_type"] not in ["movie", "tv"]:
                continue
            results.append({
                "id": item["id"],
                "media_type": item["media_type"],
                "name": item.get("title") or item.get("name"),
                "poster_url": f"{IMAGE_BASE_URL}{item.get('poster_path')}" if item.get("poster_path") else "/static/images/placeholder.png",
                # Extract year from release_date or first_air_date
                "year": (
                    item.get("release_date") or item.get("first_air_date") or "N/A"
                )[:4]
            })

    return results

def get_title_details(tmdb_id, media_type):
    """
    Fetch detailed information for a single title by TMDb ID and type.
    Returns a dict with fields: id, name, description, year, duration,
    genre, type (movie/show), poster_url, backdrop_url, media_type.
    """
    url = f"{BASE_URL}/{media_type}/{tmdb_id}"
    params = {
        "api_key": API_KEY,
        "language": "en-US"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()

    # Build readable details object
    return {
        "id": tmdb_id,
        "name": data.get("title") or data.get("name"),
        "description": data.get("overview"),
        "year": (data.get("release_date") or data.get("first_air_date") or "")[:4],
        "duration": data.get("runtime") or (f"{len(data.get('seasons', []))} seasons" if media_type == "tv" else "N/A"),
        "genre": ", ".join([genre["name"] for genre in data.get("genres", [])]),
        "type": "movie" if media_type == "movie" else "show",
        "poster_url": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else "/static/images/placeholder.png",
        "backdrop_url": f"https://image.tmdb.org/t/p/original{data.get('backdrop_path')}" if data.get("backdrop_path") else None,
        "media_type": media_type
    }

def get_episodes_for_tv_show(tmdb_id):
    """
    Retrieve the list of all episodes for a given TV show by TMDb ID.
    Returns a list of dicts: season, episode, name.
    """
    # First fetch show details to know total seasons
    details_url = f"{BASE_URL}/tv/{tmdb_id}"
    params = {"api_key": API_KEY, "language": "en-US"}
    details_response = requests.get(details_url, params=params)

    if details_response.status_code != 200:
        return []

    data = details_response.json()
    total_seasons = data.get("number_of_seasons", 1)
    all_episodes = []

    # Iterate through each season to fetch episodes
    for season_number in range(1, total_seasons + 1):
        season_url = f"{BASE_URL}/tv/{tmdb_id}/season/{season_number}"
        season_response = requests.get(season_url, params=params)

        if season_response.status_code != 200:
            continue

        season_data = season_response.json()
        for ep in season_data.get("episodes", []):
            all_episodes.append({
                "season": season_number,
                "episode": ep["episode_number"],
                "name": ep["name"]
            })

    return all_episodes
