import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time
import json
import random
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# Setting up the connection to Gsheet
conn = st.connection(
    "gsheets", 
    type=GSheetsConnection
)

# Initialize session states for application state
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = False

if 'start_time' not in st.session_state:
    st.session_state['start_time'] = None

if 'elapsed_time' not in st.session_state:
    st.session_state['elapsed_time'] = timedelta(0)

if 'running' not in st.session_state:
    st.session_state['running'] = False

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

if 'display_graph' not in st.session_state:
    st.session_state.display_graph = False

if 'graph_type' not in st.session_state:
    st.session_state.graph_type = None

# ⭐ Initialize data or load it from session state
# This is crucial - we load data only once at startup, then manage it in memory
if 'graph_data' not in st.session_state:
    st.session_state.graph_data = conn.read(worksheet="Data")
    
if 'response_data' not in st.session_state:
    st.session_state.response_data = conn.read(worksheet="Reactions")
    st.session_state.app_initialized = True

# Use data from session state
df = st.session_state.graph_data
response_data = st.session_state.response_data

# ------- LAYOUT START -------

# Title
st.title("Visualization Task")

# Go button and timer
go_button_col, timer_col = st.columns(2)

with go_button_col:
    go_button = st.button("Go", use_container_width=True, disabled=st.session_state.running)
    
    # When Go is pressed, set the graph type and start the timer
    if go_button:
        st.session_state.running = True
        st.session_state.display_graph = True
        
        # Set graph type only once when we start
        if st.session_state.graph_type is None:
            st.session_state.graph_type = random.randint(0, 1)
            
        st.session_state.last_update = datetime.now()

with timer_col:
    if st.session_state.running:
        current_time = datetime.now()
        st.session_state.elapsed_time += current_time - st.session_state.last_update
        st.session_state.last_update = current_time

    total_seconds = st.session_state.elapsed_time.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    
    # Display the time with large font
    st.markdown(f"<h1 style='text-align: center; font-size: 3em;'>{int(hours):02d}:{int(minutes):02d}:{seconds:02d}.{milliseconds:03d}</h1>", unsafe_allow_html=True)

# GRAPH SECTION
if st.session_state.display_graph:
    # Add the question above the graph
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin-bottom: 20px; background-color: #f0f2f6; border-radius: 10px;">
        <h2 style="color: #333;">What was the cause that started the second most amount of riots?</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.graph_type == 0:
        # First graph type - stacked bar
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(0, df['Amount'][0], label=df['Topic'][0])
        bottom = df['Amount'][0]

        for i in range(1, len(df)):
            ax.bar(0, df['Amount'][i], bottom=bottom, label=df['Topic'][i])
            bottom += df['Amount'][i]

        # Remove labels and ticks
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])

        # Add legend
        plt.legend()
        plt.tight_layout()
        st.pyplot(fig)
    else:
        # Second graph type - horizontal bars
        fig, ax = plt.subplots(figsize=(12, 6))
        df_sorted = df.sort_values('Amount', ascending=False)
        ax2 = sns.barplot(x='Topic', y='Amount', data=df_sorted, palette="viridis", ax=ax, hue='Topic', legend=False)
        plt.ylabel('Amount', fontsize=12)
        plt.xlabel('Topic', fontsize=12)
        plt.xticks(rotation=0)
    
        # Add clear annotations
        for i, p in enumerate(ax2.patches):
            value = int(p.get_height())
            ax2.text(p.get_x() + p.get_width()/2, 
                    p.get_height() + 0.5, 
                    f'{value}', 
                    ha='center', fontsize=11, fontweight='bold')
    
        # Add rank labels
        for i, p in enumerate(ax2.patches):
            rank = i + 1
            ax2.text(p.get_x() + p.get_width()/2, 
                    p.get_height()/2, 
                    f'Rank: {rank}', 
                    ha='center', va='center', fontsize=10, color='white', fontweight='bold')
        
        st.pyplot(fig)
