import streamlit as st
import subprocess
import os
import matplotlib.pyplot as plt
import ast

st.set_page_config(page_title="NDVI Dashboard", layout="wide")

st.title("NDVI Vegetation Monitoring Dashboard")

place = st.text_input("Enter location (e.g., Chennai, Mumbai)")

@st.cache_data(show_spinner=False)
def run_script(place):
    process = subprocess.Popen(
        ["python", "NDVI_Region_Tool.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    output, error = process.communicate(input=place)
    return output

if st.button("Run Analysis"):

    if place.strip() == "":
        st.warning("Enter location")
    else:
        with st.spinner("Running NDVI analysis..."):
            output = run_script(place)

        st.subheader("Results")
        st.text(output)

        clean = place.replace(" ", "_").lower()

        map_file = f"ndvi_{clean}.html"
        trend_file = f"ndvi_trend_{clean}.png"
        report_file = f"NDVI_report_{clean}.txt"

        # Trend graph
        if os.path.exists(trend_file):
            st.subheader("NDVI Trend")
            st.image(trend_file)

        # Map
        if os.path.exists(map_file):
            st.subheader("NDVI Map")
            with open(map_file, "r", encoding="utf-8") as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=600)

        # Vegetation Chart
        area_line = None
        for line in output.split("\n"):
            if "{'groups'" in line:
                area_line = line
                break

        if area_line:
            stats = ast.literal_eval(area_line)
            groups = stats["groups"]

            labels = ["Bare", "Low", "Moderate", "Dense"]
            areas = [g["sum"]/1e6 for g in groups]

            fig, ax = plt.subplots()
            ax.bar(labels, areas)
            ax.set_title("Vegetation Area Distribution")
            ax.set_ylabel("Area (km²)")

            st.subheader("Vegetation Area Chart")
            st.pyplot(fig)

        # Download report
        if os.path.exists(report_file):
            with open(report_file, "rb") as f:
                st.download_button(
                    "Download Report",
                    f,
                    file_name=report_file
                )