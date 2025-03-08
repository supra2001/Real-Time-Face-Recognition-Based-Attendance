import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os

# Page Configuration
st.set_page_config(page_title="Attendance Monitoring", page_icon="📋", layout="wide")

# Sidebar Navigation
st.sidebar.title("📂 Dashboard")
st.sidebar.markdown("Monitor and track attendance records in real-time.")
st.sidebar.markdown("---")

# Main Page Title
st.markdown("<h1 style='text-align: center; font-size: 36px; color: #1F77B4;'>📋 Attendance Monitoring System</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555;'>Track Attendance with Ease</h3>", unsafe_allow_html=True)

# Get Current Date
ts = time.time()
date = datetime.fromtimestamp(ts).strftime("%d-%m-%Y")

# Load and Display Attendance Data
st.markdown("<h2 style='color: #1ABC9C;'>📅 Attendance Sheet</h2>", unsafe_allow_html=True)

file_path = f"Attendance/Attendance_{date}.csv"
if os.path.exists(file_path):
    with st.spinner("⏳ Loading attendance data..."):
        df = pd.read_csv(file_path)

        # Display Data with Styling
        st.dataframe(df.style.set_properties(**{'background-color': '#FAFAFA', 'color': '#333'}))
else:
    st.warning(f"⚠ Attendance file for {date} not found.")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("👨‍💻 **Developed by Supratim Mukherjee**")
st.sidebar.markdown("📩 For feedback & improvements, contact me!")
