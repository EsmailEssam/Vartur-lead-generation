import streamlit as st
import pandas as pd
import os
from io import BytesIO
import base64
import plotly.express as px
from helper.scrap import scraper
import time
import traceback
from helper.config import LinkedInLoginError, InstagramLoginError, InvalidCredentialsError
from helper.instagramscraper import InstagramScraper
from helper.linkedinscraper import LinkedInScraper

# Configure page
st.set_page_config(
    page_title="Social Media Lead Generation @ Vartur",
    page_icon="🎯",
    layout="wide"
)

# Initialize session states
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'dataframe_result' not in st.session_state:
    st.session_state.dataframe_result = None
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""

# Cache the image loading to improve performance
@st.cache_data
def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Load images once
try:
    background = image_to_base64(os.path.join('data', 'background.png'))
    logo_base64 = image_to_base64(os.path.join('data', 'logo-vartur.png'))
    x_logo_base64 = image_to_base64(os.path.join('data', 'logo-x.png'))
    insta_logo_base64 = image_to_base64(os.path.join('data', 'logo-insta.png'))
    linkedin_logo_base64 = image_to_base64(os.path.join('data', 'logo-linkedin.png'))
    logos = {
        'LinkedIn': linkedin_logo_base64,
        "Instagram": insta_logo_base64,
        "X": x_logo_base64
    }
except Exception as e:
    st.error(f"Error loading images: {str(e)}")
    st.stop()

# Apply background and styles
st.markdown(f"""
    <style>
        .stApp {{
            background-image: url("data:image/png;base64,{background}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
        }}
        .stDataFrame {{
            background-color: rgba(255, 255, 255, 0.9) !important;
        }}
        .custom-metric-container {{
            background-color: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }}
        .stButton > button {{
            width: 100%;
            background: linear-gradient(45deg, #2E7D32, #4CAF50) !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
            padding: 0.75rem 1.5rem !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.3s ease !important;
        }}
        .stButton > button:hover {{
            background: linear-gradient(45deg, #1B5E20, #388E3C) !important;
            box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2) !important;
            transform: translateY(-2px) !important;
        }}
    </style>
""", unsafe_allow_html=True)

# Header with logo
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 2em; margin-right: 10px;">🎯</span>
            <h1 style="margin: 0;">Social Media Leads Generation</h1>
        </div>
        <img src="data:image/png;base64,{logo_base64}" style="width: 150px; height: 150px; margin-right: 50px;">
    </div>
""", unsafe_allow_html=True)

st.divider()

# Sidebar configuration
with st.sidebar:
    st.title("Settings")
    
    # Platform selection
    lead_filter = st.radio("Choose a Platform", ["LinkedIn", "Instagram", "X"])
    
    # Debug mode toggle for development
    st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
    
    # Login section
    st.markdown(f"### {lead_filter} Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Save Credentials")
        
        if submitted:
            st.session_state['email'] = email
            st.session_state['password'] = password
            st.success("Credentials saved!")

# Main content area
st.markdown(f""" 
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logos[lead_filter]}" style="width: 30px; height: 30px;">
        <h2 style="margin-left: 10px;">{lead_filter} Leads Generation</h2>
    </div>
