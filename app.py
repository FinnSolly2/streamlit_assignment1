import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import time
import random
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

st.set_page_config(
    page_title="Visualization Analysis Task",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling. NOTE: generate by generative AI, as I don't know CSS that well :)!
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Card styling */
    .card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .card-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1E3A8A;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
        height: 3rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Go button */
    .go-button .stButton > button {
        background-color: #4CAF50;
        color: white;
    }
    
    /* Answer buttons */
    .answer-button .stButton > button {
        background-color: #3b82f6;
        color: white;
    }
    
    /* Timer styling */
    .timer-display {
        text-align: center;
        font-size: 3.5rem;
        font-weight: 700;
        font-family: 'Courier New', monospace;
        color: #1E3A8A;
    }
    
    /* Question styling */
    .question-card {
        background-color: #edf2fb;
        border-left: 6px solid #3b82f6;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 8px;
    }
    
    /* Stats card */
    .stats-card {
        background-color: #f0f4f8;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    
    /* Titles */
    h1, h2, h3 {
        color: #1E3A8A;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e5e7eb;
        color: #6b7280;
        font-size: 0.875rem;
    }
</style>
""", unsafe_allow_html=True)

url = "https://docs.google.com/spreadsheets/d/1A_xcXCZcWGg0ixa83XVUFgunb_m1ATry1a37ZDID4vI/edit?gid=0#gid=0"

conn = st.connection(
    "gsheets", 
    type=GSheetsConnection,
    ttl=0  # Disable caching to always get fresh data
)

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
    
if 'data_updated' not in st.session_state:
    st.session_state.data_updated = False
    
if 'response_data' not in st.session_state:
    st.session_state.response_data = None
    
if 'show_completion' not in st.session_state:
    st.session_state.show_completion = False
    
if 'completion_time' not in st.session_state:
    st.session_state.completion_time = None

if not st.session_state.app_initialized:
    # First time loading the app fetch data from Google Sheets
    st.session_state.graph_data = conn.read(spreadsheet=url, worksheet="Data")
    st.session_state.response_data = conn.read(spreadsheet=url, worksheet="Reactions")
    st.session_state.app_initialized = True
    st.session_state.first_load = True
else:
    st.session_state.first_load = False

# Use data from session state
df = st.session_state.graph_data
response_data = st.session_state.response_data

# ------- LAYOUT START -------

st.markdown("""
<div style="text-align: center; padding-bottom: 1.5rem;">
    <h1 style="color: #1E3A8A; font-size: 2.5rem; margin-bottom: 0.5rem;">📊 Visualization Analysis Task</h1>
    <p style="color: #6b7280; font-size: 1.1rem;">Test your ability to interpret data visualizations quickly and accurately</p>
</div>
""", unsafe_allow_html=True)

if not st.session_state.running:
    st.markdown("""
    <div style="margin-bottom: 1.5rem;">
        <div class="card-header">Task Instructions</div>
        <p>1. Click the <b>Start Task</b> button below to begin</p>
        <p>2. A visualization will appear with a question</p>
        <p>3. Answer the question as quickly and accurately as possible</p>
        <p>4. Your response time will be recorded for analysis</p>
    </div>
    """, unsafe_allow_html=True)

# Go button and timer section
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
    # Only show the Go button if not running
    if not st.session_state.running:
        with st.markdown('<div class="go-button">', unsafe_allow_html=True):
            go_button = st.button("Start Task", use_container_width=True, disabled=st.session_state.running)
        
        if go_button:
            st.session_state.running = True
            st.session_state.display_graph = True
            
            if st.session_state.graph_type is None:
                st.session_state.graph_type = random.randint(0, 1)
                
            st.session_state.last_update = datetime.now()
    
    # Timer display
    if st.session_state.running:
        current_time = datetime.now()
        st.session_state.elapsed_time += current_time - st.session_state.last_update
        st.session_state.last_update = current_time

    total_seconds = st.session_state.elapsed_time.total_seconds()
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    
    if st.session_state.running:
        st.markdown(f"""
        <div class="timer-display">
            {int(hours):02d}:{int(minutes):02d}:{seconds:02d}<span style="font-size: 2rem;">.{milliseconds:03d}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# GRAPH SECTION
if st.session_state.display_graph:
    # Add the question above the graph with improvd styling
    st.markdown("""
    <div class="question-card">
        <h2 style="text-align: center; color: #1E3A8A; margin: 0;">What was the cause that started the second most amount of riots?</h2>
    </div>
    """, unsafe_allow_html=True)
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create better color palettes
    if st.session_state.graph_type == 0:
        # First graph type - stacked bar with better colors
        colors = sns.color_palette("viridis", len(df))
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#f8f9fa')
        ax.bar(0, df['Amount'][0], label=df['Topic'][0], color=colors[0])
        bottom = df['Amount'][0]

        for i in range(1, len(df)):
            ax.bar(0, df['Amount'][i], bottom=bottom, label=df['Topic'][i], color=colors[i])
            bottom += df['Amount'][i]

        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        
        for spine in ax.spines.values():
            spine.set_edgecolor('#e5e7eb')

        legend = plt.legend(title="Causes", bbox_to_anchor=(1.05, 1), loc='upper left', 
                  frameon=True, facecolor='white', edgecolor='#e5e7eb')
        legend.get_title().set_fontweight('bold')
        
        plt.tight_layout()
        st.pyplot(fig)
    else:
        # Second graph type - horizontal bars with better design
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#f8f9fa')
        df_sorted = df.sort_values('Amount', ascending=False)
        
        custom_palette = sns.color_palette("viridis", len(df_sorted))
        
        ax2 = sns.barplot(x='Topic', y='Amount', data=df_sorted, palette=custom_palette, ax=ax, hue='Topic', legend=False)
        plt.ylabel('Amount', fontsize=12, fontweight='bold')
        plt.xlabel('Topic', fontsize=12, fontweight='bold')
        plt.xticks(rotation=15, ha='right', fontsize=10)
        


        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add a border to the figure
        for spine in ax.spines.values():
            spine.set_edgecolor('#e5e7eb')
    
        for i, p in enumerate(ax2.patches):
            value = int(p.get_height())
            ax2.text(p.get_x() + p.get_width()/2, 
                    p.get_height() + 0.5, 
                    f'{value}', 
                    ha='center', fontsize=11, fontweight='bold')
    
        # Add rank labels with better contrast
        for i, p in enumerate(ax2.patches):
            rank = i + 1
            ax2.text(p.get_x() + p.get_width()/2, 
                    p.get_height()/2, 
                    f'Rank: {rank}', 
                    ha='center', va='center', fontsize=11, color='white', 
                    fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", 
                                                facecolor='black', 
                                                edgecolor='none', alpha=0.5))
        
        plt.tight_layout()
        st.pyplot(fig)
else:
    st.markdown("""
    <div style="text-align: center; padding: 3rem 1rem; background-color: #edf2fb; border-radius: 12px; margin: 1rem 0;">
        <h2 style="color: #1E3A8A; margin-bottom: 1.5rem;">🎯 Ready to Test Your Visual Analysis Skills?</h2>
        <p style="font-size: 1.2rem; margin-bottom: 1rem;">This task measures how quickly you can extract information from data visualizations.</p>
        <p style="font-size: 1.1rem;">Press the "Start Task" button above to begin!</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # Close the main card

### Function to end trial and record data
def end_trial(id):
    st.session_state.running = False
    st.session_state.display_graph = False
    st.session_state.graph_type = None
    elapsed_time = st.session_state.elapsed_time
    
    # Store the completion time for display
    st.session_state.completion_time = elapsed_time.total_seconds()
    st.session_state.show_completion = True
    
    st.session_state.elapsed_time = timedelta(0)  # Reset timer
    
    total_seconds = elapsed_time.total_seconds()
    
    new_row = pd.DataFrame({'ID': [id], 'Time': [total_seconds]})
    
    # Update our local copy of the data first
    st.session_state.response_data = pd.concat([st.session_state.response_data, new_row], ignore_index=True)
    
    # Then update Google Sheets in the background
    conn.update(worksheet="Reactions", data=st.session_state.response_data)
    
    # Set a flag to indicate we need to refresh the UI
    st.session_state.data_updated = True

if st.session_state.display_graph:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">Select Your Answer:</div>', unsafe_allow_html=True)
    
    answer1_col, answer2_col, answer3_col, answer4_col = st.columns(4)

    with answer1_col:
        with st.markdown('<div class="answer-button">', unsafe_allow_html=True):
            answer1 = st.button("Death", use_container_width=True)

    with answer2_col:
        with st.markdown('<div class="answer-button">', unsafe_allow_html=True):
            answer2 = st.button("Officer-involved shooting", use_container_width=True, on_click=end_trial, args=(st.session_state.graph_type,))

    with answer3_col:
        with st.markdown('<div class="answer-button">', unsafe_allow_html=True):
            answer3 = st.button("Not riot-related", use_container_width=True)

    with answer4_col:
        with st.markdown('<div class="answer-button">', unsafe_allow_html=True):
            answer4 = st.button("Homicide", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# TIMER UPDATE - I need to put this at the end
if st.session_state.running:
    time.sleep(0.01)
    st.rerun()

# Check if data was updated and reload the page if needed
if st.session_state.data_updated:
    st.session_state.data_updated = False 
    st.rerun()

# Display completion message when the user answers correctly
if st.session_state.show_completion:
    # Format the time nicely
    completion_seconds = st.session_state.completion_time
    minutes, seconds = divmod(completion_seconds, 60)
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    
    st.markdown(f"""
    <div class="card" style="background-color: #d1fae5; border-left: 6px solid #10b981;">
        <div style="text-align: center;">
            <h2 style="color: #065f46; margin-bottom: 0.5rem;">✅ Correct Answer!</h2>
            <p style="font-size: 1.25rem; color: #065f46;">
                Your time: <span style="font-weight: bold;">{int(minutes):02d}:{seconds:02d}.{milliseconds:03d}</span>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a button to start a new task
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.markdown('<div class="go-button">', unsafe_allow_html=True):
            if st.button("Start New Task", use_container_width=True):
                st.session_state.show_completion = False
                st.rerun()

# Results Section with Improved Design
if st.session_state.response_data is not None and not st.session_state.response_data.empty and len(st.session_state.response_data) > 0:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-header">Response Time Analysis</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Distribution", "Statistics"])
    
    with tab1:
        fig, ax = plt.subplots(figsize=(10, 6), facecolor='#f8f9fa')
        
        graph_type_0 = st.session_state.response_data[st.session_state.response_data['ID'] == 0]['Time']
        graph_type_1 = st.session_state.response_data[st.session_state.response_data['ID'] == 1]['Time']
        
        if not graph_type_0.empty:
            sns.histplot(graph_type_0, bins=10, alpha=0.7, color='#3b82f6', label='Hard to Spot (Type 0)', ax=ax)
        
        if not graph_type_1.empty:
            sns.histplot(graph_type_1, bins=10, alpha=0.7, color='#10b981', label='Easy to Spot (Type 1)', ax=ax)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        for spine in ax.spines.values():
            spine.set_edgecolor('#e5e7eb')
            
        plt.xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        plt.ylabel('Frequency', fontsize=12, fontweight='bold')
        plt.title('Distribution of Response Times by Graph Type', fontsize=14, fontweight='bold', pad=20)
        legend = plt.legend(title="Graph Types", frameon=True, facecolor='white', edgecolor='#e5e7eb')
        legend.get_title().set_fontweight('bold')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab2:
        stats = response_data.groupby('ID')['Time'].agg(['count', 'mean', 'median', 'std', 'min', 'max'])
        stats = stats.reset_index()
        
        stats['ID'] = stats['ID'].map({0: 'Type 0 (Hard)', 1: 'Type 1 (Easy)'})
        
        stats = stats.rename(columns={
            'ID': 'Graph Type',
            'count': 'Count', 
            'mean': 'Mean (sec)', 
            'median': 'Median (sec)', 
            'std': 'Std Dev', 
            'min': 'Min (sec)', 
            'max': 'Max (sec)'
        })
        
        for col in ['Mean (sec)', 'Median (sec)', 'Std Dev', 'Min (sec)', 'Max (sec)']:
            stats[col] = stats[col].round(2)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Type 0 (Hard to Spot)")
            if 'Type 0 (Hard)' in stats['Graph Type'].values:
                easy_stats = stats[stats['Graph Type'] == 'Type 0 (Hard)'].iloc[0]
                
                st.markdown(f"""
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1; min-width: 120px; background-color: #dbeafe; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #1e40af;">Average Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1e3a8a;">{easy_stats['Mean (sec)']}s</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: #dbeafe; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #1e40af;">Median Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1e3a8a;">{easy_stats['Median (sec)']}s</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: #dbeafe; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #1e40af;">Fastest Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #1e3a8a;">{easy_stats['Min (sec)']}s</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No data available for Type 0 yet.")
        
        with col2:
            st.subheader("Type 1 (Easy to Spot)")
            if 'Type 1 (Easy)' in stats['Graph Type'].values:
                hard_stats = stats[stats['Graph Type'] == 'Type 1 (Easy)'].iloc[0]
                
                st.markdown(f"""
                <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                    <div style="flex: 1; min-width: 120px; background-color: #dcfce7; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #047857;">Average Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #065f46;">{hard_stats['Mean (sec)']}s</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: #dcfce7; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #047857;">Median Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #065f46;">{hard_stats['Median (sec)']}s</div>
                    </div>
                    <div style="flex: 1; min-width: 120px; background-color: #dcfce7; padding: 15px; border-radius: 8px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #047857;">Fastest Time</div>
                        <div style="font-size: 1.5rem; font-weight: bold; color: #065f46;">{hard_stats['Min (sec)']}s</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("No data available for Type 1 yet.")
                
        st.subheader("Detailed Statistics")
        st.dataframe(stats, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)