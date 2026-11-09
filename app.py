import os
import random
import httpx
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & DARK THEME
# ==========================================
st.set_page_config(
    page_title="Global Movie Agent (OMDb)",
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
# API & LOGGING SETUP
# ==========================================
OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", "")
BASE_URL = "http://www.omdbapi.com/"

# Agent Personas
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

def fetch_omdb_movies(search_query, year):
    if not OMDB_API_KEY:
        return []

    params = {
        "apikey": OMDB_API_KEY,
        "s": search_query if search_query else "movie",
        "type": "movie"
    }
    if year:
        params["y"] = year

    try:
        r = httpx.get(BASE_URL, params=params, timeout=8.0)
        if r.status_code == 200 and r.json().get("Response") == "True":
            results = r.json().get("Search", [])[:9]
            
            # Fetch detailed info for each movie to get plot, ratings, & genre
            detailed_movies = []
            for item in results:
                detail_req = httpx.get(BASE_URL, params={"apikey": OMDB_API_KEY, "i": item["imdbID"]}, timeout=5.0)
                if detail_req.status_code == 200:
                    data = detail_req.json()
                    detailed_movies.append({
                        "title": data.get("Title", "N/A"),
                        "year": data.get("Year", "N/A"),
                        "rating": data.get("imdbRating", "N/A"),
                        "genre": data.get("Genre", "N/A"),
                        "language": data.get("Language", "N/A"),
                        "country": data.get("Country", "N/A"),
                        "overview": data.get("Plot", "No plot available."),
                        "poster": data.get("Poster") if data.get("Poster") != "N/A" else ""
                    })
            return detailed_movies
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return []

# ==========================================
# USER INTERFACE
# ==========================================
st.title("🌐 Global Movie Intelligence Agent")
st.caption("Powered by OMDb API — Search world cinema, Bollywood, Anime, Korean drama, and European titles.")

with st.sidebar:
    st.header("🔍 Global Search Filters")
    
    selected_persona = st.selectbox("Agent Persona", ["Cynical Critic", "Film Historian"])
    
    # Text input allows searching any region/category globally
    search_query = st.text_input("Global Category or Title", value="Hindi", help="e.g., Hindi, Korean, Anime, Action, France, Batman, Drama")
    release_year = st.number_input("Release Year (Optional)", min_value=1940, max_value=2026, value=None)
    
    search_btn = st.button("Search Movies 🍿", type="primary", use_container_width=True)

if search_btn:
    with st.spinner("Fetching global movie database records..."):
        movies = fetch_omdb_movies(search_query, release_year)
        
    if not OMDB_API_KEY:
        st.error("🔑 **OMDb API Key Missing!** Please add `OMDB_API_KEY` in your Streamlit Cloud Secrets.")
    elif movies:
        st.success(f"Fetched top results for '{search_query}'.")
        
        cols = st.columns(3)
        for i, movie in enumerate(movies):
            with cols[i % 3]:
                if movie["poster"]:
                    st.image(movie["poster"], use_container_width=True)
                
                st.subheader(movie["title"])
                st.write(f"⭐ **IMDb: {movie['rating']}** | 📅 {movie['year']} | 🌍 {movie['country']}")
                st.caption(f"🗣️ **Lang:** {movie['language']} | 🎭 **Genre:** {movie['genre']}")
                st.write(movie["overview"][:140] + "..." if len(movie["overview"]) > 140 else movie["overview"])
                
                verdict = random.choice(PERSONA_TAKES[selected_persona])
                st.markdown(f'<div class="critic-verdict"><b>[{selected_persona}]:</b> "{verdict}"</div>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.warning("No movies found. Try broader search terms like 'India', 'Japan', 'Action', or '2023'.")
