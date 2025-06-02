import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image
import warnings
warnings.filterwarnings("ignore")
import cv2

# === CONFIGURATION ===
attendance_dir = 'Attendance'
images_dir = 'Images'  # Directory where student images are stored

# === LOAD ATTENDANCE ===
def load_attendance_data():
    all_data = []

    if not os.path.exists(attendance_dir):
        return pd.DataFrame(columns=['ID', 'Name', 'Timestamp', 'Date'])

    for file in os.listdir(attendance_dir):
        if file.endswith(".csv"):
            try:
                date_part = file.replace('.csv', '')
                date = pd.to_datetime(date_part, format='%Y-%m-%d').date()
                file_path = os.path.join(attendance_dir, file)
                df = pd.read_csv(file_path, header=None, names=["ID", "Name", "Timestamp"])
                df["Date"] = date
                all_data.append(df)
            except Exception as e:
                st.warning(f"⚠️ Skipped file '{file}' due to error: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=['ID', 'Name', 'Timestamp', 'Date'])

# === SHOW STUDENT IMAGE ===
def show_student_image(selected_name):
    st.markdown("#### 🖼️ Student Image")
    image_path = os.path.join(images_dir, f"{selected_name}.png")

    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption=f"{selected_name}'s Photo", width=160)
    else:
        st.warning(f"⚠️ No image found for {selected_name}.")

# === SHOW TABLE ===
def show_attendance_table(df, selected_name):
    st.markdown("### 🗂️ Attendance Records")
    with st.container():
        student_data = df[df['Name'] == selected_name].copy()
        student_data['Time'] = pd.to_datetime(student_data['Timestamp']).dt.time
        student_data['Logged Date'] = pd.to_datetime(student_data['Timestamp']).dt.date

        display_df = student_data[['ID', 'Name', 'Logged Date', 'Time', 'Date']]
        display_df = display_df.sort_values(by='Date', ascending=False)

        st.dataframe(display_df.reset_index(drop=True), use_container_width=True, height=300)

        col1, col2 = st.columns(2)
        with col1:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Download CSV", csv, f"{selected_name}_attendance.csv", "text/csv")

        with col2:
            excel_buffer = BytesIO()
            display_df.to_excel(excel_buffer, index=False, engine='openpyxl')
            st.download_button("⬇️ Download Excel", excel_buffer.getvalue(), f"{selected_name}_attendance.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# === TREND CHART ===
def plot_attendance_trend(df, selected_name):
    trend = df[df['Name'] == selected_name].groupby('Date').size().reset_index(name='Attendance Count')
    trend['Date'] = pd.to_datetime(trend['Date'])

    st.markdown("### 📈 Attendance Trend")
    st.line_chart(trend.set_index('Date'))

# === PERCENTAGE ===
def calculate_percentage(df, selected_name):
    total_days = df['Date'].nunique()
    present_days = df[df['Name'] == selected_name]['Date'].nunique()
    percentage = (present_days / total_days) * 100 if total_days > 0 else 0
    st.metric("✅ Attendance Percentage", f"{percentage:.2f}%")

# === MAIN ===
def main():
    st.set_page_config(page_title="📊 Attendance Dashboard", layout="wide")

    st.markdown("""
        <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            color: whitegrey;
            padding: 10px 0 20px 0;
        }
        </style>
        <div class="main-title">📅 Student Attendance Dashboard</div>
    """, unsafe_allow_html=True)

    attendance_df = load_attendance_data()

    if attendance_df.empty:
        st.warning("⚠️ No attendance data found.")
        return

    with st.sidebar:
        st.markdown("### 🎓 Select a Student")
        student_names = sorted(attendance_df['Name'].unique())
        selected_student = st.selectbox("Choose student", student_names)

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info(
            "This dashboard provides detailed attendance insights for students. "
            "You can view records, trends, and download reports."
        )

        st.markdown("---")
        st.markdown("### 📞 Helpline Numbers")
        st.success("📌 Admin Office: +91-9876543210")

    if selected_student:
        col1, col2 = st.columns([1.2, 1])
        with col1:
            show_attendance_table(attendance_df, selected_student)
        with col2:
            calculate_percentage(attendance_df, selected_student)
            show_student_image(selected_student)

        st.markdown("---")
        plot_attendance_trend(attendance_df, selected_student)

if __name__ == "__main__":
    main()
