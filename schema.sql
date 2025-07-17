DROP TABLE IF EXISTS user_ratings;
DROP TABLE IF EXISTS user_episodes_watched;
DROP TABLE IF EXISTS users;

CREATE TABLE user_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tmdb_id INTEGER,
    media_type TEXT CHECK(media_type IN ('movie', 'show')),
    rank TEXT CHECK(rank IN (
        'ABSOLUTE CINEMA',
        'GREAT',
        'GOOD',
        'COULD BE BETTER',
        'BAD',
        'WATCHED',
        'WATCHING',
        'WATCHLIST',
        'DIDN''T WATCH',
        'NOT INTERESTED'
    )),
    watched_episodes TEXT DEFAULT '',
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visible_in_rank BOOLEAN DEFAULT 1,
    top10_position INTEGER DEFAULT NULL
);

CREATE UNIQUE INDEX idx_user_title ON user_ratings(user_id, tmdb_id);

CREATE TABLE user_episodes_watched (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tmdb_id INTEGER,
    season INTEGER,
    episode INTEGER,
    watched INTEGER DEFAULT 0,
    UNIQUE(user_id, tmdb_id, season, episode)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    avatar TEXT DEFAULT 'avatar_default.png'
);