else:
    # Display text instead of graph
    st.markdown("""
    <div style="text-align: center; padding: 50px; margin-top: 20px; background-color: #f0f2f6; border-radius: 10px;">
        <h1 style="color: #333;">Welcome to the Visualization Task</h1>
        <p style="font-size: 20px; margin-top: 20px;">Press the "Go" button to start the timer and display the graph.</p>
        <p style="font-size: 18px; margin-top: 10px;">Once the graph appears, select the appropriate answer using the buttons below.</p>
    </div>
    """, unsafe_allow_html=True)

# Add a separator for clarity
st.markdown("---")

### ⭐ CRITICAL CHANGE: The end_trial function now updates both Google Sheets AND session state
def end_trial(id):
    st.session_state.running = False
    st.session_state.display_graph = False
    st.session_state.graph_type = None
    elapsed_time = st.session_state.elapsed_time
    st.session_state.elapsed_time = timedelta(0)  # Reset timer
    
    total_seconds = elapsed_time.total_seconds()
    
    # Create a new row to add
    new_row = pd.DataFrame({'ID': [id], 'Time': [total_seconds]})
    
    # 1. Update our local copy of the data first (session state)
    # Make a deep copy to avoid reference issues
    updated_data = st.session_state.response_data.copy()
    
    # Append the new row using concat (more reliable than loc with dynamic indexing)
    st.session_state.response_data = pd.concat([updated_data, new_row], ignore_index=True)
    
    # 2. Then update Google Sheets in the background
    # We don't depend on reading it back immediately
    conn.update(worksheet="Reactions", data=st.session_state.response_data)
    
    # Log for debugging
    st.session_state.last_update_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.last_id_added = id
    st.session_state.last_time_recorded = total_seconds

# Answer buttons section
answer1_col, answer2_col, answer3_col, answer4_col = st.columns(4)

with answer1_col:
    answer1 = st.button("Death", use_container_width=True)

with answer2_col:
    answer2 = st.button("Officer-involved shooting", use_container_width=True, on_click=end_trial, args=(st.session_state.graph_type,))

with answer3_col:
    answer3 = st.button("Not riot-related", use_container_width=True)

with answer4_col:
    answer4 = st.button("Homicide", use_container_width=True)

# TIMER UPDATE - this needs to come at the end
if st.session_state.running:
    time.sleep(0.01)
    st.rerun()

st.markdown("---")
st.subheader("Response Time Distribution by Graph Type")

# Use the session_state.response_data which should have the fresh data
response_data = st.session_state.response_data

if not response_data.empty and len(response_data) > 0:
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Split data by ID (graph type)
    graph_type_0 = response_data[response_data['ID'] == 0]['Time']
    graph_type_1 = response_data[response_data['ID'] == 1]['Time']
    
    # Create histograms with light colors and transparency
    if not graph_type_0.empty:
        ax.hist(graph_type_0, bins=10, alpha=0.5, color='lightblue', label='Easy to spot')
    
    if not graph_type_1.empty:
        ax.hist(graph_type_1, bins=10, alpha=0.5, color='lightgreen', label='Hard to spot')
    
    # Add labels and legend
    plt.xlabel('Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('Distribution of Response Times by Graph Type')
    plt.legend()
    
    # Display the plot
    st.pyplot(fig)
else:
    st.info("No response data available yet. Complete some trials to see the histogram.")

# Add some statistics if there's data
if not response_data.empty and len(response_data) > 0:
    st.subheader("Response Time Statistics")
    
    # Group by ID and calculate statistics
    stats = response_data.groupby('ID')['Time'].agg(['count', 'mean', 'median', 'std', 'min', 'max'])
    stats = stats.reset_index()
    stats = stats.rename(columns={
        'count': 'Count', 
        'mean': 'Mean (sec)', 
        'median': 'Median (sec)', 
        'std': 'Std Dev', 
        'min': 'Min (sec)', 
        'max': 'Max (sec)'
    })
    
    # Format statistics to 2 decimal places
    for col in ['Mean (sec)', 'Median (sec)', 'Std Dev', 'Min (sec)', 'Max (sec)']:
        stats[col] = stats[col].round(2)
    
    # Display as a table
    st.dataframe(stats)
