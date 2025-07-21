"""
Main application module for 2WATCH Flask app.

This module defines the Flask app, configures login/session management,
sets up database connections, and registers all routes for:
- Home page and API endpoints (search, popular, now_playing, discover, genres, upcoming)
- User authentication (register, login, logout)
- Watchlist and ranking features
- Profile and title details pages
- Helper functions for TMDb API integration
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, g, flash
import requests # HTTP requests to external APIs (TMDb, YouTube)
import sqlite3  # SQLite database connection
import os       # Operating system utilities (paths, env)
import random   # Random choice for YouTube videos
from tmdb import search_title, get_title_details, get_episodes_for_tv_show
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from dotenv import load_dotenv # Load environment variables from .env

# Load environment variables (TMDB and YouTube API keys)
load_dotenv()

app = Flask(__name__)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Secret key for session signing
app.secret_key = os.getenv("SECRET_KEY")

# API Keys
API_KEY = os.getenv("TMDB_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# YouTube Channel IDs for video fetching
CHANNEL_IDS = [
    "UCzuqhhs6NWbgTzMuM09WKDQ",  # MOVIECLIPS
    "UC5nG0U7W_4XEBrr2PzZRYWg"   # BoxofficeMoviesScenes
]

# SQLite database file path
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")

# User model and loader
class User(UserMixin):
    """
    Simple User class for Flask-Login.
    Holds id, username, and avatar filename.
    """
    def __init__(self, id, username, avatar):
        self.id = id
        self.username = username
        self.avatar = avatar

@login_manager.user_loader
def load_user(user_id):
    """
    Given a user ID, fetch user record from the database
    and return a User object or None if not found.
    """
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if user:
        return User(id=user["id"], username=user["username"], avatar=user["avatar"])
    return None

# Database connection handling
def get_db():
    """
    Returns a SQLite connection stored in flask.g for reuse.
    Ensures row_factory is sqlite3.Row for named columns.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """
    Closes the database connection at the end of request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

# Home
@app.route("/")
def index():
    """
    Render the home page template.
    Contains main UI with carousels for popular, now playing, etc.
    """
    return render_template("home.html")

# API endpoint: Fetch titles for a given user and status
@app.route("/api/user_titles")
@login_required
def get_user_titles():
    """
    Return a JSON list of titles filtered by user-specific status.
    Query param 'status' must be one of: WATCHED, WATCHLIST, NOT_INTERESTED.
    """
    status = request.args.get("status", "").upper()
    if not status:
        return jsonify([])

    db = get_db()
    rows = db.execute("""
        SELECT tmdb_id, media_type
        FROM user_ratings
        WHERE user_id = ? AND rank = ?
    """, (current_user.id, status)).fetchall()

    results = []
    # For each rating record, fetch fresh details from TMDb
    for row in rows:
        tmdb_id = row["tmdb_id"]
        media_type = row["media_type"]

        tmdb_url = f"https://api.themoviedb.org/3/{'tv' if media_type == 'show' else 'movie'}/{tmdb_id}"
        params = { "api_key": API_KEY, "language": "en-US" }
        response = requests.get(tmdb_url, params=params)

        if response.status_code == 200:
            data = response.json()
            # Build a consistent result object
            results.append({
                "tmdb_id": tmdb_id,
                "media_type": media_type,
                "name": data.get("title") or data.get("name"),
                "poster_url": f"https://image.tmdb.org/t/p/w200{data['poster_path']}" if data.get("poster_path") else "/static/images/placeholder.png"
            })

    return jsonify(results)

# Home - Popular Now Row (API Endpoint: TMDb Data)
@app.route("/api/tmdb/popular")
def get_popular_movies():
    """
    Return JSON of popular movies from TMDb, page 1.
    If user is logged in, include their saved status per title.
    """
    try:
        url = "https://api.themoviedb.org/3/movie/popular"
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": 1
        }

        response = requests.get(url, params=params)
        data = response.json()

        results = []
        user_status_map = {}

        # Map user's existing ranks if any
        if current_user.is_authenticated:
            db = get_db()
            user_id = current_user.id

            query = db.execute("""
                SELECT tmdb_id, media_type, rank
                FROM user_ratings
                WHERE user_id = ?
            """, (user_id,)).fetchall()

            for row in query:
                key = f"{row['media_type']}_{row['tmdb_id']}"
                user_status_map[key] = row["rank"]

        # Build response list
        for item in data.get("results", []):
            tmdb_id = item["id"]
            media_type = "movie"
            key = f"{media_type}_{tmdb_id}"
            user_rank = user_status_map.get(key)

            results.append({
                "tmdb_id": tmdb_id,
                "name": item.get("title"),
                "media_type": media_type,
                "poster_url": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "/static/images/placeholder.png",
                "user_status": user_rank
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Home - Now Playing in Theaters Row (API Endpoint: TMDb Data)
@app.route("/api/tmdb/now_playing")
def get_now_playing_movies():
    """
    Return JSON of now-playing movies in US region.
    Similar to popular, includes user status if logged in.
    """
    try:
        url = "https://api.themoviedb.org/3/movie/now_playing"
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": 1,
            "region": "US"
        }

        response = requests.get(url, params=params)
        data = response.json()

        # ... identical logic as get_popular_movies ...
        # Return JSON list

        results = []
        user_status_map = {}

        if current_user.is_authenticated:
            db = get_db()
            user_id = current_user.id

            query = db.execute("""
                SELECT tmdb_id, media_type, rank
                FROM user_ratings
                WHERE user_id = ?
            """, (user_id,)).fetchall()

            for row in query:
                key = f"{row['media_type']}_{row['tmdb_id']}"
                user_status_map[key] = row["rank"]

        for item in data.get("results", []):
            tmdb_id = item["id"]
            media_type = "movie"
            key = f"{media_type}_{tmdb_id}"
            user_rank = user_status_map.get(key)

            results.append({
                "tmdb_id": tmdb_id,
                "name": item.get("title"),
                "media_type": media_type,
                "poster_url": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "/static/images/placeholder.png",
                "user_status": user_rank
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Home - Discover Titles Row (API Endpoint: TMDb Data)
@app.route("/api/tmdb/discover")
def discover_titles():
    """
    Return JSON of discovered movies or TV based on genre filters.
    Query params: with_genres, media_type.
    """
    try:
        genres = request.args.get("with_genres", "")
        media_type = request.args.get("media_type", "movie")

        url = f"https://api.themoviedb.org/3/discover/{media_type}"
        params = {
            "api_key": API_KEY,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "with_genres": genres,
            "page": 1
        }

        response = requests.get(url, params=params)
        data = response.json()

        results = []
        user_status_map = {}

        if current_user.is_authenticated:
            db = get_db()
            user_id = current_user.id

            query = db.execute("""
                SELECT tmdb_id, media_type, rank
                FROM user_ratings
                WHERE user_id = ?
            """, (user_id,)).fetchall()

            for row in query:
                key = f"{row['media_type']}_{row['tmdb_id']}"
                user_status_map[key] = row["rank"]

        for item in data.get("results", []):
            tmdb_id = item["id"]
            title = item.get("title") or item.get("name")
            key = f"{media_type}_{tmdb_id}"
            user_rank = user_status_map.get(key)

            results.append({
                "tmdb_id": tmdb_id,
                "name": title,
                "media_type": media_type,
                "poster_url": f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get("poster_path") else "/static/images/placeholder.png",
                "user_status": user_rank
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Home - API for genres filter list (API Endpoint: TMDb Data)
@app.route("/api/genres")
def get_genres():
    """
    Return JSON of all TMDb genres for movie and TV.
    Used to populate filter checkboxes.
    """
    try:
        genres = {}
        for media_type in ["movie", "tv"]:
            url = f"https://api.themoviedb.org/3/genre/{media_type}/list"
            params = {
                "api_key": API_KEY,
                "language": "en-US"
            }
            response = requests.get(url, params=params)
            data = response.json()
            genres[media_type] = data.get("genres", [])

        return jsonify(genres)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Home - Upcoming Titles Carousel (API Endpoint: TMDb Data)
@app.route("/api/tmdb/upcoming")
def tmdb_upcoming():
    """
    Return JSON of upcoming movies and on-the-air TV (first 6 each).
    Used to build the homepage carousel.
    """
    try:
        combined_results = []

        # --- MOVIES ---
        movie_url = "https://api.themoviedb.org/3/movie/upcoming"
        movie_params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": 1,
            "region": "US"
        }
        movie_response = requests.get(movie_url, params=movie_params)
        movie_data = movie_response.json().get("results", [])[:8]

        for movie in movie_data:
            combined_results.append({
                "tmdb_id": movie.get("id"),
                "name": movie.get("title"),
                "media_type": "movie",
                "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
                "backdrop_url": f"https://image.tmdb.org/t/p/original{movie.get('backdrop_path')}" if movie.get("backdrop_path") else None,
                "year": movie.get("release_date", "")[:4]
            })

        # --- TV SHOWS ---
        tv_url = "https://api.themoviedb.org/3/tv/on_the_air"
        tv_params = {
            "api_key": API_KEY,
            "language": "en-US",
            "page": 1
        }
        tv_response = requests.get(tv_url, params=tv_params)
        tv_data = tv_response.json().get("results", [])[:8]

        for show in tv_data:
            combined_results.append({
                "tmdb_id": show.get("id"),
                "name": show.get("name"),
                "media_type": "tv",
                "poster_url": f"https://image.tmdb.org/t/p/w500{show.get('poster_path')}" if show.get("poster_path") else None,
                "backdrop_url": f"https://image.tmdb.org/t/p/original{show.get('backdrop_path')}" if show.get("backdrop_path") else None,
                "year": show.get("first_air_date", "")[:4]
            })

        return jsonify(combined_results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    db = get_db()

    avatar_folder = os.path.join(app.static_folder, "images", "avatars")
    avatars = sorted([f for f in os.listdir(avatar_folder)])

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        avatar = request.form.get("avatar") or "avatar_default.png"

        if not username or not password or not confirmation:
            flash("Please fill out all fields.", "error")
            return redirect("/register")

        if password != confirmation:
            flash("Passwords do not match.", "error")
            return redirect("/register")

        # Password hashing
        hashed = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)",
                (username, hashed, avatar)
            )
            db.commit()
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
            return redirect("/register")

        flash("Account created successfully!", "success")
        return redirect("/login")

    return render_template("register.html", avatars=avatars)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user is None or not check_password_hash(user["password"], password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        login_user(User(user["id"], user["username"], user["avatar"]), remember=True)
        flash("Login successful!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

# Helper function
def get_genre_ids(selected_names):
    """
    Convert list of genre names to TMDb genre IDs using a cached lookup.
    """
    global _genre_cache
    if _genre_cache is None:
        _genre_cache = {}
        for media in ("movie", "tv"):
            url = f"https://api.themoviedb.org/3/genre/{media}/list"
            resp = requests.get(url, params={
                "api_key": API_KEY,
                "language": "en-US"
            })
            for g in resp.json().get("genres", []):
                _genre_cache[g["name"]] = g["id"]

    return [_genre_cache[name] for name in selected_names if name in _genre_cache]

# Menu Mobile
@app.route("/menu-mobile")
def menu_mobile():
    return render_template("menu_mobile.html")

# Settings Page
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    db = get_db()
    user_id = current_user.id

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # Change Username
        if form_type == "change_username":
            new_username = request.form.get("new_username")
            if not new_username:
                flash("Username cannot be empty.", "error")
            else:
                try:
                    db.execute("UPDATE users SET username = ? WHERE id = ?", (new_username, user_id))
                    db.commit()
                    current_user.username = new_username
                    flash("Username updated successfully.", "success")
                except sqlite3.IntegrityError:
                    flash("Username already exists.", "error")

        # Change Password
        elif form_type == "change_password":
            current = request.form.get("current_password")
            new = request.form.get("new_password")
            confirm = request.form.get("confirm_password")

            row = db.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()
            if not check_password_hash(row["password"], current):
                flash("Current password is incorrect.", "error")
            elif new != confirm:
                flash("New passwords do not match.", "error")
            else:
                db.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(new), user_id))
                db.commit()
                flash("Password updated successfully.", "success")

        # Change Avatar
        elif form_type == "change_avatar":
            new_avatar = request.form.get("avatar")
            if new_avatar:
                db.execute("UPDATE users SET avatar = ? WHERE id = ?", (new_avatar, user_id))
                db.commit()
                current_user.avatar = new_avatar
                flash("Avatar updated!", "success")

        # Delete Account
        elif form_type == "delete_account":
            db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            db.commit()
            session.clear()
            flash("Your account has been deleted.", "success")
            return redirect("/register")

    # Load avatar options
    avatar_path = os.path.join("static", "images", "avatars")
    avatars = [f for f in os.listdir(avatar_path) if f.endswith(".png") or f.endswith(".jpg")]
    avatars.sort()

    return render_template("settings.html", avatars=avatars)

# Rank Feature
@app.route("/rank")
@login_required
def rank_page():
    """
    Get user's rankings and render the rank page.
    """
    db = get_db()
    user_id = current_user.id

    tiers = [
        "ABSOLUTE CINEMA", "GREAT", "GOOD", "COULD BE BETTER", "BAD",
        "WATCHED", "WATCHING", "WATCHLIST"
    ]

    user_ratings = db.execute("""
        SELECT tmdb_id, rank, media_type
        FROM user_ratings
        WHERE user_id = ? AND visible_in_rank = 1
    """, (user_id,)).fetchall()

    tier_data = {tier: [] for tier in tiers}

    for rating in user_ratings:
        tmdb_id = rating["tmdb_id"]
        rank = rating["rank"]
        media_type = rating["media_type"]

        if media_type == "show":
            media_type = "tv"

        if rank not in tiers:
            continue

        details = get_title_details(tmdb_id, media_type)
        if details:
            tier_data[rank].append(details)

    return render_template("rank.html", tier_data=tier_data)

# Rank Feature - Update Rankings
@app.route("/rank/update", methods=["POST"])
@login_required
def rank_update():
    """
    Handle asynchronous updates when a card is dropped
    into a new tier via SortableJS.
    """
    db = get_db()
    user_id = current_user.id
    title_id = request.form.get("title_id")
    new_rank = request.form.get("new_rank")
    media_type = request.form.get("media_type")
    if media_type:
        media_type = media_type.strip().lower()
        if media_type == "tv":
            media_type = "show"

    if title_id and new_rank and media_type:
        db.execute("""
            INSERT INTO user_ratings (user_id, tmdb_id, rank, media_type, visible_in_rank)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id, tmdb_id)
            DO UPDATE SET rank = excluded.rank, media_type = excluded.media_type, visible_in_rank = 1
        """, (user_id, title_id, new_rank, media_type))
        db.commit()
        return jsonify({"status": "success"})
    
    return jsonify({"status": "error", "message": "Missing data"}), 400

# Rank Feature - Clear Rankings
@app.route("/rank/clear", methods=["POST"])
@login_required
def rank_clear():
    """
    Set all user ratings to not visible in rank.
    """
    db = get_db()
    user_id = current_user.id

    db.execute("""
        UPDATE user_ratings
        SET visible_in_rank = 0
        WHERE user_id = ? AND rank NOT IN ('WATCHED', 'WATCHING', 'WATCHLIST')
    """, (user_id,))
    db.commit()

    return jsonify({"status": "cleared"})

# Watchlist Feature
@app.route("/watchlist")
@login_required
def watchlist():
    """
    Display all titles in the current user's watchlist.
    Fetch details for each via get_title_details().
    """
    db = get_db()
    user_id = current_user.id

    rows = db.execute("""
        SELECT tmdb_id, media_type FROM user_ratings
        WHERE user_id = ? AND rank = 'WATCHLIST'
    """, (user_id,)).fetchall()

    titles = []
    for row in rows:
        tmdb_id = row["tmdb_id"]
        media_type = row["media_type"]
        details = get_title_details(tmdb_id, "tv" if media_type == "show" else "movie")
        if details:
            titles.append(details)

    return render_template("watchlist.html", titles=titles)

# Watchlist Feature - Update Watchlist
@app.route("/watchlist/update", methods=["POST"])
@login_required
def update_watchlist():
    """
    Update a single title from WATCHLIST to WATCHED or NOT_INTERESTED.
    """
    db = get_db()
    user_id = current_user.id
    tmdb_id = request.form.get("tmdb_id")
    new_rank = request.form.get("rank")

    if tmdb_id and new_rank in ["WATCHED", "NOT_INTERESTED"]:
        db.execute("""
            UPDATE user_ratings
            SET rank = ?
            WHERE user_id = ? AND tmdb_id = ?
        """, (new_rank, user_id, tmdb_id))
        db.commit()
    
    return redirect(url_for("watchlist"))

# Search Function
@app.route("/search")
def search():
    """
    Show search results for query 'q' using TMDb search_title().
    Annotate each result with current user's rank if logged in.
    """

    query = request.args.get("q", "")
    results = search_title(query) if query else []

    # Attach user-specific rank to each result
    if current_user.is_authenticated:
        db = get_db()
        user_id = current_user.id
        for title in results:
            media_type = title["media_type"]
            tmdb_id = title["id"]
            row = db.execute("""
                SELECT rank FROM user_ratings
                WHERE user_id = ? AND tmdb_id = ? AND media_type = ?
            """, (user_id, tmdb_id, "show" if media_type == "tv" else media_type)).fetchone()
            title["user_rank"] = row["rank"] if row else None
    else:
        for title in results:
            title["user_rank"] = None

    return render_template("search_results.html", query=query, results=results)

# Helper function
def fetch_tmdb_details(tmdb_id, media_type):
    """
    Fetch basic details like name and poster_url from TMDb for one title.
    Used in multiple places (watchlist, profile, etc.).
    """
    try:
        url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}"
        params = {"api_key": API_KEY, "language": "en-US"}
        res = requests.get(url, params=params)
        data = res.json()
        return {
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "name": data.get("title") or data.get("name") or "Untitled",
            "poster_url": f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}" if data.get("poster_path") else None
        }
    except:
        return {
            "tmdb_id": tmdb_id,
            "media_type": media_type,
            "name": "Unknown",
            "poster_url": None
        }

# User Profile
@app.route("/profile")
@login_required
def own_profile():
    """
    Redirect to the public profile page of current user.
    """
    return redirect(url_for("profile", username=current_user.username))

# Profile by username
@app.route("/profile/<username>")
def profile(username):
    """
    Display user profile with stats, recent ranks,
    top10 movies/shows.
    """
    db = get_db()
    user = db.execute("SELECT id, username, avatar FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        return render_template("404.html"), 404

    user_id = user["id"]

    # Stats
    stats = {
        "watched": db.execute("""
            SELECT COUNT(*) FROM user_ratings
            WHERE user_id = ? AND rank IN (
                'WATCHED', 'WATCHING', 'ABSOLUTE CINEMA', 'GREAT', 'GOOD', 'COULD BE BETTER', 'BAD'
            )
        """, (user_id,)).fetchone()[0],
        "watchlist": db.execute("""
            SELECT COUNT(*) FROM user_ratings WHERE user_id = ? AND rank = 'WATCHLIST'
        """, (user_id,)).fetchone()[0],
        "ranks": {}
    }

    ranks = ["ABSOLUTE CINEMA", "GREAT", "GOOD", "COULD BE BETTER", "BAD", "WATCHING", "WATCHLIST"]
    for rank in ranks:
        stats["ranks"][rank] = db.execute("""
            SELECT COUNT(*) FROM user_ratings
            WHERE user_id = ? AND rank = ?
        """, (user_id, rank)).fetchone()[0]

    # Full Rank
    user_ranks = {}
    for rank in ranks:
        rows = db.execute("""
            SELECT tmdb_id, media_type
            FROM user_ratings
            WHERE user_id = ? AND rank = ?
            ORDER BY created DESC
        """, (user_id, rank)).fetchall()

        user_ranks[rank] = [
            fetch_tmdb_details(row["tmdb_id"], "tv" if row["media_type"] == "show" else row["media_type"])
            for row in rows
        ]

    # Top 10 Movies
    top10_movies_rows = db.execute("""
        SELECT tmdb_id, media_type
        FROM user_ratings
        WHERE user_id = ? AND top10_position IS NOT NULL AND media_type = 'movie'
        ORDER BY top10_position
    """, (user_id,)).fetchall()

    top10_movies = [
        fetch_tmdb_details(row["tmdb_id"], row["media_type"])
        for row in top10_movies_rows
    ]

    # Top 10 Shows
    top10_shows_rows = db.execute("""
        SELECT tmdb_id, media_type
        FROM user_ratings
        WHERE user_id = ? AND top10_position IS NOT NULL AND media_type = 'show'
        ORDER BY top10_position
    """, (user_id,)).fetchall()

    top10_shows = [
        fetch_tmdb_details(row["tmdb_id"], "tv")
        for row in top10_shows_rows
    ]

    return render_template("profile.html",
                           user=user,
                           stats=stats,
                           user_ranks=user_ranks,
                           top10_movies=top10_movies,
                           top10_shows=top10_shows)

# Redirect user to login if not authenticated
@login_manager.unauthorized_handler
def unauthorized():
    flash("Please log in to access this page.", "error")
    return redirect(url_for('login'))

# Title Details
@app.route("/title/<int:title_id>")
@login_required
def title_detail(title_id):
    """
    Show detailed page for a title (movie or TV show),
    including episodes list and watched toggles.
    """
    db = get_db()
    user_id = current_user.id

    media_type = request.args.get("media_type", "movie")
    details = get_title_details(title_id, media_type)

    if not details:
        return "Title not found", 404

    # Get episodes if it's a TV show
    episodes = []
    if details["type"] == "show":
        episodes = get_episodes_for_tv_show(title_id)

    # Get user rank for this title
    user_rank = db.execute("""
        SELECT rank FROM user_ratings
        WHERE user_id = ? AND tmdb_id = ?
    """, (user_id, title_id)).fetchone()

    # Get watched episodes
    watched_rows = db.execute("""
        SELECT season, episode FROM user_episodes_watched
        WHERE user_id = ? AND tmdb_id = ?
    """, (user_id, title_id)).fetchall()

    watched_set = {(row["season"], row["episode"]) for row in watched_rows}

    return render_template(
        "title_detail.html",
        title=details,
        episodes=episodes,
        user_rank=user_rank["rank"] if user_rank else None,
        watched_set=watched_set
    )

# Title Detail - Quick Rank
@app.route("/rank/quick", methods=["POST"])
@login_required
def rank_title_quick():
    """
    Rank a title from the title detail page using buttons.
    """
    db = get_db()
    title_id = request.form.get("title_id")
    rank = request.form.get("rank")
    media_type = request.form.get("media_type")
    if media_type == "tv":
        media_type = "show"


    if title_id and rank and media_type:
        db.execute("""
            INSERT INTO user_ratings (user_id, tmdb_id, rank, media_type, visible_in_rank)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id, tmdb_id)
            DO UPDATE SET rank = excluded.rank, media_type = excluded.media_type, visible_in_rank = 1
        """, (current_user.id, title_id, rank, media_type))
        db.commit()

    return "", 204

# Title Detail - Toggle Episode Watched
@app.route("/toggle_episode", methods=["POST"])
@login_required
def toggle_episode():
    """
    Change the watched status of a specific episode for the current user.
    """
    db = get_db()
    tmdb_id = request.form.get("tmdb_id")
    season = request.form.get("season")
    episode = request.form.get("episode")
    user_id = current_user.id

    # Check if already exists
    existing = db.execute("""
        SELECT watched FROM user_episodes_watched
        WHERE user_id = ? AND tmdb_id = ? AND season = ? AND episode = ?
    """, (user_id, tmdb_id, season, episode)).fetchone()

    if existing:
        # Change the value
        new_value = 0 if existing["watched"] else 1
        db.execute("""
            UPDATE user_episodes_watched
            SET watched = ?
            WHERE user_id = ? AND tmdb_id = ? AND season = ? AND episode = ?
        """, (new_value, user_id, tmdb_id, season, episode))
    else:
        db.execute("""
            INSERT INTO user_episodes_watched (user_id, tmdb_id, season, episode, watched)
            VALUES (?, ?, ?, ?, 1)
        """, (user_id, tmdb_id, season, episode))

    db.commit()
    return redirect(request.referrer or "/")

# Watchlist Ranking Feature
@app.route("/title/<int:title_id>/rank", methods=["POST"])
@login_required
def rank_title_realtime(title_id):
    """
    Change title rank from Watchlist Page.
    """
    db = get_db()
    rank = request.form.get("rank")
    user_id = current_user.id

    if not rank:
        return jsonify({"status": "error", "message": "No rank provided"}), 400

    existing = db.execute("""
        SELECT * FROM user_ratings
        WHERE user_id = ? AND tmdb_id = ?
    """, (user_id, title_id)).fetchone()

    if existing:
        db.execute("""
            UPDATE user_ratings
            SET rank = ?
            WHERE user_id = ? AND tmdb_id = ?
        """, (rank, user_id, title_id))
    else:
        db.execute("""
            INSERT INTO user_ratings (user_id, tmdb_id, rank)
            VALUES (?, ?, ?)
        """, (user_id, title_id, rank))

    db.commit()
    return jsonify({"status": "success"})

# Top 10 Feature
@app.route("/top10")
@login_required
def top10_page():
    """
    Render the Top 10 selection page with draggable lists.
    """
    db = get_db()
    user_id = current_user.id

    # Filmes
    movies_rows = db.execute("""
        SELECT tmdb_id FROM user_ratings
        WHERE user_id = ? AND media_type = 'movie' AND top10_position IS NOT NULL
        ORDER BY top10_position
    """, (user_id,)).fetchall()

    # Séries
    shows_rows = db.execute("""
        SELECT tmdb_id FROM user_ratings
        WHERE user_id = ? AND media_type = 'show' AND top10_position IS NOT NULL
        ORDER BY top10_position
    """, (user_id,)).fetchall()

    def search_title_by_id(tmdb_id, media_type):
        url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key=86babcc2b25137bd5e895bb023520c67&language=en"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    # Busca detalhes completos de cada título via função search_title_by_id
    movies = [search_title_by_id(row["tmdb_id"], "movie") for row in movies_rows]
    shows = [search_title_by_id(row["tmdb_id"], "tv") for row in shows_rows]

    # Monta lista para renderização com nome e poster
    def format_title(t, media_type):
        return {
            "id": t["id"],
            "name": t.get("title") or t.get("name"),
            "poster_url": f"https://image.tmdb.org/t/p/w200{t.get('poster_path')}" if t.get("poster_path") else "/static/images/placeholder.png"
        }

    movies = [format_title(m, "movie") for m in movies if m]
    shows = [format_title(s, "tv") for s in shows if s]

    return render_template("top10.html", movies=movies, shows=shows)

# Top 10 Feature - Save Rankings
@app.route("/top10/save", methods=["POST"])
@login_required
def save_top10():
    """
    Save the ordering of Top 10 movies and shows
    for the current user.
    """
    db = get_db()
    user_id = current_user.id
    data = request.get_json()

    # Reset top10_position for this user
    db.execute("""
        UPDATE user_ratings
        SET top10_position = NULL
        WHERE user_id = ?
    """, (user_id,))

    for index, tmdb_id in enumerate(data.get("movies", [])):
        db.execute("""
            INSERT INTO user_ratings (user_id, tmdb_id, rank, media_type, top10_position)
            VALUES (?, ?, NULL, ?, ?)
            ON CONFLICT(user_id, tmdb_id)
            DO UPDATE SET top10_position = excluded.top10_position
        """, (user_id, tmdb_id, "movie", index + 1))

    for index, tmdb_id in enumerate(data.get("shows", [])):
        db.execute("""
            INSERT INTO user_ratings (user_id, tmdb_id, rank, media_type, top10_position)
            VALUES (?, ?, NULL, ?, ?)
            ON CONFLICT(user_id, tmdb_id)
            DO UPDATE SET top10_position = excluded.top10_position
        """, (user_id, tmdb_id, "show", index + 1))

    db.commit()
    return jsonify({"status": "saved"})

@app.route("/api/search")
@login_required
def api_search():
    """
    Search bar on Top 10 Page.
    """
    query = request.args.get("q", "")
    results = search_title(query) if query else []

    # Convert "tv" media type to "show"
    for item in results:
        if item["media_type"] == "tv":
            item["media_type"] = "show"

    return jsonify(results)

# Finder Feature - Load and display a random video from the YouTube playlist
@app.route("/api/random_video")
def random_video():
    """
    Return JSON of a random video from predefined YouTube playlist.
    """
    try:
        PLAYLIST_ID = "PL86SiVwkw_oeDQoAZwcuyoyG43eKWtbJM"
        API_KEY = os.getenv("YOUTUBE_API_KEY")

        if not API_KEY:
            return jsonify({"error": "Missing API key"}), 500

        all_videos = []
        next_page_token = None

        while True:
            params = {
                "part": "snippet",
                "playlistId": PLAYLIST_ID,
                "maxResults": 50,
                "key": API_KEY
            }
            if next_page_token:
                params["pageToken"] = next_page_token

            response = requests.get("https://www.googleapis.com/youtube/v3/playlistItems", params=params)
            data = response.json()

            items = data.get("items", [])
            all_videos.extend(items)

            next_page_token = data.get("nextPageToken")
            if not next_page_token or len(all_videos) >= 200:
                break  # Limit to 200 videos

        if not all_videos:
            return jsonify({"error": "No videos found"}), 404

        # Pick a random video from the list
        video = random.choice(all_videos)
        snippet = video["snippet"]
        video_id = snippet["resourceId"]["videoId"]
        title = snippet.get("title", "Untitled")
        description = snippet.get("description", "")

        return jsonify({
            "videoId": video_id,
            "title": title,
            "description": description
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Finder Feature
@app.route("/finder")
def finder_page():
    """
    Render the finder page for random video lookup.
    """
    return render_template("finder.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
