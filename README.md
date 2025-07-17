[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.39.5-blue.svg)](https://www.sqlite.org/)
[![Flask](https://img.shields.io/pypi/v/Flask.svg)](https://pypi.org/project/Flask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen.svg)](https://cs50x-final-project-q1yh.onrender.com/)

# 2WATCH

#### Video Demo:  <URL HERE>
#### Description: A social Flask app for film & TV lovers: explore upcoming releases, random scenes, build watchlists, tier‑rank titles, craft Top 10 lists and share profiles — powered by the TMDb & YouTube Data APIs.



## 📋 Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [Tech Stack](#tech-stack)  
4. [Project Structure](#project-structure)  
5. [Installation](#installation)  
6. [Configuration](#configuration)  
7. [Database Setup](#database-setup)
8. [Flask Environment](#flask-environment)
9. [Running the App](#running-the-app)  
10. [Usage](#usage)  
11. [License & Acknowledgments](#license--acknowledgments)  



## 🌟 Overview

**2WATCH** is a social Flask web app for movie & TV enthusiasts that lets you:

- **Explore** popular, now‑playing, and upcoming titles — filter by genres to find your next watch  
- **Inspire** yourself with random movie & TV scenes straight from YouTube  
- **Track** what you’re currently watching  
- **Manage** a personal watchlist 
- **Rank** movies & shows with an intuitive drag‑and‑drop tier list  
- **Craft** and reorder your Top 10 Movies & Shows using autocomplete search  
- **Share** profiles with friends — compare each other’s ranks, watchlists, watching status, and Top 10s  
- **Customize** your profile settings and avatar for a personal touch  



## 🚀 Features

- **User Authentication**: Sign up, log in, log out using `flask-login`  
- **TMDb Integration**: Search for movies & TV shows, fetch details, display posters  
- **YouTube Integration**: Random video picker from a curated playlist  
- **Tier List**: Drag‑and‑drop classification (SortableJS)  
- **Top 10**: Autocomplete search, add/remove, reorder via drag‑and‑drop  
- **Watchlist**: Mark items as Watched or Not Interested  
- **Responsive Design**: Responsive design (mobile + desktop) via CSS Grid & Flexbox
- **Flash Messages**: User feedback for success & error events  



## 🛠 Tech Stack

- **Backend**: Python 3, Flask, SQLite  
- **APIs**: The Movie Database (TMDb), YouTube Data API v3  
- **Frontend**: HTML5, CSS3, JavaScript (ES6)  
- **Drag & Drop**: [SortableJS](https://github.com/SortableJS/Sortable)  
- **Environment Variables**: `python-dotenv`  
- **Dependencies**: Listed in `requirements.txt`



## 📂 Project Structure
```bash
2watch/
├── app.py # Main Flask application
├── tmdb.py # TMDb API helper functions
├── init_db.py # Database initialization script
├── db.py # SQLite connection helper
├── .env # Environment variables
├── .gitignore
├── .env.example # Example environment variables
├── requirements.txt # Python dependencies
└── schema.sql # SQL schema definitions
├── static/ # Static assets (CSS, JS, images)
│   ├── css/
│   │   ├── finder.css
│   │   ├── home.css
│   │   ├── layout.css
│   │   ├── menu_mobile.css
│   │   ├── profile.css
│   │   ├── rank.css
│   │   ├── search_results.css
│   │   ├── settings.css
│   │   ├── styles.css
│   │   ├── title_detail.css
│   │   ├── top10.css
│   │   └── watchlist.css
│   ├── images/
│   │   ├── avatars/
│   │   │   ├── avatar_default.png
│   │   │   └── ...
│   │   ├── placeholder.png
│   │   └── search-icon.png
│   ├── js/
│   │   └── home.js
├── templates/ # Jinja2 templates
│   ├── finder.html
│   ├── home.html
│   ├── layout.html
│   ├── login.html
│   ├── menu_mobile.html
│   ├── profile.html
│   ├── rank.html
│   ├── register.html
│   ├── search_results.html
│   ├── settings.html
│   ├── title_detail.html
│   ├── top10.html
│   └── watchlist.html
```



## 🔧 Installation
1. **Clone** and activate a virtual environment
   ```bash
   git clone https://github.com/YOUR-USERNAME/2watch.git
   cd 2watch
   ```

2. **Create** & activate a virtual environment
    ```bash
    python3 -m venv venv
    source venv/bin/activate    # macOS/Linux
    venv\Scripts\activate       # Windows
    ```

3. **Install** dependencies
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration
1. **Copy** the example env file
   ```bash
   cp .env.example .env
   ```

2. **Edit** `.env` and set your API keys:
   ```bash
    TMDB_API_KEY=your_tmdb_api_key
    YOUTUBE_API_KEY=your_youtube_api_key
    SECRET_KEY=a_random_secret_key
   ```

## 🗄️ Database Setup
### Initialize the SQLite database with the schema:
   ```bash
    python init_db.py
   ```
This creates database.db according to schema.sql.

## ⚙️ Flask Environment
### Before you start the server, tell Flask which file is your application and enable development mode:
   ```
   # macOS / Linux
   export FLASK_APP=app.py
   export FLASK_ENV=development  # optional: enables debug mode

   # Windows CMD
   set FLASK_APP=app.py
   set FLASK_ENV=development

   # Windows PowerShell
   $env:FLASK_APP = "app.py"
   $env:FLASK_ENV = "development"
   ```

## ▶️ Running the App
### With your virtual environment activated:
   ```bash
    flask run
   ```
Then open your browser to http://127.0.0.1:5000/

## 📖 Usage

### 1. Sign Up & Sign In
- Go to **Register** to create a new account and pick your avatar  
- Or **Log In** with your existing credentials  

### 2. Discover & Browse
- **Home**  
  - **Discover**: Browse upcoming, popular & now‑playing titles—filter by genre to narrow down  
  - **Watching**: Keep track of what you’re currently watching
  - **Watchlist**: View titles you’ve saved to watch later

- **Search**  
  - Type any movie/TV title to see results  
  - Click a card for full details 

### 3. Rank & Curate
- **Rank**  
  - Drag & drop posters into tier categories (e.g. “GREAT,” “BAD,” etc.)  
  - Changes save instantly to your profile 

- **Top 10**  
  - Start typing in the search bar to autocomplete titles  
  - Click to add them to your Top 10 Movies or Shows  
  - Drag cards to reorder—your #1, #2, #3… picks are updated live  
  - Hit **Save** to commit the list to your profile

### 4. Get Inspired
- **Finder**  
  - Watch a random movie/show scene to help you decide what to watch next
  - Click **Get another one** for a random movie/TV scene embedded via YouTube  
  - Perfect when you need fresh watch ideas!

### 5. Customize & Share
- **Profile**  
  - View your overall stats, full tier lists, “Watching” queue, watchlist and Top 10 side by side  
  - Copy your profile URL to share with friends and compare rankings  

- **Settings**  
  - Change your **Username**, **Password**, or **Avatar**  
  - Or **Delete Account** if you ever need to start fresh  

Enjoy exploring, ranking, and sharing your movie & TV passions with 2WATCH!  

## 📝 License & Acknowledgments
- **MIT License** — see `LICENSE`

- Built with data from **TMDb** and **YouTube**

- Inspired by CS50x course and modern streaming platforms
