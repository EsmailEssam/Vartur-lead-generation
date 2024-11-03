import streamlit as st
import pandas as pd
from io import BytesIO
from helper.scrap import scraper

# Placeholder function to simulate processing the URL
def process_url(url):
    text_result = "This is a sample text result from processing the URL."
    data = {
        "Column1": ["A", "B", "C"],
        "Column2": [1, 2, 3],
        "Column3": [4.5, 5.5, 6.5]
    }
    dataframe_result = pd.DataFrame(data)
    return text_result, dataframe_result

# Streamlit app code
st.title("LinkedIn Lead Generation")

# Sidebar for settings
st.sidebar.title("Settings")
lead_filter = st.sidebar.selectbox("Select Lead Filter", ["All", "Filter 1", "Filter 2"])

# Input URL from user
col1, col2 = st.columns(2)

with col1:
    url = st.text_input("Enter a Post URL:")

with col2:
    generate_button = st.button("Generate")

if generate_button:
    if url:
        with st.spinner('Processing...'):
            try:
                text_result, dataframe_result = scraper(url)

                # Display the Post Content
                st.markdown("### Post Content:")
                st.markdown(text_result)

                # Display the DataFrame as a table
                st.markdown("### Potential Leads:")
                st.dataframe(dataframe_result.style.highlight_max(axis=0))

                # Download button for the DataFrame
                def convert_df_to_xlsx(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.to_excel(writer, index=False, sheet_name='Sheet1')
                    return output.getvalue()

                xlsx_data = convert_df_to_xlsx(dataframe_result)

                # Show download button
                st.download_button(
                    label="Download as XLSX",
                    data=xlsx_data,
                    file_name="dataframe_result.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.error(f"Error processing URL: {e}")
    else:
        st.warning("Please enter a URL.")

# Help section
st.markdown("""
### How to Use
1. Enter a LinkedIn post URL in the text box.
2. Click on **Generate** to extract potential leads.
3. Download the data as an XLSX file if needed.
""")
