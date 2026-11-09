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
    page_title="The Cynical Critic",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for dark theme movie cards
st.markdown("""
<style>
    .main { background-color: #0e0e10; }
    .stAppHeader { background-color: transparent; }
    .movie-card {
        background-color: #18181c;
        border: 1px solid #2d2d35;
        border-radius: 12px;
        padding: 16px;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .critic-verdict {
        background-color: #2c1517;
        border-left: 3px solid #ff4d4d;
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
# DATABASE & BACKEND LOGIC
# ==========================================
def init_db():
    conn = sqlite3.connect("critic_agent.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            genre TEXT,
            min_rating REAL,
            release_year INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_query(genre, min_rating, year):
    conn = sqlite3.connect("critic_agent.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (timestamp, genre, min_rating, release_year) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), str(genre), min_rating, year)
    )
    conn.commit()
    conn.close()

init_db()

# TMDB & Persona Settings
TMDB_API_KEY = st.secrets.get("TMDB_API_KEY", "")
BASE_URL = "https://api.themoviedb.org/3"

CYNICAL_TAKES_HIGH = [
    "Fine, humanity actually got one right. It's tolerable.",
    "Surprisingly decent. Lower your expectations slightly less for this one.",
    "A rare moment where Hollywood didn't completely waste millions of dollars.",
    "Critics loved it, which means you'll pretend to understand the subtext."
]

CYNICAL_TAKES_MID = [
    "A perfectly average way to waste two hours of your fleeting existence.",
    "Aggressively mid. Ideal background noise while you scroll on your phone.",
    "Not awful enough to laugh at, not good enough to remember tomorrow.",
    "It exists. That's about the highest compliment I can muster."
]

CYNICAL_TAKES_LOW = [
    "A cinematic trainwreck. Watching paint dry has a tighter plot.",
    "If you willingly select this, I question all your life decisions.",
    "Proof that anyone with a camera and a budget can get greenlit.",
    "I've seen infomercials with better acting and deeper character arcs."
]

GENRES = {
    "Any Trash": None,
    "Action": 28,
    "Comedy": 35,
    "Drama": 18,
    "Sci-Fi": 878,
    "Horror": 27,
    "Animation": 16
}

def fetch_filtered_movies(genre_id, min_rating, year):
    if not TMDB_API_KEY:
        # Fallback Mock Movies if API Key is not configured
        return [
            {
                "title": "Inception",
                "rating": 8.4,
                "release_date": "2010",
                "overview": "A thief steals corporate secrets through dream-sharing technology.",
                "poster_path": "https://image.tmdb.org/t/p/w500/oYuLEW9SpatialHQXYIiNV9dMRhW.jpg",
                "critic_verdict": random.choice(CYNICAL_TAKES_HIGH)
            },
            {
                "title": "The Dark Knight",
                "rating": 8.5,
                "release_date": "2008",
                "overview": "Batman faces off against the chaotic Joker in Gotham City.",
                "poster_path": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
                "critic_verdict": random.choice(CYNICAL_TAKES_HIGH)
            }
        ]

    params = {
        "api_key": TMDB_API_KEY,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": False,
        "vote_count.gte": 100,
        "vote_average.gte": min_rating,
        "page": 1
    }
    if genre_id:
        params["with_genres"] = genre_id
    if year:
        params["primary_release_year"] = year

    try:
        r = httpx.get(f"{BASE_URL}/discover/movie", params=params, timeout=5.0)
        if r.status_code == 200:
            movies = r.json().get("results", [])[:8]
            processed = []
            for m in movies:
                rating = m.get("vote_average", 0)
                take = (
                    random.choice(CYNICAL_TAKES_HIGH) if rating >= 7.5
                    else random.choice(CYNICAL_TAKES_MID) if rating >= 5.5
                    else random.choice(CYNICAL_TAKES_LOW)
                )
                processed.append({
                    "title": m.get("title"),
                    "rating": rating,
                    "release_date": m.get("release_date", "N/A")[:4],
                    "overview": m.get("overview", "No overview provided."),
                    "poster_path": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
                    "critic_verdict": take
                })
            return processed
    except Exception:
        pass
    return []

# ==========================================
# FRONTEND INTERFACE UI
# ==========================================
st.title("🎬 The Cynical Critic")
st.caption("Real-time movie recommendations served with zero respect for your taste.")

with st.sidebar:
    st.header("Filter Criteria")
    selected_genre_name = st.selectbox("Genre", list(GENRES.keys()))
    min_rating = st.slider("Minimum Rating (TMDB)", 0.0, 9.5, 6.0, 0.5)
    release_year = st.number_input("Release Year (Optional)", min_value=1950, max_value=2026, value=None)
    
    judge_button = st.button("Judge Movies 🍿", type="primary", use_container_width=True)

if judge_button:
    genre_id = GENRES[selected_genre_name]
    log_query(selected_genre_name, min_rating, release_year)
    
    with st.spinner("Analyzing movies to roast your selections..."):
        movies = fetch_filtered_movies(genre_id, min_rating, release_year)
        
    if movies:
        st.info("🤖 **The Cynical Critic says:** *'Oh, you want movie suggestions? How original. Here is the least offensive garbage matching your strict criteria.'*")
        
        cols = st.columns(4)
        for i, movie in enumerate(movies):
            with cols[i % 4]:
                if movie["poster_path"]:
                    st.image(movie["poster_path"], use_container_width=True)
                st.subheader(movie["title"])
                st.caption(f"⭐ **{movie['rating']:.1f}** | Year: {movie['release_date']}")
                st.write(movie["overview"][:110] + "...")
                st.markdown(f'<div class="critic-verdict">"{movie["critic_verdict"]}"</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.warning("Your criteria is so absurdly specific that not even Hollywood has manufactured trash for it yet. Try again.")
