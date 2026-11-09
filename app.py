import time
import sqlite3
import streamlit as st
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION & CUSTOM STYLING
# ==========================================
st.set_page_config(
    page_title="Dynamic Sudoku Solver Agent",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for bold subgrid borders and crisp inputs
st.markdown("""
<style>
    .main { background-color: #0e0e10; }
    
    /* Input Cell Styling */
    div[data-testid="stTextInput"] input {
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        color: #ffffff;
        background-color: #1e1e24;
        border: 1px solid #3a3a45;
        border-radius: 4px;
        height: 48px;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #e50914;
        background-color: #2a2a35;
    }
    
    /* Subgrid Border Styles */
    .border-right-thick input {
        border-right: 3px solid #ff4d4d !important;
    }
    .border-bottom-thick input {
        border-bottom: 3px solid #ff4d4d !important;
    }
    .border-right-bottom-thick input {
        border-right: 3px solid #ff4d4d !important;
        border-bottom: 3px solid #ff4d4d !important;
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
            grid_size INTEGER,
            solve_time_ms REAL,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_solve_event(grid_size, time_ms, status):
    conn = sqlite3.connect("sudoku_agent.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO solve_logs (timestamp, grid_size, solve_time_ms, status) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), grid_size, time_ms, status)
    )
    conn.commit()
    conn.close()

init_db()

# ==========================================
# GENERALIZED N x N SUDOKU SOLVER ENGINE
# ==========================================
# Grid configs: Size N -> (sub_rows, sub_cols)
GRID_CONFIGS = {
    "4x4 (Mini)": {"N": 4, "sub_r": 2, "sub_c": 2},
    "6x6 (Junior)": {"N": 6, "sub_r": 2, "sub_c": 3},
    "9x9 (Standard)": {"N": 9, "sub_r": 3, "sub_c": 3}
}

PRESET_PUZZLES = {
    "4x4 (Mini)": [
        [1, 0, 0, 4],
        [0, 0, 2, 0],
        [0, 3, 0, 0],
        [2, 0, 0, 1]
    ],
    "6x6 (Junior)": [
        [0, 2, 0, 0, 4, 0],
        [1, 0, 0, 0, 0, 6],
        [0, 0, 3, 2, 0, 0],
        [0, 0, 6, 4, 0, 0],
        [5, 0, 0, 0, 0, 1],
        [0, 1, 0, 0, 6, 0]
    ],
    "9x9 (Standard)": [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
}

def is_valid(board, row, col, num, N, sub_r, sub_c):
    # Row and Column check
    for x in range(N):
        if board[row][x] == num or board[x][col] == num:
            return False
            
    # Subgrid Box check
    start_row = sub_r * (row // sub_r)
    start_col = sub_c * (col // sub_c)
    for i in range(sub_r):
        for j in range(sub_c):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve_sudoku(board, N, sub_r, sub_c):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                for num in range(1, N + 1):
                    if is_valid(board, r, c, num, N, sub_r, sub_c):
                        board[r][c] = num
                        if solve_sudoku(board, N, sub_r, sub_c):
                            return True
                        board[r][c] = 0
                return False
    return True

def is_board_valid(board, N, sub_r, sub_c):
    for r in range(N):
        for c in range(N):
            val = board[r][c]
            if val != 0:
                board[r][c] = 0
                if not is_valid(board, r, c, val, N, sub_r, sub_c):
                    board[r][c] = val
                    return False
                board[r][c] = val
    return True

# ==========================================
# STATE & UI CONTROLS
# ==========================================
st.title("🧩 Dynamic Sudoku Solver Agent")
st.caption("Constraint Satisfaction Engine supporting custom 4x4, 6x6, and 9x9 grids with subgrid outlining.")

with st.sidebar:
    st.header("⚙️ Grid Settings")
    grid_format_label = st.selectbox("Choose Grid Format", list(GRID_CONFIGS.keys()), index=2)
    cfg = GRID_CONFIGS[grid_format_label]
    N, sub_r, sub_c = cfg["N"], cfg["sub_r"], cfg["sub_c"]

    if "current_format" not in st.session_state or st.session_state.current_format != grid_format_label:
        st.session_state.current_format = grid_format_label
        st.session_state.grid = [row[:] for row in PRESET_PUZZLES[grid_format_label]]

    if st.button("Reset to Preset", use_container_width=True):
        st.session_state.grid = [row[:] for row in PRESET_PUZZLES[grid_format_label]]
        st.rerun()

    if st.button("Clear Grid 🧹", use_container_width=True):
        st.session_state.grid = [[0]*N for _ in range(N)]
        st.rerun()

# ==========================================
# GRID RENDERING WITH BOLD SUBGRID OUTLINES
# ==========================================
st.subheader(f"{grid_format_label} Grid ({N}x{N})")

grid_input = [[0]*N for _ in range(N)]

for r in range(N):
    cols = st.columns(N)
    for c in range(N):
        val = st.session_state.grid[r][c]
        
        # Determine CSS borders based on subgrid boundaries
        is_thick_right = ((c + 1) % sub_c == 0) and (c + 1 != N)
        is_thick_bottom = ((r + 1) % sub_r == 0) and (r + 1 != N)
        
        border_class = ""
        if is_thick_right and is_thick_bottom:
            border_class = "border-right-bottom-thick"
        elif is_thick_right:
            border_class = "border-right-thick"
        elif is_thick_bottom:
            border_class = "border-bottom-thick"
            
        with cols[c]:
            if border_class:
                st.markdown(f'<div class="{border_class}">', unsafe_allow_html=True)
            
            input_val = st.text_input(
                label=f"r{r}c{c}",
                value=str(val) if val != 0 else "",
                key=f"cell_{grid_format_label}_{r}_{c}",
                label_visibility="collapsed"
            )
            
            if border_class:
                st.markdown('</div>', unsafe_allow_html=True)
                
            try:
                grid_input[r][c] = int(input_val) if input_val.strip().isdigit() and 1 <= int(input_val) <= N else 0
            except ValueError:
                grid_input[r][c] = 0

col_btn1, _ = st.columns([1, 4])

with col_btn1:
    solve_clicked = st.button("Solve Puzzle ⚡", type="primary", use_container_width=True)

if solve_clicked:
    if not is_board_valid(grid_input, N, sub_r, sub_c):
        st.error(f"❌ Invalid Board Configuration! Duplicate numbers found in row, column, or subgrid box.")
        log_solve_event(N, 0, "Invalid Initial Input")
    else:
        start_time = time.time()
        board_copy = [row[:] for row in grid_input]
        
        with st.spinner(f"Agent solving {N}x{N} grid constraints..."):
            success = solve_sudoku(board_copy, N, sub_r, sub_c)
            elapsed_time_ms = round((time.time() - start_time) * 1000, 2)

        if success:
            st.session_state.grid = board_copy
            st.success(f"✅ Solved {N}x{N} puzzle in **{elapsed_time_ms} ms**!")
            log_solve_event(N, elapsed_time_ms, "Success")
            st.rerun()
        else:
            st.error("❌ Unsolvable Sudoku Puzzle!")
            log_solve_event(N, elapsed_time_ms, "Unsolvable")
