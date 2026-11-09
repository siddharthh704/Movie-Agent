import time
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & DARK THEME
# ==========================================
st.set_page_config(
    page_title="Sudoku Solver Agent",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0e0e10; }
    div[data-testid="stTextInput"] input {
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        color: #ffffff;
        background-color: #1e1e24;
        border: 1px solid #3a3a45;
        border-radius: 6px;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #ff4d4d;
        background-color: #2a2a35;
    }
    .status-card {
        background-color: #18181c;
        border: 1px solid #2d2d35;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATABASE LOGGING
# ==========================================
def init_db():
    conn = sqlite3.connect("sudoku_agent.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solve_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            difficulty TEXT,
            solve_time_ms REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_solve_event(difficulty, time_ms, status):
    conn = sqlite3.connect("sudoku_agent.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO solve_logs (timestamp, difficulty, solve_time_ms, status) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), difficulty, time_ms, status)
    )
    conn.commit()
    conn.close()

init_db()

# ==========================================
# SUDOKU SOLVER ENGINE (BACKTRACKING)
# ==========================================
PRESET_PUZZLES = {
    "Easy": [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ],
    "Medium": [
        [0, 0, 0, 6, 0, 0, 4, 0, 0],
        [7, 0, 0, 0, 0, 3, 6, 0, 0],
        [0, 0, 0, 0, 9, 1, 0, 8, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 5, 0, 1, 8, 0, 0, 0, 3],
        [0, 0, 0, 3, 0, 6, 0, 4, 5],
        [0, 4, 0, 2, 0, 0, 0, 6, 0],
        [9, 0, 3, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 0, 1, 0, 0]
    ],
    "Hard": [
        [0, 0, 0, 0, 0, 0, 0, 1, 2],
        [0, 0, 0, 0, 3, 5, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 7, 0],
        [7, 0, 0, 0, 0, 0, 3, 0, 0],
        [0, 0, 0, 4, 0, 0, 8, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 2, 0, 0, 0, 0],
        [0, 8, 0, 0, 0, 0, 0, 4, 0],
        [0, 5, 0, 0, 0, 0, 6, 0, 0]
    ]
}

def is_valid(board, row, col, num):
    for x in range(9):
        if board[row][x] == num or board[x][col] == num:
            return False
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve_sudoku(board):
    for r in range(9):
        for c in range(9):
            if board[r][c] == 0:
                for num in range(1, 10):
                    if is_valid(board, r, c, num):
                        board[r][c] = num
                        if solve_sudoku(board):
                            return True
                        board[r][c] = 0
                return False
    return True

def is_board_valid(board):
    for r in range(9):
        for c in range(9):
            val = board[r][c]
            if val != 0:
                board[r][c] = 0
                if not is_valid(board, r, c, val):
                    board[r][c] = val
                    return False
                board[r][c] = val
    return True

# ==========================================
# USER INTERFACE
# ==========================================
st.title("🧩 Sudoku Solver Agent")
st.caption("Constraint Satisfaction Engine built with Python & Streamlit.")

if "grid" not in st.session_state:
    st.session_state.grid = [row[:] for row in PRESET_PUZZLES["Easy"]]

with st.sidebar:
    st.header("⚙️ Agent Settings")
    preset_choice = st.selectbox("Load Preset Puzzle", ["Custom", "Easy", "Medium", "Hard"])
    
    if st.button("Load Selected Preset", use_container_width=True):
        if preset_choice != "Custom":
            st.session_state.grid = [row[:] for row in PRESET_PUZZLES[preset_choice]]
            st.rerun()

    if st.button("Clear Grid 🧹", use_container_width=True):
        st.session_state.grid = [[0]*9 for _ in range(9)]
        st.rerun()

# Render 9x9 Grid Input UI
st.subheader("Interactive 9x9 Grid")

grid_input = [[0]*9 for _ in range(9)]
cols_container = st.container()

with cols_container:
    for r in range(9):
        cols = st.columns(9)
        for c in range(9):
            val = st.session_state.grid[r][c]
            input_val = cols[c].text_input(
                label=f"r{r}c{c}",
                value=str(val) if val != 0 else "",
                key=f"cell_{r}_{c}",
                label_visibility="collapsed"
            )
            try:
                grid_input[r][c] = int(input_val) if input_val.strip().isdigit() and 1 <= int(input_val) <= 9 else 0
            except ValueError:
                grid_input[r][c] = 0

col_btn1, col_btn2 = st.columns([1, 4])

with col_btn1:
    solve_clicked = st.button("Solve Puzzle ⚡", type="primary", use_container_width=True)

if solve_clicked:
    if not is_board_valid(grid_input):
        st.error("❌ Invalid Board Configuration! Check for duplicate numbers in the same row, column, or 3x3 box.")
        log_solve_event(preset_choice, 0, "Invalid Initial Input")
    else:
        start_time = time.time()
        board_copy = [row[:] for row in grid_input]
        
        with st.spinner("Agent is solving board constraints..."):
            success = solve_sudoku(board_copy)
            elapsed_time_ms = round((time.time() - start_time) * 1000, 2)

        if success:
            st.session_state.grid = board_copy
            st.success(f"✅ Solved successfully in **{elapsed_time_ms} ms**!")
            log_solve_event(preset_choice, elapsed_time_ms, "Success")
            st.rerun()
        else:
            st.error("❌ Unsolvable Sudoku Puzzle!")
            log_solve_event(preset_choice, elapsed_time_ms, "Unsolvable")
