import os
import random
import httpx
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & DARK THEME SETUP
# ==========================================
st.set_page_config(
    page_title="Global Movie Agent",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e0e10; }
    .movie-card {
        background-color: #18181c;
        border: 1px solid #2d2d35;
        border-radius: 12px;
        padding: 16px;
        height: 100%;
    }
    .critic-verdict {
        background-color: #2c1517;
        border-left: 3px solid #e50914;
        padding: 8px 12px;
        border-radius: 4px;
        margin-top: 10px;
        font-style: italic;
        color: #ffb3b3;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE & LOGGING
# ==========================================
def init_db():
    conn = sqlite3.connect("global_movie_agent.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            language TEXT,
            genre TEXT,
            min_rating REAL,
            release_year INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_search(lang, genre, rating, year):
    conn = sqlite3.connect("global_movie_agent.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO search_logs (timestamp, language, genre, min_rating, release_year) VALUES (?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), lang, str(genre), rating, year)
    )
    conn.commit()
    conn.close()

init_db()

# ==========================================
# API CONFIGURATION & MAPPINGS
# ==========================================
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BASE_URL = "https://api.themoviedb.org/3"

# Comprehensive Global Language Mapping
LANGUAGES = {
    "All Languages (Global)": "",
    "Hindi (हिंदी)": "hi",
    "Korean (한국어)": "ko",
    "Japanese (日本語)": "ja",
    "Tamil (தமிழ்)": "ta",
    "Telugu (తెలుగు)": "te",
    "Malayalam (മലയാളം)": "ml",
    "Spanish (Español)": "es",
    "French (Français)": "fr",
    "German (Deutsch)": "de",
    "Italian (Italiano)": "it",
    "Mandarin (中文)": "zh",
    "English": "en"
}

GENRES = {
    "All Genres": None,
    "Action": 28,
    "Adventure": 12,
    "Animation": 16,
    "Comedy": 35,
    "Crime": 80,
    "Documentary": 99,
    "Drama": 18,
    "Family": 10751,
    "Fantasy": 14,
    "History": 36,
    "Horror": 27,
    "Mystery": 9648,
    "Romance": 10749,
    "Sci-Fi": 878,
    "Thriller": 53
}

# Persona Takes
PERSONA_TAKES = {
    "Cynical Critic": [
        "A rare moment where cinema actually got something right.",
        "Aggressively mid. Ideal background noise while you check your phone.",
        "A complete trainwreck. Watching paint dry has tighter pacing.",
        "Critics praised it, which means you'll pretend to get the symbolism."
    ],
    "Film Historian": [
        "A monumental landmark for global world cinema aesthetics.",
        "Demonstrates masterclass direction and brilliant narrative pacing.",
        "A quiet, underrated gem that deserves far more global recognition.",
        "Offers a fascinating lens into the culture and era of its production."
    ]
}

def fetch_global_movies(lang_code, genre_id, min_rating, year, min_votes):
    if not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": False,
        "vote_count.gte": min_votes,
        "vote_average.gte": min_rating,
        "page": 1
    }

    if lang_code:
        params["with_original_language"] = lang_code
    if genre_id:
        params["with_genres"] = genre_id
    if year:
        params["primary_release_year"] = year

    try:
        r = httpx.get(f"{BASE_URL}/discover/movie", params=params, timeout=8.0)
        if r.status_code == 200:
            movies = r.json().get("results", [])[:12]
            processed = []
            for m in movies:
                processed.append({
                    "title": m.get("title"),
                    "original_title": m.get("original_title"),
                    "rating": m.get("vote_average", 0.0),
                    "vote_count": m.get("vote_count", 0),
                    "release_date": m.get("release_date", "N/A")[:4],
                    "overview": m.get("overview", "No synopsis available."),
                    "poster_path": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
                    "lang": m.get("original_language", "").upper()
                })
            return processed
    except Exception as e:
        st.error(f"Network error: {e}")
    return []

# ==========================================
# USER INTERFACE
# ==========================================
st.title("🌐 Global Movie Intelligence Agent")
st.caption("Discover cinema from around the globe with live ratings, original titles, and personalized commentary.")

with st.sidebar:
    st.header("🔍 Global Search Filters")
    
    selected_persona = st.selectbox("Agent Persona", ["Cynical Critic", "Film Historian"])
    selected_lang_label = st.selectbox("Original Language", list(LANGUAGES.keys()))
    selected_genre_label = st.selectbox("Genre", list(GENRES.keys()))
    
    min_rating = st.slider("Minimum Rating (TMDB)", 0.0, 9.5, 6.0, 0.5)
    min_votes = st.select_slider("Minimum Votes (Filtering noise)", options=[10, 50, 100, 500, 1000], value=100)
    release_year = st.number_input("Release Year (Optional)", min_value=1940, max_value=2026, value=None)
    
    search_btn = st.button("Find Movies 🍿", type="primary", use_container_width=True)

if search_btn:
    lang_code = LANGUAGES[selected_lang_label]
    genre_id = GENRES[selected_genre_label]
    log_search(selected_lang_label, selected_genre_label, min_rating, release_year)
    
    with st.spinner("Fetching live global movie records..."):
        movies = fetch_global_movies(lang_code, genre_id, min_rating, release_year, min_votes)
        
    if not TMDB_API_KEY:
        st.error("🔑 **TMDb API Key Missing!** Please add your `TMDB_API_KEY` in Streamlit Cloud Secrets (Advanced Settings) to fetch live data.")
    elif movies:
        st.success(f"Fetched {len(movies)} top matching titles from global databases.")
        
        cols = st.columns(3)
        for i, movie in enumerate(movies):
            with cols[i % 3]:
                if movie["poster_path"]:
                    st.image(movie["poster_path"], use_container_width=True)
                
                st.subheader(movie["title"])
                if movie["original_title"] != movie["title"]:
                    st.caption(f"Original Title: *{movie['original_title']}*")
                
                st.write(f"⭐ **{movie['rating']:.1f}/10** ({movie['vote_count']} votes) | 📅 {movie['release_date']} | 🗣️ {movie['lang']}")
                st.write(movie["overview"][:140] + "..." if len(movie["overview"]) > 140 else movie["overview"])
                
                verdict = random.choice(PERSONA_TAKES[selected_persona])
                st.markdown(f'<div class="critic-verdict"><b>[{selected_persona}]:</b> "{verdict}"</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.warning("No movies matched these strict filters. Try lowering the minimum rating or minimum vote threshold.")
