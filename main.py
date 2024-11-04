import streamlit as st
import pandas as pd
from io import BytesIO
from helper.scrap import scraper
import validators  # Make sure to install this package for URL validation

# Streamlit app code
st.title("LinkedIn Lead Generation")

# Input URL from user
url = st.text_input("Enter a LinkedIn Post URL:")

# Generate button
if st.button("Generate"):
    if url and validators.url(url) and "linkedin.com" in url:
        with st.spinner("Processing..."):
            try:
                # Process the URL
                text_result, dataframe_result = scraper(url)

                # Display the DataFrame as a table
                st.write("Potential Leads:")
                st.dataframe(dataframe_result)

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
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a valid LinkedIn URL.")
