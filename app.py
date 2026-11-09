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

OMDB_API_KEY = st.secrets.get("OMDB_API_KEY", "")
BASE_URL = "http://www.omdbapi.com/"

# Global Languages & Curated Popular Keywords for OMDb compatibility
LANGUAGE_KEYWORDS = {
    "All World Cinema": ["Avengers", "Batman", "Inception", "Spider", "Matrix"],
    "Hindi / Bollywood (हिंदी)": ["Dangal", "Pathaan", "Jawan", "3 Idiots", "Sholay", "RRR", "Brahmastra"],
    "Korean / K-Drama (한국어)": ["Parasite", "Train to Busan", "Oldboy", "Decision to Leave", "Exhuma"],
    "Japanese / Anime (日本語)": ["Suzume", "Your Name", "Godzilla", "Spirited Away", "Demon Slayer"],
    "Tamil / Kollywood (தமிழ்)": ["Leo", "Jailer", "Vikram", "Ponniyin Selvan", "Master"],
    "Telugu / Tollywood (తెలుగు)": ["RRR", "Pushpa", "Baahubali", "Kalki", "Salar"],
    "Spanish (Español)": ["Pan's Labyrinth", "Roma", "Money Heist", "The Platform"],
    "French (Français)": ["Amélie", "Intouchables", "La La Land", "Portrait of a Lady on Fire"]
}

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

def fetch_omdb_movies(search_term, year=None):
    if not OMDB_API_KEY:
        # Fallback Mock Data if API Key is not set in Secrets
        return [
            {
                "title": "Parasite",
                "year": "2019",
                "rating": "8.5",
                "genre": "Drama, Thriller",
                "language": "Korean",
                "country": "South Korea",
                "overview": "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan.",
                "poster": "https://m.media-amazon.com/images/M/MV5BYWZjMjk3ZTItODQ2ZC00NTlhLWE0WEItZmFjOWJhYzFiYWVmXkEyXkFqcGdeQXVyMTA3MDk2NDg2._V1_SX300.jpg"
            },
            {
                "title": "RRR",
                "year": "2022",
                "rating": "7.8",
                "genre": "Action, Drama",
                "language": "Telugu, Tamil, Hindi",
                "country": "India",
                "overview": "A fearless revolutionary and an officer in the British army join forces to fight for independence.",
                "poster": "https://m.media-amazon.com/images/M/MV5BODUwNDNjYzctODUxNy00ZTA2LWAyYTEtMDhhNDQwZjdhMGNmXkEyXkFqcGdeQXVyNTE1NjY5Mg@@._V1_SX300.jpg"
            }
        ]

    params = {"apikey": OMDB_API_KEY, "s": search_term, "type": "movie"}
    if year:
        params["y"] = year

    try:
        r = httpx.get(BASE_URL, params=params, timeout=8.0)
        if r.status_code == 200 and r.json().get("Response") == "True":
            results = r.json().get("Search", [])[:6]
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
st.caption("Search regional cinema worldwide with custom agent perspectives.")

with st.sidebar:
    st.header("🔍 Filter & Search Options")
    
    selected_persona = st.selectbox("Agent Persona", ["Cynical Critic", "Film Historian"])
    selected_region = st.selectbox("Select Global Region / Language", list(LANGUAGE_KEYWORDS.keys()))
    
    custom_title = st.text_input("Or Direct Movie Title (Optional)", placeholder="e.g. Inception, KGF, Naruto")
    release_year = st.number_input("Release Year (Optional)", min_value=1950, max_value=2026, value=None)
    
    search_btn = st.button("Search Movies 🍿", type="primary", use_container_width=True)

if search_btn:
    # Determine search term
    if custom_title.strip():
        search_query = custom_title.strip()
    else:
        # Pick a random keyword from the selected regional bucket to ensure valid OMDb results
        search_query = random.choice(LANGUAGE_KEYWORDS[selected_region])

    with st.spinner(f"Fetching movies matching '{search_query}'..."):
        movies = fetch_omdb_movies(search_query, release_year)
        
    if movies:
        st.success(f"Showing top results for category: **{selected_region}** (Search: *{search_query}*)")
        
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
        st.warning("No matches found for this specific year/title combo. Clear the year box or try a direct movie title!")
