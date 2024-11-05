import streamlit as st
import pandas as pd
from io import BytesIO
import plotly.express as px
from helper.scrap import scraper

# Streamlit app code
st.title("Social Media Lead Generation")

# Sidebar for settings with radio buttons
st.sidebar.title("Settings")
lead_filter = st.sidebar.radio("Choose a Platform", ["LinkedIn", "Instagram", "X"])
st.title("Social Media Lead Generation")

# Sidebar for settings with radio buttons
st.sidebar.title("Settings")
lead_filter = st.sidebar.radio("Choose a Platform", ["LinkedIn", "Instagram", "X"])

# Input URL from user

url = st.text_input("Enter a Post URL:")


generate_button = st.button("Generate")

# Initialize session state for the selected chart
if 'chart_type' not in st.session_state:
    st.session_state['chart_type'] = "Pie Chart"

if lead_filter == "LinkedIn":
    if generate_button:
        if url:
            with st.spinner("Processing..."):
                try:
                    text_result, dataframe_result = scraper(url)

                    # Display the DataFrame as a table
                    st.markdown("### Potential Leads")
                    st.dataframe(dataframe_result)

                    st.markdown("### Analysis")
                    tab1, tab2, tab3 = st.tabs(["Pie Chart", "Histogram", "Bar Chart"])

                    with tab1:
                        fig = px.pie(dataframe_result, names="Is Lead")
                        st.plotly_chart(fig, use_container_width=True)

                    with tab2:
                        st.info("Histogram is coming soon!")
                    
                    with tab3:
                        st.info("Bar Chart is coming soon!")
                        
                    # Download button for the DataFrame
                    csv_data = dataframe_result.to_csv(index=False).encode("utf-8")

                    # Show download button
                    st.download_button(
                        label="Download as CSV",
                        data=csv_data,
                        file_name="dataframe_result.csv",
                        mime="text/csv",
                    )
                except Exception as e:
                    st.error(f"Error processing URL: {e}")
        else:
            st.warning("Please enter a URL.")
else:
    # Show "Coming Soon" message for Instagram and X
    st.info(f"{lead_filter} functionality is coming soon!")

# Help section
st.markdown(
    """
### How to Use
1. Enter a LinkedIn post URL in the text box.
2. Click on **Generate** to extract potential leads.
3. Download the data as an CSV file if needed.
"""
)