""", unsafe_allow_html=True)

# URL input and processing
url = st.text_input(f"Enter {lead_filter} Post URL:")

# Check if URL has changed
if url != st.session_state.current_url:
    st.session_state.dataframe_result = None
    st.session_state.current_url = url

if lead_filter == "LinkedIn":
    if not url:
        st.info("Please enter a LinkedIn post URL to begin.")
    elif 'email' not in st.session_state or not st.session_state['email']:
        st.warning("Please enter your LinkedIn credentials in the sidebar first.")
    else:
        # Process button with loading animation
        if st.button("Generate Leads", use_container_width=True):
            with st.spinner('Processing... This may take a few minutes.'):
                try:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update status
                    status_text.text("Logging in to LinkedIn...")
                    progress_bar.progress(20)
                    
                    # Get the data
                    st.session_state.dataframe_result = LinkedInScraper(
                        url,
                        st.session_state['email'],
                        st.session_state['password'],
                        is_headless=not st.session_state.debug_mode
                    ).scrape()
                    
                    progress_bar.progress(100)
                    status_text.text("Processing complete!")
                    time.sleep(1)
                    status_text.empty()
                    progress_bar.empty()

                except InvalidCredentialsError:
                    st.error("Invalid LinkedIn credentials. Please check your email and password.")
                except LinkedInLoginError as e:
                    st.error(f"Login error: {str(e)}")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                    if st.session_state.debug_mode:
                        with st.expander("Error Details"):
                            st.code(traceback.format_exc())

        # Display results if data exists
        if st.session_state.dataframe_result is not None and not st.session_state.dataframe_result.empty:
            # Show results in tabs
            tab1, tab2 = st.tabs(["📊 Data", "📈 Analysis"])
            
            with tab1:
                st.markdown("### Identified Leads")
                
                # Check if 'Is Lead' column exists
                if 'Is Lead' in st.session_state.dataframe_result.columns:
                    lead_filter = st.selectbox(
                        "Filter by lead status:",
                        ["All", "Lead", "Not a Lead"]
                    )
                    
                    filtered_df = st.session_state.dataframe_result
                    if lead_filter != "All":
                        filtered_df = st.session_state.dataframe_result[st.session_state.dataframe_result["Is Lead"] == lead_filter]
                else:
                    filtered_df = st.session_state.dataframe_result
                
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        "Download as CSV",
                        csv,
                        "leads.csv",
                        "text/csv",
                        use_container_width=True
                    )
                with col2:
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        filtered_df.to_excel(writer, sheet_name='Leads', index=False)
                    excel_data = buffer.getvalue()
                    st.download_button(
                        "Download as Excel",
                        excel_data,
                        "leads.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with tab2:
                # Summary metrics
                if 'Is Lead' in st.session_state.dataframe_result.columns:
                    total_leads = len(st.session_state.dataframe_result[st.session_state.dataframe_result["Is Lead"] == "Lead"])
                    total_comments = len(st.session_state.dataframe_result)
                    lead_rate = (total_leads / total_comments * 100) if total_comments > 0 else 0
                else:
                    total_leads = 0
                    total_comments = len(st.session_state.dataframe_result)
                    lead_rate = 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Comments", total_comments)
                with col2:
                    st.metric("Total Leads", total_leads)
                with col3:
                    st.metric("Lead Rate", f"{lead_rate:.1f}%")
                
                # Visualizations
                viz_tabs = st.tabs(["Lead Distribution", "Header Analysis"])
                
                with viz_tabs[0]:
                    if 'Is Lead' in st.session_state.dataframe_result.columns:
                        fig = px.pie(
                            st.session_state.dataframe_result,
                            names="Is Lead",
                            title="Lead Distribution",
                            color_discrete_sequence=px.colors.qualitative.Set3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No lead classification data available.")
                
                with viz_tabs[1]:
                    st.info("Header analysis visualization coming soon!")
        elif st.session_state.dataframe_result is not None and st.session_state.dataframe_result.empty:
            st.warning("No results found for this URL. Please check if the post exists and has comments.")
            st.session_state.dataframe_result = None  # Reset the state

else:
    st.info(f"{lead_filter} integration coming soon! 🚀")

# Help section
with st.expander("ℹ️ How to Use"):
    st.markdown(f"""
    1. Choose {lead_filter} platform from the sidebar
    2. Enter your login credentials in the sidebar
    3. Paste a {lead_filter} post URL in the input field
    4. Click Generate to analyze potential leads
    5. Download the results as CSV or Excel
    
    **Note:** The analysis may take a few minutes to complete.
    """)

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: grey;'>
        Made with ❤️ by Vartur AI Team
    </div>
""", unsafe_allow_html=True)