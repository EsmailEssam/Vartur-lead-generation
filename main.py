import streamlit as st
import pandas as pd
import os
from io import BytesIO
import base64
import plotly.express as px
import time
import traceback

# Ensure you have these in your project structure
from helper.linkedinscraper import LinkedInScraper
from helper.instagramscraper import InstagramScraper
from helper.xscraper import XScraper
from helper.config import (
    LinkedInLoginError, 
    InstagramLoginError, 
    InvalidCredentialsError, 
    XLoginError
)

class SocialMediaLeadsApp:
    def __init__(self):
        # Configure page
        st.set_page_config(
            page_title="Social Media Lead Generation @ Vartur",
            page_icon="🎯",
            layout="wide"
        )
        
        # Initialize session states
        self._initialize_session_states()
        
        # Load logos and background
        self._load_assets()
        
        # Apply styles
        self._apply_styles()

    def _initialize_session_states(self):
        """Initialize Streamlit session states"""
        default_states = {
            'debug_mode': False,
            'dataframe_result': None,
            'current_url': "",
            'email': "",
            'password': ""
        }
        
        for key, default_value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def _load_assets(self):
        """Load and cache logos and background images"""
        try:
            @st.cache_data
            def image_to_base64(image_path):
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode()
            
            self.background = image_to_base64(os.path.join('data', 'background.png'))
            self.logo_base64 = image_to_base64(os.path.join('data', 'logo-vartur.png'))
            
            self.logos = {
                'LinkedIn': image_to_base64(os.path.join('data', 'logo-linkedin.png')),
                'Instagram': image_to_base64(os.path.join('data', 'logo-instagram.png')),
                'X': image_to_base64(os.path.join('data', 'logo-x.png'))
            }
        except Exception as e:
            st.error(f"Error loading images: {str(e)}")
            st.stop()

    def _apply_styles(self):
        """Apply custom CSS styles to Streamlit app"""
        st.markdown(f"""
            <style>
                .stApp {{
                    background-image: url("data:image/png;base64,{self.background}");
                    background-size: cover;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                    background-position: center;
                }}
                .stButton > button {{
                    width: 100%;
                    background: linear-gradient(45deg, #2E7D32, #4CAF50) !important;
                    color: white !important;
                    font-weight: bold !important;
                    border-radius: 8px !important;
                }}
            </style>
        """, unsafe_allow_html=True)

    def _render_header(self, logo_base64):
        """Render the application header"""
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

    def _sidebar_configuration(self):
        """Configure sidebar for platform and login"""
        with st.sidebar:
            st.title("Platform")
            
            # Platform selection
            lead_filter = st.radio("Choose a Platform", ["LinkedIn", "Instagram", "X"])
            
            # Debug mode toggle
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
            
            return lead_filter

    def _process_platform_scraping(self, lead_filter, url):
        """Process scraping for different platforms"""
        scrapers = {
            'LinkedIn': LinkedInScraper,
            'Instagram': InstagramScraper,
            'X': XScraper
        }
        
        login_errors = {
            'LinkedIn': LinkedInLoginError,
            'Instagram': InstagramLoginError,
            'X': XLoginError
        }
        
        if not url:
            st.info(f"Please enter a {lead_filter} post URL to begin.")
            return None
        
        if 'email' not in st.session_state or not st.session_state['email']:
            st.warning(f"Please enter your {lead_filter} credentials in the sidebar first.")
            return None
        
        with st.spinner('Processing... This may take a few minutes.'):
            try:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text(f"Logging in to {lead_filter}...")
                progress_bar.progress(20)
                
                scraper_kwargs = {
                    'url': url,
                    'email': st.session_state['email'],
                    'password': st.session_state['password']
                }
                
                # Add platform-specific parameters
                if lead_filter == 'LinkedIn':
                    scraper_kwargs['is_headless'] = not st.session_state.debug_mode
                elif lead_filter == 'Instagram':
                    scraper_kwargs['headless'] = not st.session_state.debug_mode
                elif lead_filter == 'X':
                    scraper_kwargs['is_headless'] = not st.session_state.debug_mode
                
                dataframe_result = scrapers[lead_filter](**scraper_kwargs).scrape()
                
                progress_bar.progress(100)
                status_text.text("Processing complete!")
                time.sleep(1)
                status_text.empty()
                progress_bar.empty()
                
                return dataframe_result
                
            except InvalidCredentialsError:
                st.error(f"Invalid {lead_filter} credentials. Please check your email and password.")
            except login_errors[lead_filter] as e:
                st.error(f"Login error: {str(e)}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                if st.session_state.debug_mode:
                    with st.expander("Error Details"):
                        st.code(traceback.format_exc())
        
        return None

    def _render_results(self, dataframe_result, lead_filter):
        """Render results for the scraped data"""
        if dataframe_result is None or dataframe_result.empty:
            st.warning("No results found for this URL. Please check if the post exists and has comments.")
            return
        
        tab1, tab2 = st.tabs(["📊 Data", "📈 Analysis"])
        
        with tab1:
            st.markdown("### Identified Data")
            
            # Platform-specific filtering
            if lead_filter == 'X':
                filter_options = st.multiselect(
                    "Filter comments by:",
                    ["Has Media", "Has Links", "Has Mentions"],
                    default=[]
                )
                
                filtered_df = dataframe_result.copy()
                
                # Apply filters for X
                if "Has Media" in filter_options:
                    filtered_df = filtered_df[filtered_df["Comment Content"].str.contains(r'pic.twitter.com|video.twimg.com', na=False)]
                if "Has Links" in filter_options:
                    filtered_df = filtered_df[filtered_df["Comment Content"].str.contains(r'https?://', na=False)]
                if "Has Mentions" in filter_options:
                    filtered_df = filtered_df[filtered_df["Comment Content"].str.contains(r'@\w+', na=False)]
            else:
                # Lead filter for LinkedIn and Instagram
                if 'Is Lead' in dataframe_result.columns:
                    lead_filter_option = st.selectbox(
                        "Filter by lead status:",
                        ["All", "Lead", "Not a Lead"]
                    )
                    
                    filtered_df = dataframe_result
                    if lead_filter_option != "All":
                        filtered_df = dataframe_result[dataframe_result["Is Lead"] == lead_filter_option]
                else:
                    filtered_df = dataframe_result
            
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    "Download as CSV",
                    csv,
                    f"{lead_filter.lower()}_data.csv",
                    "text/csv",
                    use_container_width=True
                )
            with col2:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    filtered_df.to_excel(writer, sheet_name='Data', index=False)
                excel_data = buffer.getvalue()
                st.download_button(
                    "Download as Excel",
                    excel_data,
                    f"{lead_filter.lower()}_data.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        # Analysis Tab
        with tab2:
            self._render_platform_analysis(filtered_df, lead_filter)

    def _render_platform_analysis(self, filtered_df, lead_filter):
        """Render platform-specific analysis"""
        # Common metrics
        total_entries = len(filtered_df)
        
        # Platform-specific metrics
        total_leads = len(filtered_df[filtered_df["Is Lead"] == "Lead"]) if "Is Lead" in filtered_df.columns else 0
        lead_rate = (total_leads / total_entries * 100) if total_entries > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", total_entries)
        with col2:
            st.metric("Total Leads", total_leads)
        with col3:
            st.metric("Lead Rate", f"{lead_rate:.1f}%")
        
        # Visualizations
        viz_tabs = st.tabs(["Lead Distribution", "Header Analysis"])
        
        with viz_tabs[0]:
            if "Is Lead" in filtered_df.columns:
                fig = px.pie(
                    filtered_df,
                    names="Is Lead",
                    title="Lead Distribution",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No lead classification data available.")
        

    def run(self):
        """Main application runner"""
        # Render header
        self._render_header(self.logo_base64)
        
        # Sidebar configuration
        lead_filter = self._sidebar_configuration()
        
        # Platform-specific logo and title
        st.markdown(f""" 
            <div style="display: flex; align-items: center;">
                <img src="data:image/png;base64,{self.logos[lead_filter]}" style="width: 30px; height: 30px;">
                <h2 style="margin-left: 10px;">{lead_filter} Leads Generation</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # URL input
        url = st.text_input(f"Enter {lead_filter} Post URL:")
        
        # Reset dataframe if URL changes
        if url != st.session_state.current_url:
            st.session_state.dataframe_result = None
            st.session_state.current_url = url
        
        # Generate Leads button
        if st.button("Generate Leads", use_container_width=True):
            st.session_state.dataframe_result = self._process_platform_scraping(lead_filter, url)
        
        # Render results
        if st.session_state.dataframe_result is not None:
            self._render_results(st.session_state.dataframe_result, lead_filter)
        
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


# Main execution
if __name__ == "__main__":
    app = SocialMediaLeadsApp()
    app.run()