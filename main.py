import streamlit as st
import pandas as pd
from data_engine import rasha_parse_intent, your_add_and_sort_itinerary

st.set_page_config(layout="wide", page_title="SheetMap Workspace")

# Custom Dark/Neon Workspace Theming
st.markdown("""
    <style>
    .stApp { background-color: #0f1115; color: #e2e8f0; }
    h1 { color: #38bdf8 !important; font-family: monospace; font-weight: bold; }
    .stButton>button { background-color: #38bdf8 !important; color: #0f1115 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ SheetMap: AI-Powered Travel Ledger")
st.caption("Fusing Tabular Financial Records with Real-Time Spatial Mapping Layouts")

# 1. Initialize Starting State Framework (Matches your exact prompt requirement)
if "itinerary_data" not in st.session_state:
    st.session_state.itinerary_data = pd.DataFrame([
        {
            "Time Slot": "12:00 PM", 
            "My Raw Note": "Lunch somewhere cheap near the central station on Tuesday", 
            "Venue Name": "The Station Diner", 
            "Price": "£", 
            "Cost (£)": 12,
            "Hours": "08:00 AM - 10:00 PM", 
            "Address": "Euston Rd, London NW1 2RT",
            "latitude": 51.5284,
            "longitude": -0.1338
        }
    ])

# 2. Live Budget Interlocking Card Component Dashboard UI
total_cost = int(st.session_state.itinerary_data["Cost (£)"].sum())
st.metric(label="📊 Running Total Estimated Budget Accrual", value=f"£{total_cost}")

# 3. Create the Split-Screen Workspace (60% Spreadsheet Panel, 40% Map Panel)
col1, col2 = st.columns([0.6, 0.4])

with col1:
    st.subheader("📝 Living Itinerary Spreadsheet Workspace")
    
    # Render interactive data grid table canvas
    edited_df = st.data_editor(
        st.session_state.itinerary_data, 
        num_rows="dynamic", 
        use_container_width=True,
        key="spreadsheet_editor"
    )
    st.session_state.itinerary_data = edited_df

    st.markdown("---")
    st.subheader("📥 Ingestion Pipeline Portal")
    
    # Entry form inputs
    with st.form("ingest_form", clear_on_submit=True):
        user_input_note = st.text_input("What do you want to plan?", placeholder="e.g., Find an upscale Italian dinner spot under £50")
        user_input_time = st.text_input("Set Arrival Time", value="07:00 PM")
        submit_clicked = st.form_submit_button("Engage Gemma Data Fusion Pipeline")
        
        if submit_clicked and user_input_note:
            with st.spinner("Gemma 4 orchestrating layout matrix transformations..."):
                
                # Execution Pipeline Loop:
                # Stage A: Pass target string into Rasha's parsing logic engine
                parsed_data = rasha_parse_intent(user_input_note)
                
                # Stage B: Pass result into your chronological assembly sorting engine
                updated_dataframe = your_add_and_sort_itinerary(
                    st.session_state.itinerary_data, 
                    parsed_data, 
                    user_input_time, 
                    user_input_note
                )
                
                # Stage C: Commit back to system runtime state cache and reload interface
                st.session_state.itinerary_data = updated_dataframe
                st.rerun()

with col2:
    st.subheader("📍 Real-Time Spatial Routing Visualizer")
    
    # Isolate valid latitude/longitude numbers to display tracking pin marks
    map_pins = st.session_state.itinerary_data[["latitude", "longitude"]].dropna()
    
    if not map_pins.empty:
        st.map(map_pins)
    else:
        st.info("No spatial data coordinate points mapped in ledger columns yet.")
